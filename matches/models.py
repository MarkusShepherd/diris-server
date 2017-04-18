# -*- coding: utf-8 -*-

'''models'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import logging
import random

from collections import defaultdict

from django.db import models
from django.utils import timezone
from djangae import fields, storage
from djangae.contrib.gauth.datastore.models import GaeDatastoreUser
# from djangae.contrib.pagination import paginated_model
from djangae.db.consistency import ensure_instances_consistent
from rest_framework import serializers

from .utils import clear_list

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

    def __init__(self, player, is_inviting_player=False, date_invited=None,
                 invitation_status=INVITED, date_responded=None, score=0):
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
    def __init__(self, player, is_storyteller=False, image=None,
                 score=0, vote=None, vote_player=None):
        self.player = player
        self.is_storyteller = is_storyteller
        self.image = image
        self.score = score
        self.vote = vote
        self.vote_player = vote_player

    def display_vote_to(self, player=None):
        if (self.match_round.status == Round.FINISHED
                or (player and player == self.player)):
            return True

        elif not player:
            return False

        else:
            details = self.match_round.player_round_details.filter(player=player).first()
            return bool(details and (details.is_storyteller or details.vote))

    def submit_image(self, image, story=None):
        if not image:
            # TODO other validations
            raise ValueError('image is required')

        if self.is_storyteller:
            if self.match_round.status != Round.SUBMIT_STORY:
                raise ValueError('not ready for submission')

            if not story:
                # TODO validate story further
                raise ValueError('story is required')

            if self.image and self.match_round.story:
                self.match_round.match.check_status()
                raise ValueError('image and story already exists')

            self.match_round.story = story
            self.match_round.status = Round.SUBMIT_OTHERS

        else:
            if self.match_round.status != Round.SUBMIT_OTHERS:
                raise ValueError('not ready for submission')

            if self.image:
                self.match_round.match.check_status()
                raise ValueError('image story already exists')

            if all(details.image for details
                   in self.match_round.player_round_details.exclude(pk=self.pk)):
                self.match_round.status = Round.SUBMIT_VOTES

        self.image = image

        self.match_round.save()
        self.save()

        self.match_round.match.check_status(self.pk, self.match_round.pk)

    def submit_vote(self, image_pk):
        if self.is_storyteller:
            raise ValueError('storyteller cannot vote')

        if self.vote:
            raise ValueError('vote already exists')

        if self.match_round.status != Round.SUBMIT_VOTES:
            raise ValueError('not ready for submission')

        if not image_pk:
            raise ValueError('image is required')

        details = self.match_round.player_round_details.get(image=image_pk)
        image = details.image
        player = details.player

        if player.pk == self.player.pk:
            raise ValueError('players cannot vote for themselves')

        self.vote = image
        self.vote_player = player
        self.save()

        self.match_round.match.check_status(self.pk)
        self.match_round.match.score(self.pk)


class RoundDetailsSerializer(serializers.Serializer):
    player = serializers.IntegerField()
    is_storyteller = serializers.BooleanField(default=False)
    image = serializers.IntegerField(required=False, allow_null=True)
    score = serializers.IntegerField(min_value=0, default=0)
    vote = serializers.IntegerField(required=False, allow_null=True)
    vote_player = serializers.IntegerField(required=False, allow_null=True, read_only=True)

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

    MAX_DECEIVED_VOTE_SCORE = 3
    DECEIVED_VOTE_SCORE = 1
    ALL_CORRECT_SCORE = 2
    ALL_CORRECT_STORYTELLER_SCORE = 0
    ALL_WRONG_SCORE = 2
    ALL_WRONG_STORYTELLER_SCORE = 0
    NOT_ALL_CORRECT_OR_WRONG_SCORE = 3
    NOT_ALL_CORRECT_OR_WRONG_STORYTELLER_SCORE = 3

    def __init__(self, number, storyteller, details,
                 is_current_round=False, status=WAITING, story=None):
        self.number = number
        self.storyteller = storyteller
        self.details = details
        self.is_current_round = is_current_round
        self.status = status
        self.story = story

    _details_dict = None
    @property
    def details_dict(self):
        if self._details_dict is not None:
            return self._details_dict

        result = {}
        for player_pk, data in self.details.items():
            serializer = MatchDetailsSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            result[int(player_pk)] = serializer.save()

        self._details_dict = result
        return self._details_dict

    def display_images_to(self, player=None):
        return (self.status == Round.SUBMIT_VOTES
                or self.status == Round.FINISHED
                or (player and player == self.storyteller))

    def check_status(self, *updated, **kwargs):
        round_details = ensure_instances_consistent(self.player_round_details.all(), updated)

        if all(details.vote for details in round_details.exclude(is_storyteller=True)):
            self.status = Round.FINISHED

        elif all(details.image for details in round_details):
            self.status = Round.SUBMIT_VOTES

        elif round_details.get(is_storyteller=True).image and self.story:
            self.status = Round.SUBMIT_OTHERS

        elif self.number == 1:
            match = kwargs.get('match') or self.match
            self.status = (Round.SUBMIT_STORY
                           if match.status == Match.IN_PROGESS
                           else Round.WAITING)

        else:
            prev_round = kwargs.get('prev_round')
            if not prev_round:
                match = kwargs.get('match') or self.match
                prev_round = match.rounds.get(number=self.number - 1)

            self.status = (Round.SUBMIT_STORY
                           if prev_round.status == Round.FINISHED
                           else Round.WAITING)

        self.is_current_round = self.status != Round.FINISHED and self.status != Round.WAITING
        self.save()
        return self

    def score(self, *updated):
        if self.status != Round.FINISHED:
            return defaultdict(int)

        round_details = ensure_instances_consistent(self.player_round_details.all(), updated)
        scores = defaultdict(int)

        for details in round_details.exclude(is_storyteller=True):
            if (details.vote_player != self.storyteller
                    and scores[details.vote_player.pk] < Round.MAX_DECEIVED_VOTE_SCORE):
                scores[details.vote_player.pk] += Round.DECEIVED_VOTE_SCORE

        if all(details.vote_player == self.storyteller
               for details in round_details.exclude(is_storyteller=True)):
            scores[self.storyteller.pk] += Round.ALL_CORRECT_STORYTELLER_SCORE
            for details in round_details.exclude(is_storyteller=True):
                scores[details.player.pk] += Round.ALL_CORRECT_SCORE

        elif all(details.vote_player != self.storyteller
                 for details in round_details.exclude(is_storyteller=True)):
            scores[self.storyteller.pk] += Round.ALL_WRONG_STORYTELLER_SCORE
            for details in round_details.exclude(is_storyteller=True):
                scores[details.player.pk] += Round.ALL_WRONG_SCORE

        else:
            scores[self.storyteller.pk] += Round.NOT_ALL_CORRECT_OR_WRONG_STORYTELLER_SCORE
            for details in round_details.filter(vote_player=self.storyteller):
                scores[details.player.pk] += Round.NOT_ALL_CORRECT_OR_WRONG_SCORE

        for details in round_details:
            details.score = scores[details.player.pk]
            details.save()

        return scores

    def __str__(self):
        return 'Round #{}'.format(self.number)


class RoundSerializer(serializers.Serializer):
    number = serializers.IntegerField(min_value=1)
    storyteller = serializers.IntegerField()
    details = serializers.DictField(child=RoundDetailsSerializer())
    is_current_round = serializers.BooleanField(default=False)
    status = serializers.ChoiceField(choices=Round.ROUND_STATUSES,
                                     default=Round.WAITING)
    story = serializers.CharField(required=False, allow_null=True, min_length=3,
                                  allow_blank=False, trim_whitespace=True)

    def create(self, validated_data):
        return Round(**validated_data)


class MatchManager(models.Manager):
    def create_match(self, players, inviting_player=None, total_rounds=0, timeout=0):
        players = clear_list(players)

        if inviting_player and inviting_player not in players:
            players.insert(0, inviting_player)

        player_pks = players
        players = Player.objects.filter(pk__in=players)
        inviting_player = players.get(pk=inviting_player) if inviting_player else players[0]

        if len(players) != len(player_pks):
            raise ValueError('Some of the players were not found in the database')

        if len(players) < Match.MINIMUM_PLAYER:
            raise ValueError('Not enough players - need to give at least {} players '
                             'to create a match'.format(Match.MINIMUM_PLAYER))

        match_details = {player: MatchDetails(player=player,
                                              is_inviting_player=player == inviting_player.pk)
                         for player in player_pks}
        match_details_data = {player: MatchDetailsSerializer(instance=details).data
                              for player, details in match_details.items()}

        total_rounds = total_rounds or len(players)

        random.shuffle(player_pks)

        rounds = [Round(
            number=i + 1,
            storyteller=player_pks[i % len(player_pks)],
            is_current_round=i == 0,
            status=Round.WAITING,
            details={player: RoundDetails(
                player=player,
                is_storyteller=player_pks[i % len(player_pks)] == player,
            ) for player in player_pks},
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
    MATCH_STATUSES = (
        (WAITING, 'waiting'),
        (IN_PROGESS, 'in progress'),
        (FINISHED, 'finished'),
    )
    STANDARD_TIMEOUT = 60 * 60 * 36  # 36
    MINIMUM_PLAYER = 4

    objects = MatchManager()

    players = fields.RelatedSetField('Player', related_name='matches', on_delete=models.PROTECT)
    inviting_player = models.ForeignKey('Player', related_name='inviting_matches',
                                        on_delete=models.PROTECT)

    details = fields.JSONField()
    _details_dict = None
    @property
    def details_dict(self):
        if self._details_dict is not None:
            return self._details_dict

        result = {}
        for player_pk, data in self.details.items():
            serializer = MatchDetailsSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            result[int(player_pk)] = serializer.save()

        self._details_dict = result
        return self._details_dict

    rounds = fields.JSONField()
    _rounds_list = None
    @property
    def rounds_list(self):
        if self._rounds_list is not None:
            return self._rounds_list

        result = []
        for data in self.rounds:
            serializer = RoundSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            result.append(serializer.save())

        self._rounds_list = result
        return self._rounds_list

    total_rounds = fields.ComputedIntegerField(func=lambda match: len(match.rounds))
    # TODO could be a computed field
    current_round = models.PositiveSmallIntegerField(default=1)
    # TODO could be a computed field
    images = fields.RelatedSetField('Image', related_name='matches')

    status = fields.CharField(max_length=1, choices=MATCH_STATUSES, default=WAITING)
    timeout = models.PositiveIntegerField(default=STANDARD_TIMEOUT)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def respond(self, player_pk, accept=False):
        player_details = self.player_match_details.get(player=player_pk)
        if player_details.invitation_status != MatchDetails.INVITED:
            raise ValueError('Player already responded to this invitation')

        player_details.invitation_status = (MatchDetails.ACCEPTED if accept
                                            else MatchDetails.DECLINED)
        player_details.date_responded = timezone.now()
        player_details.save()

        self.check_status(player_details.pk)

        return self

    def check_status(self, *updated):
        self.status = (Match.WAITING
                       if any(details.invitation_status != MatchDetails.ACCEPTED
                              for details
                              in ensure_instances_consistent(self.player_match_details.all(),
                                                             updated))
                       else Match.IN_PROGESS)

        prev_round = None
        curr_round = None

        for curr_round in self.rounds.order_by('number'):
            curr_round = curr_round.check_status(*updated, match=self, prev_round=prev_round)
            if curr_round.is_current_round:
                self.current_round = curr_round.number
            prev_round = curr_round

        if prev_round.status == Round.FINISHED:
            self.status = Match.FINISHED

        self.save()

        return self

    def score(self, *updated):
        scores = defaultdict(int)

        for round_ in self.rounds.order_by('number'):
            round_scores = round_.score(*updated)
            for player, value in round_scores.items():
                scores[player] += value

        for details in self.player_match_details.all():
            details.score = scores[details.player.pk]
            details.save()

        return scores

    def save(self, *args, **kwargs):
        if self._details_dict is not None:
            self.details = {player_pk: MatchDetailsSerializer(instance=details).data
                            for player_pk, details in self._details_dict}

        if self._rounds_list is not None:
            self.rounds = RoundSerializer(instance=self._rounds_list, many=True).data

        super(Match, self).save(*args, **kwargs)

    def __str__(self):
        return '#%d: %s' % (self.id, ', '.join([str(p) for p in self.players.all()]))

    class Meta(object):
        ordering = ('-last_modified',)
        verbose_name_plural = 'matches'


class Player(models.Model):
    user = models.OneToOneField(GaeDatastoreUser, on_delete=models.CASCADE)
    avatar = models.ForeignKey('Image',
                               related_name='avatars',
                               blank=True, null=True,
                               on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    class Meta(object):
        ordering = ('-last_modified',)


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

    def __str__(self):
        return str(self.url)

    def is_available_to(self, player=None):
        return self.is_available_publically or (player and player == self.owner)

    class Meta(object):
        ordering = ('-last_modified',)
