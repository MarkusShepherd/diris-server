# -*- coding: utf-8 -*-

'''models'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

import hashlib
import logging
import time

# pylint: disable=redefined-builtin
from builtins import int, map, range, str
from collections import defaultdict
from datetime import datetime, timedelta
from io import BytesIO

import requests

from django.conf import settings
from django.core.files.images import ImageFile
from django.db import models
from django.utils import timezone
from django.utils.crypto import random
from djangae import fields, storage
from djangae.contrib.gauth_datastore.models import GaeDatastoreUser
from djangae.contrib.pagination import paginated_model
from djangae.db.consistency import ensure_instance_consistent
from future.utils import python_2_unicode_compatible
from gcm import GCM
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from six import iteritems, itervalues

from .pubsub_utils import PubSubSender
from .utils import calculate_id, clear_list, find_current_round, random_integer

GCM_SENDER = GCM(settings.GCM_API_KEY, debug=settings.DEBUG)
LOGGER = logging.getLogger(__name__)
PUBSUB_SENDER = PubSubSender()
STORAGE = storage.CloudStorage(bucket='diris-app.appspot.com', google_acl='public-read')


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
                 invitation_status=INVITED, date_responded=None, score=0, notification_sent=None):
        self.match = match
        self.player = player
        self.is_inviting_player = is_inviting_player
        self.date_invited = date_invited or timezone.now()
        self.invitation_status = (MatchDetails.ACCEPTED
                                  if is_inviting_player
                                  else invitation_status or MatchDetails.INVITED)
        self.date_responded = date_responded or timezone.now() if is_inviting_player else None
        self.score = score
        self.notification_sent = (notification_sent
                                  or (timezone.now()
                                      if self.invitation_status == MatchDetails.ACCEPTED
                                      else None))


class MatchDetailsSerializer(serializers.Serializer):
    player = serializers.IntegerField()
    is_inviting_player = serializers.BooleanField(default=False)
    date_invited = serializers.DateTimeField(required=False, allow_null=True)
    invitation_status = serializers.ChoiceField(choices=MatchDetails.INVITATION_STATUSES,
                                                default=MatchDetails.INVITED)
    date_responded = serializers.DateTimeField(required=False, allow_null=True)
    score = serializers.IntegerField(min_value=0, default=0)
    notification_sent = serializers.DateTimeField(required=False, allow_null=True)

    def create(self, validated_data):
        return MatchDetails(**validated_data)


class RoundDetails(object):
    def __init__(self, player, match_round=None, is_storyteller=False, image=None,
                 score=0, vote=None, vote_player=None, notification_image_sent=None,
                 notification_vote_sent=None, notification_finished_sent=None):
        self.match_round = match_round
        self.player = player
        self.is_storyteller = is_storyteller
        self.image = image
        self.score = score
        self.vote = vote
        self.vote_player = vote_player
        self.notification_image_sent = notification_image_sent or None
        self.notification_vote_sent = (notification_vote_sent
                                       or (timezone.now() if self.is_storyteller else None))
        self.notification_finished_sent = notification_finished_sent or None

    def display_vote_to(self, match_round=None, player_pk=None):
        match_round = match_round or self.match_round

        if not match_round:
            return bool(player_pk and player_pk == self.player)

        if (match_round.status == Round.FINISHED
                or (player_pk and player_pk == self.player)):
            return True

        details = match_round.details_dict.get(player_pk)
        return bool(details and (details.is_storyteller or details.vote))


class RoundDetailsSerializer(serializers.Serializer):
    player = serializers.IntegerField()
    is_storyteller = serializers.BooleanField(default=False)
    image = serializers.IntegerField(required=False, allow_null=True)
    score = serializers.IntegerField(min_value=0, default=0)
    vote = serializers.IntegerField(required=False, allow_null=True)
    vote_player = serializers.IntegerField(required=False, allow_null=True)
    notification_image_sent = serializers.DateTimeField(required=False, allow_null=True)
    notification_vote_sent = serializers.DateTimeField(required=False, allow_null=True)
    notification_finished_sent = serializers.DateTimeField(required=False, allow_null=True)

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

    DEADLINE_FIELDS = {
        SUBMIT_STORY: 'deadline_story',
        SUBMIT_OTHERS: 'deadline_others',
        SUBMIT_VOTES: 'deadline_votes',
    }

    MAX_DECEIVED_VOTE_SCORE = 3
    DECEIVED_VOTE_SCORE = 1
    ALL_CORRECT_SCORE = 2
    ALL_CORRECT_STORYTELLER_SCORE = 0
    ALL_WRONG_SCORE = 2
    ALL_WRONG_STORYTELLER_SCORE = 0
    NOT_ALL_CORRECT_OR_WRONG_SCORE = 3
    NOT_ALL_CORRECT_OR_WRONG_STORYTELLER_SCORE = 3
    NO_STORY_SCORE = 3
    NO_STORY_STORYTELLER_SCORE = 0

    def __init__(self, number, storyteller, details, match=None,
                 is_current_round=False, status=WAITING, story=None,
                 deadline_story=None, deadline_others=None, deadline_votes=None):
        self.match = match
        self.number = number
        self.storyteller = storyteller
        self.details = details
        self.is_current_round = is_current_round
        self.status = status
        self.story = story
        self.deadline_story = deadline_story
        self.deadline_others = deadline_others
        self.deadline_votes = deadline_votes
        self._details_dict = None

    @property
    def details_dict(self):
        if self._details_dict is not None:
            return self._details_dict

        result = {}
        for player_pk, data in iteritems(self.details):
            serializer = RoundDetailsSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            result[int(player_pk)] = serializer.save(match_round=self)

        self._details_dict = result
        return self._details_dict

    def submit_image(self, player_pk, image_pk, story=None, match=None):
        if not (player_pk and image_pk and Image.objects.filter(pk=image_pk).exists()):
            raise ValueError('player and image are required')

        self.check_status()

        details = self.details_dict[player_pk]

        if details.is_storyteller:
            if self.status != Round.SUBMIT_STORY:
                raise ValueError('not ready for submission')

            if details.image and self.story:
                raise ValueError('image and story already exists')

            if not story:
                raise ValueError('story is required for the storyteller')

            serializer = RoundSerializer()
            story = serializer.fields['story'].run_validation(story)

            self.story = story
            self.status = Round.SUBMIT_OTHERS

        else:
            if self.status != Round.SUBMIT_OTHERS:
                raise ValueError('not ready for submission')

            if details.image:
                raise ValueError('image story already exists')

        details.image = image_pk

        match = match or self.match

        if match:
            match.images_ids.add(image_pk)

    def submit_vote(self, player_pk, image_pk):
        if not player_pk or not image_pk:
            raise ValueError('player and image are required')

        self.check_status()

        details = self.details_dict[player_pk]

        if details.is_storyteller:
            raise ValueError('storyteller cannot vote')

        if details.vote:
            raise ValueError('vote already exists')

        if self.status != Round.SUBMIT_VOTES:
            raise ValueError('not ready for submission')

        vote_player = [d.player for d in itervalues(self.details_dict) if d.image == image_pk]

        if len(vote_player) != 1:
            raise ValueError('image not found in this round')

        vote_player = vote_player[0]

        if player_pk == vote_player:
            raise ValueError('players cannot vote for themselves')

        details.vote = image_pk
        details.vote_player = vote_player

    def check_status(self, match=None, prev_round=None):
        if (all(details.vote for player_pk, details in iteritems(self.details_dict)
                if player_pk != self.storyteller)
                or (self.deadline_votes and timezone.now() > self.deadline_votes)):
            self.status = Round.FINISHED

        elif (all(details.image for details in itervalues(self.details_dict))
              or (self.deadline_others and timezone.now() > self.deadline_others)):
            self.status = Round.SUBMIT_VOTES

        elif self.details_dict[self.storyteller].image and self.story:
            self.status = Round.SUBMIT_OTHERS

        elif self.deadline_story and timezone.now() > self.deadline_story:
            self.status = Round.FINISHED

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
        scores = defaultdict(int)

        if self.status != Round.FINISHED:
            return scores

        if not (self.story and self.details_dict[self.storyteller].image):
            for player_pk, details in iteritems(self.details_dict):
                details.score = (Round.NO_STORY_STORYTELLER_SCORE
                                 if details.is_storyteller else Round.NO_STORY_SCORE)
                scores[player_pk] = details.score
            return scores

        non_storyteller_details = [details for player_pk, details in iteritems(self.details_dict)
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
                if details.vote:
                    scores[details.player] += Round.ALL_WRONG_SCORE

        else:
            scores[self.storyteller] += Round.NOT_ALL_CORRECT_OR_WRONG_STORYTELLER_SCORE
            for details in non_storyteller_details:
                if details.vote_player == self.storyteller:
                    scores[details.player] += Round.NOT_ALL_CORRECT_OR_WRONG_SCORE

        for details in itervalues(self.details_dict):
            details.score = scores[details.player]

        return scores

    def send_notifications(self, match=None):
        match = match or self.match
        match_pk = match.pk if match else None

        if (self.status == Round.SUBMIT_STORY
                and not self.details_dict[self.storyteller].notification_image_sent):
            data = {
                'player_pk': self.storyteller,
                'match_pk': match_pk,
                'title': 'Tell your story!',
                'message': 'A new round has started - tell us your story',
            }
            response = PUBSUB_SENDER.send_message(data=data)

            if response:
                self.details_dict[self.storyteller].notification_image_sent = timezone.now()

        elif self.status == Round.SUBMIT_OTHERS:
            player_pks = [player_pk for player_pk, details in iteritems(self.details_dict)
                          if not (details.is_storyteller or details.notification_image_sent)]

            if player_pks:
                # pylint: disable=no-member
                storyteller = Player.objects.get(pk=self.storyteller).user.username
                data = {
                    'player_pks': player_pks,
                    'match_pk': match_pk,
                    'title': 'Submit your image!',
                    'message': ('Player {} has told their story, now find an image that fits'
                                .format(storyteller)),
                }
                response = PUBSUB_SENDER.send_message(data=data)

                if response:
                    for player_pk in player_pks:
                        self.details_dict[player_pk].notification_image_sent = timezone.now()

        elif self.status == Round.SUBMIT_VOTES:
            player_pks = [player_pk for player_pk, details in iteritems(self.details_dict)
                          if not (details.is_storyteller or details.notification_vote_sent)]

            if player_pks:
                data = {
                    'player_pks': player_pks,
                    'match_pk': match_pk,
                    'title': 'Vote for the right image!',
                    'message': ('Everybody has submitted their image, '
                                'now find the one that fits the story'),
                }
                response = PUBSUB_SENDER.send_message(data=data)

                if response:
                    for player_pk in player_pks:
                        self.details_dict[player_pk].notification_vote_sent = timezone.now()

        elif self.status == Round.FINISHED:
            player_pks = [player_pk for player_pk, details in iteritems(self.details_dict)
                          if not details.notification_finished_sent]

            if player_pks:
                if match and match.status == Match.FINISHED:
                    title = 'The match has finished'
                    message = ('The last round has finished - '
                               'check out the votes and the final scores!')
                else:
                    title = 'The round has finished'
                    message = 'Everybody has submitted their votes, now check out the scores!'

                data = {
                    'player_pks': player_pks,
                    'match_pk': match_pk,
                    'title': title,
                    'message': message,
                }
                response = PUBSUB_SENDER.send_message(data=data)

                if response:
                    for player_pk in player_pks:
                        self.details_dict[player_pk].notification_finished_sent = timezone.now()

    def update_deadlines(self, delta):
        field = self.DEADLINE_FIELDS.get(self.status)

        if field:
            setattr(self, field, getattr(self, field, None) or timezone.now() + delta)

    def display_images_to(self, player_pk=None):
        return bool(self.status in (Round.SUBMIT_VOTES, Round.FINISHED)
                    or (player_pk and player_pk == self.storyteller))


def validate_story(story):
    story_lower = story.lower()

    # TODO add validations like filter words etc. (#20)
    if 'fuck' in story_lower:
        raise ValidationError('story contains blocked word(s)')


class RoundSerializer(serializers.Serializer):
    number = serializers.IntegerField(min_value=1)
    storyteller = serializers.IntegerField()
    details = serializers.DictField(child=RoundDetailsSerializer())
    is_current_round = serializers.BooleanField(default=False)
    status = serializers.ChoiceField(choices=Round.ROUND_STATUSES,
                                     default=Round.WAITING)
    story = serializers.CharField(required=False, allow_null=True,
                                  min_length=Round.MINIMUM_STORY_LENGTH,
                                  allow_blank=False, trim_whitespace=True,
                                  validators=[validate_story])
    deadline_story = serializers.DateTimeField(required=False, allow_null=True)
    deadline_others = serializers.DateTimeField(required=False, allow_null=True)
    deadline_votes = serializers.DateTimeField(required=False, allow_null=True)

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

        group_id = calculate_id((player.pk for player in players), bits=63)
        if (Match.objects.order_by().filter(group_id=group_id)
                .exclude(status__in=[Match.FINISHED, Match.DELETE]).exists()):
            raise ValueError('Match with these players already in progress')

        inviting_player = inviting_player or players[0]

        match_details = {player.pk: MatchDetails(player=player.pk,
                                                 is_inviting_player=player.pk == inviting_player.pk)
                         for player in players}
        match_details_data = {player: MatchDetailsSerializer(instance=details).data
                              for player, details in iteritems(match_details)}

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

        match = self.create(**data)

        for player in players:
            player.total_matches += 1
            player.save(new_match=match)

        return match


@paginated_model(orderings=('deadline_action', 'created', 'last_modified',
                            ('deadline_action', '-last_modified')))
@python_2_unicode_compatible
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
    STANDARD_TIMEOUT = 60 * 60 * 36  # 36 hours
    MINIMUM_PLAYER = 4
    MAXIMUM_PLAYER = 10

    objects = MatchManager()

    players = fields.RelatedSetField('Player', related_name='matches', on_delete=models.PROTECT)
    inviting_player = models.ForeignKey('Player', related_name='inviting_matches',
                                        on_delete=models.PROTECT)
    group_id = fields.ComputedIntegerField(
        func=lambda match: calculate_id(match.players_ids, bits=63),
        blank=True, null=True, default=None)

    details = fields.JSONField()
    _details_dict = None
    rounds = fields.JSONField()
    _rounds_list = None

    total_rounds = fields.ComputedIntegerField(func=lambda match: len(match.rounds))
    current_round = fields.ComputedIntegerField(func=find_current_round, default=-1)
    images = fields.RelatedSetField('Image', related_name='matches')

    status = fields.CharField(max_length=1, choices=MATCH_STATUSES, default=WAITING)
    timeout = models.PositiveIntegerField(default=STANDARD_TIMEOUT)
    deadline_response = models.DateTimeField(blank=True, null=True, default=None)
    deadline_action = models.DateTimeField(default=datetime.max.replace(tzinfo=timezone.utc))
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    finished = models.DateTimeField(blank=True, null=True, default=None)

    class Meta(object):
        ordering = ('deadline_action', '-last_modified')
        verbose_name_plural = 'matches'

    @property
    def details_dict(self):
        if self._details_dict is not None:
            return self._details_dict

        result = {}
        for player_pk, data in iteritems(self.details):
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
        self.check_status()

        if self.status != Match.WAITING:
            raise ValueError('match does not expect invitation responses')

        player_details = self.details_dict[player_pk]
        if player_details.invitation_status != MatchDetails.INVITED:
            raise ValueError('player already responded to this invitation')

        player_details.invitation_status = (MatchDetails.ACCEPTED if accept
                                            else MatchDetails.DECLINED)
        player_details.date_responded = timezone.now()

    def check_status(self):
        self.status = (Match.WAITING
                       if any(details.invitation_status != MatchDetails.ACCEPTED
                              for details in itervalues(self.details_dict))
                       else Match.IN_PROGESS)

        if (self.status == Match.WAITING and self.deadline_response
                and timezone.now() > self.deadline_response):
            LOGGER.info('deadline for invitation response has passed, '
                        'decline invitation of pending players')
            for details in itervalues(self.details_dict):
                details.invitation_status = (MatchDetails.DECLINED
                                             if details.invitation_status == MatchDetails.INVITED
                                             else details.invitation_status)
                details.date_responded = timezone.now()

        for details in itervalues(self.details_dict):
            if details.invitation_status == MatchDetails.DECLINED:
                # TODO remove the player instead (if possible) and adjust rounds & details
                LOGGER.info('player %d declined the invitation, delete the match', details.player)
                self.status = Match.DELETE
                return

        prev_round = None
        # pylint: disable=no-member
        self.images_ids.clear()

        for curr_round in self.rounds_list:
            curr_round.check_status(match=self, prev_round=prev_round)
            if curr_round.is_current_round:
                self.current_round = curr_round.number
            for details in itervalues(curr_round.details_dict):
                if details.image:
                    # pylint: disable=no-member
                    self.images_ids.add(details.image)
            prev_round = curr_round

        if prev_round.status == Round.FINISHED:
            self.status = Match.FINISHED
            self.finished = self.finished or timezone.now()

    def score(self):
        scores = defaultdict(int)

        for round_ in self.rounds_list:
            round_scores = round_.score()
            for player_pk, value in iteritems(round_scores):
                scores[player_pk] += value

        for details in itervalues(self.details_dict):
            details.score = scores[details.player]

        return scores

    def send_notifications(self):
        if self.status == Match.WAITING:
            player_pks = [player_pk for player_pk, details in iteritems(self.details_dict)
                          if not details.notification_sent]
            if player_pks:
                # pylint: disable=no-member
                data = {
                    'player_pks': player_pks,
                    'match_pk': self.pk or '_new',
                    'title': 'New invitation',
                    'message': ('You got an invitation from {}. Do you want to accept it?'
                                .format(self.inviting_player.user.username)),
                }
                response = PUBSUB_SENDER.send_message(data=data)

                if response:
                    for player_pk in player_pks:
                        self.details_dict[player_pk].notification_sent = timezone.now()

        else:
            for round_ in self.rounds_list:
                round_.send_notifications(match=self)

    def send_chat(self, player_pk, text, timestamp=None):
        # pylint: disable=no-member
        if player_pk not in self.players_ids:
            raise ValueError('player <{}> does not participate in this match', player_pk)
        if not text:
            raise ValueError('messages need to have a text')

        group_id = self.group_id
        if group_id is None:
            # pylint: disable=no-member
            group_id = calculate_id(self.players_ids, bits=63)

        # pylint: disable=no-member
        message_group = (MessageGroup.objects
                         .filter(group_id=group_id)
                         .order_by('-sequence', '-last_modified')
                         .first())

        if message_group is None:
            # pylint: disable=no-member
            message_group = MessageGroup.objects.create(group_id=group_id)

        try:
            message = message_group.add(player_pk, text, timestamp)
        except ValueError:
            # pylint: disable=no-member
            message_group = MessageGroup.objects.create(
                group_id=group_id, sequence=message_group.sequence + 1)
            message = message_group.add(player_pk, text, timestamp)
        finally:
            message_group.save()

        LOGGER.debug(message_group)

        data = {
            'player_pks': [pk for pk in self.players_ids if pk != player_pk],
            'match_pk': self.pk or '_new',
            'title': 'New message from {}'.format(self.players.get(pk=player_pk).user.username),
            'message': message.text,
            'sender_pk': player_pk,
            'route': 'chat',
            'timestamp': message.timestamp.isoformat() + 'Z',
            'group_id': group_id,
        }
        response = PUBSUB_SENDER.send_message(data=data)
        LOGGER.debug(response)

        return message_group

    def update_deadlines(self):
        delta = timedelta(seconds=self.timeout or Match.STANDARD_TIMEOUT)

        if self.status == Match.WAITING:
            self.deadline_response = self.deadline_response or timezone.now() + delta
            self.deadline_action = (self.deadline_response
                                    or datetime.max.replace(tzinfo=timezone.utc))

        else:
            for round_ in self.rounds_list:
                round_.update_deadlines(delta)

            if self.status == Match.IN_PROGESS:
                curr_round = self.rounds_list[self.current_round - 1]
                field = Round.DEADLINE_FIELDS.get(curr_round.status) or ''
                self.deadline_action = (getattr(curr_round, field, None)
                                        or datetime.max.replace(tzinfo=timezone.utc))
            else:
                self.deadline_action = datetime.max.replace(tzinfo=timezone.utc)

    def save(self, *args, **kwargs):
        if self.status == Match.DELETE:
            LOGGER.info('match %d marked for deletion', self.pk)
            LOGGER.info(self.delete())

            # pylint: disable=no-member
            for player in self.players.all():
                player.total_matches -= 1
                player.save(new_match=self)

            return

        self.update_deadlines()

        stt = time.time()
        self.send_notifications()
        LOGGER.info('sending PubSub messages took %.3f seconds', time.time() - stt)

        if self._details_dict is not None:
            self.details = {player_pk: MatchDetailsSerializer(instance=details).data
                            for player_pk, details in iteritems(self._details_dict)}

        if self._rounds_list is not None:
            for round_ in self._rounds_list:
                if round_._details_dict is not None:
                    round_.details = {player_pk: RoundDetailsSerializer(instance=details).data
                                      for player_pk, details in iteritems(round_._details_dict)}
            self.rounds = RoundSerializer(instance=self._rounds_list, many=True).data

        super(Match, self).save(*args, **kwargs)

    def __str__(self):
        # pylint: disable=no-member
        return ('match {match_pk} started on {created} (players: {player_pks})'
                .format(match_pk=self.pk, created=self.created,
                        player_pks=', '.join(map(str, self.players_ids))))


@paginated_model(orderings=('total_matches', 'created', 'last_modified',
                            ('-total_matches', '-last_modified')))
@python_2_unicode_compatible
class Player(models.Model):
    user = models.OneToOneField(GaeDatastoreUser, on_delete=models.CASCADE)
    avatar = models.ForeignKey('Image',
                               related_name='avatars',
                               blank=True, null=True,
                               on_delete=models.SET_NULL)
    avatar_url = fields.ComputedCharField(func=lambda p: p.avatar.url if p.avatar else None,
                                          max_length=1500, blank=True, null=True, default=None)
    gcm_registration_id = fields.CharField(blank=True, null=True)
    total_matches = models.PositiveSmallIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta(object):
        ordering = ('-last_modified',)

    def send_message(self, **data):
        if self.gcm_registration_id:
            stt = time.time()
            try:
                response = GCM_SENDER.plaintext_request(registration_id=self.gcm_registration_id,
                                                        data=data)
            except Exception as exc:
                LOGGER.warning(exc)
                response = None
            LOGGER.info('sending GCM messages took %.3f seconds', time.time() - stt)
            return response

    def fetch_avatar(self, url=None, params=None, name=None):
        if not url:
            # pylint: disable=no-member
            gravatar = hashlib.md5(self.user.email.lower()).hexdigest()
            url = 'https://www.gravatar.com/avatar/{}'.format(gravatar)
            name = name or '{}.jpeg'.format(gravatar)
            params = params or {}
            params['s'] = 1080
            params['d'] = 404
            params['r'] = 'pg'

        response = requests.get(url, params=params)
        response.raise_for_status()

        # TODO use url basename instead
        name = name or 'avatar.jpeg'
        image = ImageFile(file=BytesIO(response.content), name=name)
        avatar = Image.objects.create_image(
            file=image,
            size=len(response.content),
            owner=self,
            copyright=Image.OWNER,
            info={'source': url},
        )

        if avatar:
            self.avatar = avatar

        return avatar

    def save(self, new_match=None, *args, **kwargs):
        # TODO inefficient - just have a counter and add sanity check method
        try:
            # pylint: disable=no-member
            if not hasattr(self, 'matches') or self.matches is None:
                self.total_matches = 0
            elif new_match:
                # pylint: disable=no-member
                self.total_matches = ensure_instance_consistent(self.matches, new_match).count()
            else:
                # pylint: disable=no-member
                self.total_matches = self.matches.count()
        except Exception as exc:
            LOGGER.warning(exc)
            self.total_matches = 0

        # pylint: disable=no-member
        if not self.avatar_id:
            try:
                self.fetch_avatar()
            except Exception as exc:
                LOGGER.warning(exc)

        super(Player, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.user)


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
            # pylint: disable=import-error
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


@paginated_model(orderings=('random_order', 'created', 'last_modified'))
@python_2_unicode_compatible
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
    url = fields.ComputedCharField(func=lambda image: '{}?pk={}'.format(image.file.url, image.pk),
                                   max_length=1500, blank=True, null=True, default=None)
    width = models.PositiveSmallIntegerField(blank=True, null=True)
    height = models.PositiveSmallIntegerField(blank=True, null=True)
    size = models.PositiveIntegerField(blank=True, null=True)
    owner = models.ForeignKey(Player, related_name='images',
                              blank=True, null=True, on_delete=models.SET_NULL)
    copyright = fields.CharField(max_length=1, choices=COPYRIGHTS, default=OWNER)
    info = fields.JSONField(blank=True, null=True)
    is_available_publicly = fields.ComputedBooleanField(
        func=lambda image: image.copyright in (image.DIRIS, image.PUBLIC),
        default=False,
    )
    random_order = fields.ComputedIntegerField(func=random_integer, default=random_integer)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta(object):
        ordering = ('-last_modified',)

    def is_available_to(self, player=None):
        return self.is_available_publicly or (player and player == self.owner)

    def __str__(self):
        return self.url


@python_2_unicode_compatible
class Message(object):
    def __init__(self, player, text, timestamp=None):
        super(Message, self).__init__()
        self.player = player
        self.text = text
        self.timestamp = timestamp or timezone.now()

    def __str__(self):
        return '<{}> {}'.format(self.timestamp, self.text)


class MessageSerializer(serializers.Serializer):
    player = serializers.IntegerField()
    text = serializers.CharField(trim_whitespace=True)
    timestamp = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        return Message(**validated_data)


@paginated_model(orderings=('last_modified', 'sequence', ('-last_modified', '-sequence')))
@python_2_unicode_compatible
class MessageGroup(models.Model):
    MAX_SIZE = 100

    group_id = models.PositiveIntegerField()
    sequence = models.PositiveSmallIntegerField(default=0)
    messages = fields.JSONField(default=list)
    _messages_list = None

    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    @property
    def messages_list(self):
        if self._messages_list is not None:
            return self._messages_list

        result = []
        for data in self.messages or ():
            serializer = MessageSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            result.append(serializer.save())

        self._messages_list = result
        return self._messages_list

    def add(self, player, text, timestamp=None):
        if len(self.messages_list) >= MessageGroup.MAX_SIZE:
            raise ValueError('message group capacity exhausted')

        message = Message(player, text, timestamp)
        self.messages_list.append(message)
        return message

    def save(self, *args, **kwargs):
        if self._messages_list is not None:
            sorted_messages = sorted(self._messages_list, key=lambda message: message.timestamp)
            self.messages = MessageSerializer(instance=sorted_messages, many=True).data

        super(MessageGroup, self).save(*args, **kwargs)

    class Meta(object):
        ordering = ('-last_modified', '-sequence')

    def __str__(self):
        return 'message group <{}> #{}'.format(self.group_id, self.sequence)
