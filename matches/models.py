# -*- coding: utf-8 -*-

'''models'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import logging
import random

from collections import defaultdict

from django.conf import settings
from django.db import models
from django.utils import timezone
from djangae import fields, storage
from djangae.contrib.gauth.datastore.models import GaeDatastoreUser
# from djangae.contrib.pagination import paginated_model
# from djangae.db.consistency import ensure_instances_consistent
from gcm import GCM
from rest_framework import serializers

from .utils import clear_list

GCM_SENDER = GCM(settings.GCM_API_KEY, debug=settings.DEBUG)
LOGGER = logging.getLogger(__name__)
STORAGE = storage.CloudStorage(bucket='diris-images', google_acl='public-read')


class MatchDetails(object):
    INVITED = 'i'
    ACCEPTED = 'a'
    DECLINED = 'd'
    INVITATION_STATUSES = (
        (INVITED, 'invited'),
        (ACCEPTED, 'accepted'),
        (DECLINED, 'declined'),
    )

    def __init__(self, player, match=None, is_inviting_player=False, date_invited=None,
                 invitation_status=INVITED, date_responded=None, score=0):
        self.match = match
        self.player = player
        self.is_inviting_player = is_inviting_player
        self.date_invited = date_invited or timezone.now()
        self.invitation_status = (MatchDetails.ACCEPTED if is_inviting_player
                                  else invitation_status or MatchDetails.INVITED)
        self.date_responded = date_responded or timezone.now() if is_inviting_player else None
        self.score = score


class MatchDetailsSerializer(serializers.Serializer):
    player = serializers.IntegerField()
    is_inviting_player = serializers.BooleanField(default=False)
    date_invited = serializers.DateTimeField(required=False, allow_null=True)
    invitation_status = serializers.ChoiceField(choices=MatchDetails.INVITATION_STATUSES,
                                                default=MatchDetails.INVITED)
    date_responded = serializers.DateTimeField(required=False, allow_null=True)
    score = serializers.IntegerField(min_value=0, default=0)

    def create(self, validated_data):
        return MatchDetails(**validated_data)


class RoundDetails(object):
    def __init__(self, player, match_round=None, is_storyteller=False, image=None,
                 score=0, vote=None, vote_player=None):
        self.match_round = match_round
        self.player = player
        self.is_storyteller = is_storyteller
        self.image = image
        self.score = score
        self.vote = vote
        self.vote_player = vote_player

    def display_vote_to(self, match_round=None, player_pk=None):
        match_round = match_round or self.match_round

        if not match_round:
            return bool(player_pk and player_pk == self.player)

        elif (match_round.status == Round.FINISHED
              or (player_pk and player_pk == self.player)):
            return True

        else:
            details = match_round.details_dict.get(player_pk)
            return bool(details and (details.is_storyteller or details.vote))


class RoundDetailsSerializer(serializers.Serializer):
    player = serializers.IntegerField()
    is_storyteller = serializers.BooleanField(default=False)
    image = serializers.IntegerField(required=False, allow_null=True)
    score = serializers.IntegerField(min_value=0, default=0)
    vote = serializers.IntegerField(required=False, allow_null=True)
    vote_player = serializers.IntegerField(required=False, allow_null=True)

    def create(self, validated_data):
        return RoundDetails(**validated_data)


class Round(object):
    WAITING = 'w'
    SUBMIT_STORY = 's'
    SUBMIT_OTHERS = 'o'
    SUBMIT_VOTES = 'v'
    FINISHED = 'f'
    ROUND_STATUSES = (
        (WAITING, 'waiting'),
        (SUBMIT_STORY, 'submit storyteller'),
        (SUBMIT_OTHERS, 'submit others'),
        (SUBMIT_VOTES, 'submit votes'),
        (FINISHED, 'finished'),
    )

    MINIMUM_STORY_LENGTH = 3

    MAX_DECEIVED_VOTE_SCORE = 3
    DECEIVED_VOTE_SCORE = 1
    ALL_CORRECT_SCORE = 2
    ALL_CORRECT_STORYTELLER_SCORE = 0
    ALL_WRONG_SCORE = 2
    ALL_WRONG_STORYTELLER_SCORE = 0
    NOT_ALL_CORRECT_OR_WRONG_SCORE = 3
    NOT_ALL_CORRECT_OR_WRONG_STORYTELLER_SCORE = 3

    def __init__(self, number, storyteller, details, match=None,
                 is_current_round=False, status=WAITING, story=None):
        self.match = match
        self.number = number
        self.storyteller = storyteller
        self.details = details
        self.is_current_round = is_current_round
        self.status = status
        self.story = story
        self._details_dict = None

    @property
    def details_dict(self):
        if self._details_dict is not None:
            return self._details_dict

        result = {}
        for player_pk, data in self.details.items():
            serializer = RoundDetailsSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            result[int(player_pk)] = serializer.save(match_round=self)

        self._details_dict = result
        return self._details_dict

    def submit_image(self, player_pk, image_pk, story=None):
        if not player_pk or not image_pk:
            # TODO other validations
            raise ValueError('player and image are required')

        self.check_status()

        details = self.details_dict[player_pk]

        if details.is_storyteller:
            if self.status != Round.SUBMIT_STORY:
                raise ValueError('not ready for submission')

            if not story or len(story) < Round.MINIMUM_STORY_LENGTH:
                # TODO validate story further
                raise ValueError('story is required and needs to be at least {} characters long'
                                 .format(Round.MINIMUM_STORY_LENGTH))

            if details.image and self.story:
                raise ValueError('image and story already exists')

            self.story = story
            self.status = Round.SUBMIT_OTHERS

        else:
            if self.status != Round.SUBMIT_OTHERS:
                raise ValueError('not ready for submission')

            if details.image:
                raise ValueError('image story already exists')

        details.image = image_pk

        if self.match:
            self.match.images_ids.add(image_pk)

        self.check_status()

    def submit_vote(self, player_pk, image_pk):
        if not player_pk or not image_pk:
            # TODO other validations
            raise ValueError('player and image are required')

        self.check_status()

        details = self.details_dict[player_pk]

        if details.is_storyteller:
            raise ValueError('storyteller cannot vote')

        if details.vote:
            raise ValueError('vote already exists')

        if self.status != Round.SUBMIT_VOTES:
            raise ValueError('not ready for submission')

        vote_player = [d.player for d in self.details_dict.values() if d.image == image_pk]

        if len(vote_player) != 1:
            raise ValueError('image not found in this round')

        vote_player = vote_player[0]

        if player_pk == vote_player:
            raise ValueError('players cannot vote for themselves')

        details.vote = image_pk
        details.vote_player = vote_player

        if self.match:
            self.match.check_status()
            self.match.score()
        else:
            self.check_status()
            self.score()

    def check_status(self, match=None, prev_round=None):
        if all(details.vote for player_pk, details in self.details_dict.items()
               if player_pk != self.storyteller):
            self.status = Round.FINISHED

        elif all(details.image for details in self.details_dict.values()):
            self.status = Round.SUBMIT_VOTES

        elif self.details_dict[self.storyteller].image and self.story:
            self.status = Round.SUBMIT_OTHERS

        elif self.number == 1:
            match = match or self.match
            self.status = (Round.SUBMIT_STORY
                           if match.status == Match.IN_PROGESS
                           else Round.WAITING)

        else:
            match = match or self.match
            prev_round = prev_round or match.rounds_list[self.number - 2]
            self.status = (Round.SUBMIT_STORY
                           if prev_round.status == Round.FINISHED
                           else Round.WAITING)

        self.is_current_round = self.status not in (Round.FINISHED, Round.WAITING)

    def score(self):
        if self.status != Round.FINISHED:
            return defaultdict(int)

        scores = defaultdict(int)

        non_storyteller_details = [details for player_pk, details in self.details_dict.items()
                                   if player_pk != self.storyteller]

        for details in non_storyteller_details:
            if (details.vote_player != self.storyteller
                    and scores[details.vote_player] < Round.MAX_DECEIVED_VOTE_SCORE):
                scores[details.vote_player] += Round.DECEIVED_VOTE_SCORE

        if all(details.vote_player == self.storyteller for details in non_storyteller_details):
            scores[self.storyteller] += Round.ALL_CORRECT_STORYTELLER_SCORE
            for details in non_storyteller_details:
                scores[details.player] += Round.ALL_CORRECT_SCORE

        elif all(details.vote_player != self.storyteller for details in non_storyteller_details):
            scores[self.storyteller] += Round.ALL_WRONG_STORYTELLER_SCORE
            for details in non_storyteller_details:
                scores[details.player] += Round.ALL_WRONG_SCORE

        else:
            scores[self.storyteller] += Round.NOT_ALL_CORRECT_OR_WRONG_STORYTELLER_SCORE
            for details in non_storyteller_details:
                if details.vote_player == self.storyteller:
                    scores[details.player] += Round.NOT_ALL_CORRECT_OR_WRONG_SCORE

        for details in self.details_dict.values():
            details.score = scores[details.player]

        return scores

    def display_images_to(self, player_pk=None):
        return bool(self.status in (Round.SUBMIT_VOTES, Round.FINISHED)
                    or (player_pk and player_pk == self.storyteller))


class RoundSerializer(serializers.Serializer):
    number = serializers.IntegerField(min_value=1)
    storyteller = serializers.IntegerField()
    details = serializers.DictField(child=RoundDetailsSerializer())
    is_current_round = serializers.BooleanField(default=False)
    status = serializers.ChoiceField(choices=Round.ROUND_STATUSES,
                                     default=Round.WAITING)
    story = serializers.CharField(required=False, allow_null=True,
                                  min_length=Round.MINIMUM_STORY_LENGTH,
                                  allow_blank=False, trim_whitespace=True)

    def create(self, validated_data):
        return Round(**validated_data)


class MatchManager(models.Manager):
    def create_match(self, players, inviting_player=None, total_rounds=0, timeout=0):
        players = clear_list(players)

        if inviting_player and inviting_player not in players:
            players.insert(0, inviting_player)

        if len(players) < Match.MINIMUM_PLAYER:
            raise ValueError('Not enough players - need to give at least {} players '
                             'to create a match'.format(Match.MINIMUM_PLAYER))

        if len(players) > Match.MAXIMUM_PLAYER:
            raise ValueError('Too many players - need to give at most {} players '
                             'to create a match'.format(Match.MAXIMUM_PLAYER))

        inviting_player = inviting_player or players[0]

        match_details = {player.pk: MatchDetails(player=player.pk,
                                                 is_inviting_player=player.pk == inviting_player.pk)
                         for player in players}
        match_details_data = {player: MatchDetailsSerializer(instance=details).data
                              for player, details in match_details.items()}

        total_rounds = total_rounds or len(players)

        random.shuffle(players)

        rounds = [Round(
            number=i + 1,
            storyteller=players[i % len(players)].pk,
            is_current_round=i == 0,
            status=Round.WAITING,
            details={player.pk: RoundDetails(
                player=player.pk,
                is_storyteller=players[i % len(players)].pk == player.pk,
            ) for player in players},
        ) for i in range(total_rounds)]
        round_data = RoundSerializer(instance=rounds, many=True).data

        data = {
            'players': players,
            'inviting_player': inviting_player,
            'details': match_details_data,
            'rounds': round_data,
        }

        if timeout:
            data['timeout'] = timeout

        return self.create(**data)


# @paginated_model(orderings=('last_modified', 'created', 'status', ('status', 'last_modified')))
class Match(models.Model):
    WAITING = 'w'
    IN_PROGESS = 'p'
    FINISHED = 'f'
    DELETE = 'd'
    MATCH_STATUSES = (
        (WAITING, 'waiting'),
        (IN_PROGESS, 'in progress'),
        (FINISHED, 'finished'),
        (DELETE, 'delete'),
    )
    STANDARD_TIMEOUT = 60 * 60 * 36  # 36
    MINIMUM_PLAYER = 4
    MAXIMUM_PLAYER = 10

    objects = MatchManager()

    players = fields.RelatedSetField('Player', related_name='matches', on_delete=models.PROTECT)
    inviting_player = models.ForeignKey('Player', related_name='inviting_matches',
                                        on_delete=models.PROTECT)

    details = fields.JSONField()
    _details_dict = None
    rounds = fields.JSONField()
    _rounds_list = None

    total_rounds = fields.ComputedIntegerField(func=lambda match: len(match.rounds))
    # TODO could be a computed field
    current_round = models.PositiveSmallIntegerField(default=1)
    images = fields.RelatedSetField('Image', related_name='matches')

    status = fields.CharField(max_length=1, choices=MATCH_STATUSES, default=WAITING)
    timeout = models.PositiveIntegerField(default=STANDARD_TIMEOUT)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    @property
    def details_dict(self):
        if self._details_dict is not None:
            return self._details_dict

        result = {}
        for player_pk, data in self.details.items():
            serializer = MatchDetailsSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            result[int(player_pk)] = serializer.save(match=self)

        self._details_dict = result
        return self._details_dict

    @property
    def rounds_list(self):
        if self._rounds_list is not None:
            return self._rounds_list

        result = []
        for data in self.rounds:
            serializer = RoundSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            result.append(serializer.save(match=self))

        self._rounds_list = result
        return self._rounds_list

    def respond(self, player_pk, accept=False):
        player_details = self.details_dict[player_pk]
        if player_details.invitation_status != MatchDetails.INVITED:
            raise ValueError('Player already responded to this invitation')

        player_details.invitation_status = (MatchDetails.ACCEPTED if accept
                                            else MatchDetails.DECLINED)
        player_details.date_responded = timezone.now()

        self.check_status()

    def check_status(self):
        for details in self.details_dict.values():
            if details.invitation_status == MatchDetails.DECLINED:
                # TODO remove the player instead (if possible) and adjust rounds & details
                LOGGER.info('player %d declined the invitation, delete the match', details.player)
                self.status = Match.DELETE
                return

        self.status = (Match.WAITING
                       if any(details.invitation_status != MatchDetails.ACCEPTED
                              for details in self.details_dict.values())
                       else Match.IN_PROGESS)

        prev_round = None
        self.images_ids.clear()

        for curr_round in self.rounds_list:
            curr_round.check_status(match=self, prev_round=prev_round)
            if curr_round.is_current_round:
                self.current_round = curr_round.number
            for details in curr_round.details_dict.values():
                if details.image:
                    self.images_ids.add(details.image)
            prev_round = curr_round

        if prev_round.status == Round.FINISHED:
            self.status = Match.FINISHED

    def score(self):
        scores = defaultdict(int)

        for round_ in self.rounds_list:
            round_scores = round_.score()
            for player_pk, value in round_scores.items():
                scores[player_pk] += value

        for details in self.details_dict.values():
            details.score = scores[details.player]

        return scores

    def save(self, *args, **kwargs):
        if self.status == Match.DELETE:
            LOGGER.info('match %d marked for deletion', self.pk)
            LOGGER.info(self.delete())
            return

        if self._details_dict is not None:
            self.details = {player_pk: MatchDetailsSerializer(instance=details).data
                            for player_pk, details in self._details_dict.items()}

        if self._rounds_list is not None:
            for round_ in self._rounds_list:
                if round_._details_dict is not None:
                    round_.details = {player_pk: RoundDetailsSerializer(instance=details).data
                                      for player_pk, details in round_._details_dict.items()}
            self.rounds = RoundSerializer(instance=self._rounds_list, many=True).data

        super(Match, self).save(*args, **kwargs)

    class Meta(object):
        ordering = ('-last_modified',)
        verbose_name_plural = 'matches'


class Player(models.Model):
    user = models.OneToOneField(GaeDatastoreUser, on_delete=models.CASCADE)
    avatar = models.ForeignKey('Image',
                               related_name='avatars',
                               blank=True, null=True,
                               on_delete=models.SET_NULL)
    gcm_registration_id = fields.CharField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta(object):
        ordering = ('-last_modified',)

    def send_message(self, **data):
        if self.gcm_registration_id:
            return GCM_SENDER.plaintext_request(registration_id=self.gcm_registration_id,
                                                data=data)


class ImageManager(models.Manager):
    def create_image(self, *args, **kwargs):
        image = self.create(*args, **kwargs)

        # TODO factor out into utils function
        width = int(image.width) if image.width else -1
        height = int(image.height) if image.height else -1

        # TODO set size
        if width > 0 and height > 0:
            return image

        try:
            width = image.file.width
            height = image.file.height
        except Exception as exc:
            LOGGER.warning(exc)

        if width > 0 and height > 0:
            image.width = width
            image.height = height
            image.save()
            return image

        try:
            import google.appengine.api.images
            image.file.open(mode='r')
            image_obj = google.appengine.api.images.Image(image_data=image.file.read())
            width = image_obj.width
            height = image_obj.height
        except Exception as exc:
            LOGGER.warning(exc)
        finally:
            image.file.close()

        if width > 0 and height > 0:
            image.width = width
            image.height = height
            image.save()
            return image

        try:
            width = int(image.info.get('width'))
            height = int(image.info.get('height'))
        except Exception as exc:
            LOGGER.warning(exc)

        image.width = width if width and width > 0 else None
        image.height = height if height and height > 0 else None
        image.save()
        return image


class Image(models.Model):
    OWNER = 'o'
    RESTRICTED = 'r'
    DIRIS = 'd'
    PUBLIC = 'p'
    COPYRIGHTS = (
        (OWNER, 'owner'),
        (RESTRICTED, 'restricted'),
        (DIRIS, 'diris'),
        (PUBLIC, 'public'),
    )

    objects = ImageManager()

    file = models.ImageField(
        upload_to='%Y/%m/%d/%H/%M/',
        storage=STORAGE,
    )
    url = fields.ComputedCharField(func=lambda image: image.file.url, max_length=1500,
                                   blank=True, null=True, default=None)
    # TODO computed fields?
    width = models.PositiveSmallIntegerField(blank=True, null=True)
    height = models.PositiveSmallIntegerField(blank=True, null=True)
    size = models.PositiveIntegerField(blank=True, null=True)
    owner = models.ForeignKey(Player, related_name='images',
                              blank=True, null=True, on_delete=models.SET_NULL)
    copyright = fields.CharField(max_length=1, choices=COPYRIGHTS, default=OWNER)
    info = fields.JSONField(blank=True, null=True)
    is_available_publically = fields.ComputedBooleanField(
        func=lambda image: image.copyright in (image.DIRIS, image.PUBLIC),
        default=False,
    )
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def is_available_to(self, player=None):
        return self.is_available_publically or (player and player == self.owner)

    class Meta(object):
        ordering = ('-last_modified',)
