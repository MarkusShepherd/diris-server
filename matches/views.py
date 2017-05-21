# -*- coding: utf-8 -*-

'''views'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import json
import logging
import os.path

from base64 import b64decode

from builtins import int, str
from django.conf import settings
from django.contrib.auth import login
from django.db.models import Q
from django.utils.crypto import get_random_string, random
from djangae.contrib.gauth_datastore.models import GaeDatastoreUser
from djangae.contrib.pagination import Paginator
from google.appengine.api.mail import send_mail
from rest_framework import mixins, permissions, status, views, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import ValidationError, NotAuthenticated, NotFound
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework_jwt.settings import api_settings
from six import itervalues, raise_from, string_types

from .models import Image, Match, Player
from .permissions import IsOwnerOrCreateAndRead
from .serializers import MatchSerializer, PlayerSerializer, ImageSerializer
from .utils import get_player, merge, normalize_space, random_string

LOGGER = logging.getLogger(__name__)


def upload_image(request, owner=None, file_extension=None):
    image = request.data['file']
    orig_extension = (os.path.splitext(image.name)[1]
                      if hasattr(image, 'name') and isinstance(image.name, string_types)
                      else None)
    file_extension = file_extension or orig_extension or '.jpeg'
    image.name = random_string() + file_extension

    copyright = (normalize_space(request.data.get('copyright'))
                 or normalize_space(request.query_params.get('copyright')))
    if copyright not in {c[0] for c in Image.COPYRIGHTS}:
        copyright = Image.OWNER if owner else Image.RESTRICTED

    try:
        body_info = json.loads(request.data.get('info') or '{}')
    except ValueError as exc:
        LOGGER.warning(exc)
        body_info = {}

    info = merge(request.query_params or {}, body_info)

    return Image.objects.create_image(file=image, owner=owner, copyright=copyright, info=info)


class MatchViewSet(
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        viewsets.GenericViewSet
):
    serializer_class = MatchSerializer
    permission_classes = (permissions.IsAuthenticated,)
    ordering = ('deadline_action', '-last_modified')
    filter_fields = ('inviting_player', 'status')

    default_checks_size = 100

    def get_queryset(self):
        player = get_player(self.request)
        return player.matches.all() if player else Match.objects.none()

    def create(self, request, *args, **kwargs):
        player = get_player(request, raise_error=True)

        request.data['inviting_player'] = player.pk
        try:
            return super(MatchViewSet, self).create(request, *args, **kwargs)
        except ValueError as exc:
            raise_from(ValidationError(detail=str(exc)), exc)

    def retrieve(self, request, *args, **kwargs):
        player = get_player(request, raise_error=True)

        match = self.get_object()
        serializer = self.get_serializer(instance=match, player=player)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        player = get_player(request, raise_error=True)

        matches = self.filter_queryset(self.get_queryset()).order_by(*self.ordering)

        page = self.paginate_queryset(matches)
        if page is not None:
            serializer = self.get_serializer(instance=page, player=player, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(instance=matches, player=player, many=True)
        return Response(serializer.data)

    @list_route(methods=['get', 'post'], permission_classes=())
    def checks(self, request, *args, **kwargs):
        matches = (self.filter_queryset(Match.objects.all())
                   .order_by('deadline_action', 'last_modified'))

        try:
            size = int(request.query_params.get('size'))
            size = size if size > 0 else self.default_checks_size
        except (TypeError, ValueError):
            size = self.default_checks_size

        for match in matches[:size]:
            match.check_status()
            match.score()
            match.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['get', 'post'], permission_classes=())
    def check(self, request, pk=None, *args, **kwargs):
        try:
            match = Match.objects.get(pk=pk)
        except Match.DoesNotExist as exc:
            raise_from(NotFound(detail='match "{}" does not exist'.format(pk)), exc)

        match.check_status()
        match.score()
        match.save()

        player = get_player(request)

        if player and player.pk in match.players_ids:
            serializer = self.get_serializer(instance=match, player=player)
            return Response(serializer.data)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'])
    def accept(self, request, pk, *args, **kwargs):
        player = get_player(request, raise_error=True)
        match = self.get_object()

        try:
            match.respond(player.pk, accept=True)
        except ValueError as exc:
            raise_from(ValidationError(detail=str(exc)), exc)
        finally:
            match.check_status()
            match.save()

        serializer = self.get_serializer(instance=match, player=player)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def decline(self, request, pk, *args, **kwargs):
        player = get_player(request, raise_error=True)
        match = self.get_object()

        try:
            match.respond(player.pk, accept=False)
        except ValueError as exc:
            raise_from(ValidationError(detail=str(exc)), exc)
        finally:
            match.check_status()
            match.save()

        serializer = self.get_serializer(instance=match, player=player)
        return Response(serializer.data)

    @detail_route()
    def players(self, request, pk=None, *args, **kwargs):
        match = self.get_object()
        serializer = PlayerSerializer(instance=match.players, many=True)
        return Response(serializer.data)

    @detail_route()
    def images(self, request, pk=None, *args, **kwargs):
        player = get_player(request, raise_error=True)
        match = self.get_object()

        try:
            rounds = ([match.rounds_list[int(request.query_params['round']) - 1]]
                      if request.query_params.get('round') else match.rounds_list)
        except Exception as exc:
            raise_from(ValidationError(detail=str(exc)), exc)

        image_pks = {details.image
                     for round_ in rounds
                     if round_.display_images_to(player.pk)
                     for details in itervalues(round_.details_dict)
                     if details.image}

        serializer = ImageSerializer(instance=Image.objects.filter(pk__in=image_pks),
                                     player=player, many=True)
        return Response(serializer.data)


class MatchImageView(views.APIView):
    parser_classes = (MultiPartParser, FileUploadParser)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, match_pk, round_number, filename):
        player = get_player(request, raise_error=True)
        match = player.matches.get(pk=match_pk)
        round_ = match.rounds_list[int(round_number) - 1]

        file_extension = (os.path.splitext(filename)[1] if isinstance(filename, string_types)
                          else None)
        image = upload_image(request, player, file_extension)

        story = (normalize_space(request.data.get('story'))
                 or normalize_space(request.query_params.get('story')))

        try:
            round_.submit_image(player_pk=player.pk, image_pk=image.pk, story=story)
        except ValueError as exc:
            raise_from(ValidationError(detail=str(exc)), exc)
        finally:
            match.check_status()
            match.save()

        serializer = MatchSerializer(instance=match, player=player)
        return Response(serializer.data)


class MatchVoteView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, match_pk, round_number, image_pk):
        player = get_player(request, raise_error=True)
        match = player.matches.get(pk=match_pk)
        round_ = match.rounds_list[int(round_number) - 1]

        try:
            round_.submit_vote(player_pk=player.pk, image_pk=int(image_pk))
        except ValueError as exc:
            raise_from(ValidationError(detail=str(exc)), exc)
        finally:
            match.check_status()
            match.score()
            match.save()

        serializer = MatchSerializer(instance=match, player=player)
        return Response(serializer.data)


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    permission_classes = (IsOwnerOrCreateAndRead,)
    serializer_class = PlayerSerializer
    ordering = ('-last_modified',)

    def create(self, request, *args, **kwargs):
        response = super(PlayerViewSet, self).create(request, *args, **kwargs)

        player = response.data
        user = GaeDatastoreUser.objects.get(pk=player['user']['pk'])
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        response.data['token'] = token

        return response

    @list_route(methods=['post'], permission_classes=())
    def send(self, request, *args, **kwargs):
        if request.query_params.get('key') != settings.GCM_SERVER_KEY:
            raise NotAuthenticated(detail='the supplied key "{}" is not valid'
                                   .format(request.query_params.get('key')))

        if request.data.get('message') and request.data.get('subscription'):
            msg_obj = request.data.get('message')
            attributes = msg_obj.get('attributes') or {}
            try:
                add_data = json.loads(b64decode(msg_obj.get('data') or 'e30='))
                data = merge(attributes, add_data)
            except Exception as exc:
                LOGGER.warning('could not process data "%s"', msg_obj.get('data'))
                LOGGER.warning(exc)
                data = attributes

        else:
            data = request.data

        player_pk = data.pop('player_pk', None)
        player_pks = data.pop('player_pks', ())

        if isinstance(player_pks, (list, tuple, set, frozenset)):
            player_pks = set(player_pks)
        elif player_pks:
            player_pks = {player_pks}
        else:
            player_pks = set()

        if player_pk:
            player_pks.add(player_pk)

        LOGGER.info(player_pks)
        LOGGER.info(data)

        for player in Player.objects.filter(pk__in=player_pks):
            LOGGER.info(player.pk)
            LOGGER.info(player.send_message(**data))

        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(methods=['post'], permission_classes=())
    def reset_password(self, request, *args, **kwargs):
        username = request.data.get('username') or request.query_params.get('username')
        email = request.data.get('email') or request.query_params.get('email')

        if not username or not email:
            raise ValidationError(detail='username and email are required')

        try:
            user = GaeDatastoreUser.objects.get(username=username, email=email)
        except GaeDatastoreUser.DoesNotExist as exc:
            raise_from(NotFound(detail='user with this combination of '
                                'name and email does not exist'), exc)

        new_password = get_random_string(length=20)
        user.set_password(new_password)
        user.save()

        # TODO put into util function
        # TODO use email template
        send_mail(
            sender='noreply@diris-app.appspotmail.com',
            to=[email],
            subject='[Diris] New password',
            body='''
            Hi {username}!

            Your new password is {password}.

            Please use it to log in and change it.

            Happy storytelling!
            '''.format(username=username, password=new_password),
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    permission_classes = (IsOwnerOrCreateAndRead,)
    serializer_class = ImageSerializer
    parser_classes = (MultiPartParser, FileUploadParser)
    ordering = ('random_order',)
    filter_fields = ('copyright', 'is_available_publicly', 'owner')

    default_random_size = 5
    default_shuffle_size = 100

    def create(self, request, *args, **kwargs):
        if not request.data.get('owner'):
            request.data['owner'] = get_player(request)

        return super(ImageViewSet, self).create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        player = get_player(request)
        image = self.get_object()
        serializer = self.get_serializer(instance=image, player=player)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        player = get_player(request)

        images = self.filter_queryset(self.get_queryset()).order_by(*self.ordering)

        page = self.paginate_queryset(images)
        if page is not None:
            serializer = self.get_serializer(instance=page, player=player, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(instance=images, player=player, many=True)
        return Response(serializer.data)

    @list_route(methods=['get', 'post'])
    def shuffle(self, request, *args, **kwargs):
        try:
            size = int(request.query_params.get('size'))
            size = size if size > 0 else self.default_shuffle_size
        except (TypeError, ValueError):
            size = self.default_shuffle_size

        images = self.get_queryset().order_by('last_modified')
        for image in images[:size]:
            image.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route()
    def random(self, request, *args, **kwargs):
        player = get_player(request)

        query = Q(is_available_publicly=True)
        if player:
            query |= Q(owner=player)

        images = self.get_queryset().order_by('random_order').filter(query)
        images = images.reverse() if random.random() < .5 else images

        try:
            size = int(request.query_params.get('size'))
            size = size if size > 0 else self.default_random_size
        except (TypeError, ValueError):
            size = self.default_random_size

        paginator = Paginator(images, size * 2, readahead=100)
        # need to access first page before page_range works
        paginator.page(1)
        page_range = list(paginator.page_range)
        random.shuffle(page_range)

        image_list = []

        for page_num in page_range:
            image_list.extend(paginator.page(page_num))
            if len(image_list) >= size:
                break

        random.shuffle(image_list)

        serializer = self.get_serializer(instance=image_list[:size], many=True)
        return Response(serializer.data)


class ImageUploadView(views.APIView):
    parser_classes = (MultiPartParser, FileUploadParser)

    def put(self, request, filename):
        owner = get_player(request)

        file_extension = (os.path.splitext(filename)[1] if isinstance(filename, string_types)
                          else None)
        image = upload_image(request, owner, file_extension)
        serializer = ImageSerializer(instance=image)
        return Response(serializer.data)
