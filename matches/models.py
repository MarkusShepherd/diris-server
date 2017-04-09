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

from .utils import clear_list

LOGGER = logging.getLogger(__name__)
STORAGE = storage.CloudStorage(bucket='diris-images', google_acl='public-read')


class MatchManager(models.Manager):
    def create_match(self, players, inviting_player=None, total_rounds=0, timeout=0):
        players = clear_list(players)

        if inviting_player and inviting_player not in players:
            players.insert(0, inviting_player)

        inviting_player = inviting_player or players[0]

        if len(players) < Match.MINIMUM_PLAYER:
            raise ValueError('Not enough players - need to give at least {} players '
                             'to create a match'.format(Match.MINIMUM_PLAYER))

        player_details = [{'player': player, 'is_inviting_player': player == inviting_player}
                          for player in players]

        if not inviting_player:
            player_details[0]['is_inviting_player'] = True

        total_rounds = total_rounds or len(players)

        data = {
            'players': players,
            'inviting_player': inviting_player,
            'total_rounds': total_rounds,
        }

        if timeout:
            data['timeout'] = timeout

        match = self.create(**data)

        for player_detail in player_details:
            is_inviting_player = player_detail.get('is_inviting_player') or False
            player_detail['match'] = match
            player_detail['invitation_status'] = (PlayerMatchDetails.ACCEPTED
                                                  if is_inviting_player
                                                  else PlayerMatchDetails.INVITED)
            player_detail['date_responded'] = timezone.now() if is_inviting_player else None
            PlayerMatchDetails.objects.create(**player_detail)

        random.shuffle(players)

        for i in range(total_rounds):
            data = {
                'match': match,
                'number': i + 1,
                'is_current_round': i == 0,
                'status': Round.WAITING,
                'storyteller': players[i % len(players)],
            }
            match_round = Round.objects.create(**data)

            for player in players:
                data = {
                    'player': player,
                    'match_round': match_round,
                    'is_storyteller': players[i % len(players)] == player,
                }
                PlayerRoundDetails.objects.create(**data)

        return match


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

    players = fields.RelatedSetField('Player', related_name='matches')
    inviting_player = models.ForeignKey('Player', related_name='invited_to',
                                        on_delete=models.PROTECT)
    total_rounds = models.PositiveSmallIntegerField()
    current_round = models.PositiveSmallIntegerField(default=1)
    status = fields.CharField(max_length=1, choices=MATCH_STATUSES, default=WAITING)
    timeout = models.PositiveIntegerField(default=STANDARD_TIMEOUT)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def respond(self, player_pk, accept=False):
        player_details = self.player_match_details.get(player=player_pk)
        if player_details.invitation_status != PlayerMatchDetails.INVITED:
            raise ValueError('Player already responded to this invitation')

        player_details.invitation_status = (PlayerMatchDetails.ACCEPTED if accept
                                            else PlayerMatchDetails.DECLINED)
        player_details.date_responded = timezone.now()
        player_details.save()

        self.check_status(player_details.pk)

        return self

    def check_status(self, *updated):
        self.status = (Match.WAITING
                       if any(details.invitation_status != PlayerMatchDetails.ACCEPTED
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

    def __str__(self):
        return '#%d: %s' % (self.id, ', '.join([str(p) for p in self.players.all()]))

    class Meta(object):
        ordering = ('-last_modified',)
        verbose_name_plural = 'matches'


class Round(models.Model):
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

    match = models.ForeignKey(Match, related_name='rounds', on_delete=models.CASCADE)
    # players = fields.RelatedSetField('Player', related_name='rounds')
    storyteller = models.ForeignKey('Player', related_name='storyteller_in',
                                    on_delete=models.PROTECT)
    number = models.PositiveSmallIntegerField()
    is_current_round = models.BooleanField(default=False)
    status = fields.CharField(max_length=1, choices=ROUND_STATUSES, default=WAITING)
    story = fields.CharField(max_length=256, blank=True)
    last_modified = models.DateTimeField(auto_now=True)

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
        return 'Match #%d Round #%d' % (self.match.id, self.number)

    class Meta(object):
        ordering = ('number',)


class Player(models.Model):
    user = models.OneToOneField(GaeDatastoreUser, on_delete=models.CASCADE)
    avatar = models.ForeignKey('Image',
                               related_name='used_as_avatars',
                               blank=True, null=True,
                               on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    class Meta(object):
        ordering = ('user',)


class GaeImageField(models.ImageField):
    def update_dimension_fields(self, instance, *args, **kwargs):
        # TODO find dimensions
        if self.width_field:
            setattr(instance, self.width_field, -1)
        if self.height_field:
            setattr(instance, self.height_field, -1)


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

    file = GaeImageField(
        upload_to='%Y/%m/%d/%H/%M/',
        storage=STORAGE,
        width_field='width',
        height_field='height',
    )
    width = models.PositiveSmallIntegerField(blank=True, null=True)
    height = models.PositiveSmallIntegerField(blank=True, null=True)
    owner = models.ForeignKey(Player, related_name='images',
                              blank=True, null=True, on_delete=models.PROTECT)
    copyright = fields.CharField(max_length=1, choices=COPYRIGHTS, default=OWNER)
    info = fields.JSONField(blank=True, null=True)
    is_available_publically = fields.ComputedBooleanField(
        func=lambda image: image.copyright in (image.DIRIS, image.PUBLIC),
        default=False,
    )
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.file)

    def is_available_to(self, player=None):
        return self.is_available_publically or (player and player == self.owner)

    class Meta(object):
        ordering = ('created',)


class PlayerMatchDetails(models.Model):
    INVITED = 'i'
    ACCEPTED = 'a'
    DECLINED = 'd'
    INVITATION_STATUSES = (
        (INVITED, 'invited'),
        (ACCEPTED, 'accepted'),
        (DECLINED, 'declined'),
    )

    player = models.ForeignKey(Player, related_name='player_match_details',
                               on_delete=models.PROTECT)
    match = models.ForeignKey(Match, related_name='player_match_details',
                              on_delete=models.CASCADE)
    is_inviting_player = models.BooleanField(default=False)
    date_invited = models.DateTimeField(auto_now_add=True)
    invitation_status = fields.CharField(max_length=1, choices=INVITATION_STATUSES, default=INVITED)
    date_responded = models.DateTimeField(blank=True, null=True)
    score = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return '%s in Match #%d' % (self.player.user.username, self.match.id)


class PlayerRoundDetails(models.Model):
    player = models.ForeignKey(Player, related_name='player_round_details',
                               on_delete=models.PROTECT)
    match_round = models.ForeignKey(Round, related_name='player_round_details',
                                    on_delete=models.CASCADE)
    is_storyteller = models.BooleanField(default=False)
    image = models.ForeignKey(Image,
                              related_name='used_in_round_details',
                              blank=True, null=True,
                              on_delete=models.PROTECT)
    score = models.PositiveSmallIntegerField(default=0)
    vote = models.ForeignKey(Image,
                             related_name='voted_by',
                             blank=True, null=True,
                             on_delete=models.PROTECT)
    vote_player = models.ForeignKey(Player,
                                    related_name='voted_by',
                                    blank=True, null=True,
                                    on_delete=models.PROTECT)

    def __str__(self):
        return '%s in %s' % (self.player.user.username, str(self.match_round))

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
