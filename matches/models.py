# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import random

from collections import defaultdict

from django.db import models
# from django.contrib.auth.models import User
from diris.settings import AUTH_USER_MODEL
from djangae.contrib.gauth.datastore.models import GaeDatastoreUser
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from djangae import fields, storage
from djangae.fields import CharField
# from djangae.db.consistency import ensure_instance_consistent

from .utils import ensure_consistency

STORAGE = storage.CloudStorage(bucket='images', google_acl='public-read')

class MatchManager(models.Manager):
    def create_match(self, player_details=None, players=None, total_rounds=0, timeout=0):
        # TODO use request user to mark inviting player

        if not player_details:
            if not players:
                raise ValueError('Need to give players in the match')

            player_details = [{'player': player, 'is_inviting_player': False}
                              for player in players]
            player_details[0]['is_inviting_player'] = True

        else:
            player_details = tuple(player_details)

        # TODO make sure there are no duplicates

        if len(player_details) < Match.MINIMUM_PLAYER:
            raise ValueError('Not enough players - need to give at least %d players to create a match'
                             % Match.MINIMUM_PLAYER)

        players = {details['player'] for details in player_details}
        if not total_rounds:
            total_rounds = len(player_details)
        data = {'players': players, 'total_rounds': total_rounds}

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

        players = [player_detail['player'] for player_detail in player_details]
        random.shuffle(players)

        for i in range(total_rounds):
            data = {
                'match': match,
                'number': i + 1,
                'is_current_round': i == 0,
                'status': Round.WAITING,
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

class Match(models.Model):
    WAITING = 'w'
    IN_PROGESS = 'p'
    FINISHED = 'f'
    MATCH_STATUSES = (
        (WAITING, 'waiting'),
        (IN_PROGESS, 'in progress'),
        (FINISHED, 'finished'),
    )
    STANDARD_TIMEOUT = 60 * 60 * 24 # 24h
    MINIMUM_PLAYER = 4

    objects = MatchManager()

    # players = models.ManyToManyField('Player', related_name='matches', through='PlayerMatchDetails')
    players = fields.RelatedSetField('Player', related_name='matches')
    total_rounds = models.PositiveSmallIntegerField()
    status = fields.CharField(max_length=1, choices=MATCH_STATUSES, default=WAITING)
    timeout = models.PositiveIntegerField(default=STANDARD_TIMEOUT)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def respond(self, player_pk, accept=False):
        player_details = self.player_match_details.get(player=player_pk)
        if player_details.invitation_status != PlayerMatchDetails.INVITED:
            raise ValueError('Player already responded to this invitation')

        player_details.invitation_status = \
            PlayerMatchDetails.ACCEPTED if accept else PlayerMatchDetails.DECLINED
        player_details.date_responded = timezone.now()
        player_details.save()

        if all(details.invitation_status == PlayerMatchDetails.ACCEPTED
               for details in ensure_consistency(self.player_match_details, (player_details.pk,))
                             .exclude(player=player_pk)):
            self.status = Match.IN_PROGESS
            self.save()

            first_round = self.rounds.get(number=1)
            first_round.is_current_round = True
            first_round.status = Round.SUBMIT_STORY
            first_round.save()

        return self

    def check_status(self, last_updated=None):
        player_details = ensure_consistency(self.player_match_details, last_updated).all()

        if any(details.invitation_status != PlayerMatchDetails.ACCEPTED
               for details in player_details):
            self.status = Match.WAITING
            self.save()

        round_ = None
        rounds = ensure_consistency(self.rounds, last_updated, self.pk).order_by('number')
        updated = [self.pk]

        for round_ in rounds:
            round_.check_status(updated)
            updated.append(round_)
            updated.extend(round_.player_round_details.all())

        if round_.status == Round.FINISHED:
            self.status = Match.FINISHED

        self.save()

        return self

    def score(self, last_updated=None):
        rounds = ensure_consistency(self.rounds, last_updated).order_by('number')

        updated = []

        scores = defaultdict(int)

        for round_ in rounds:
            round_scores = round_.score(last_updated)
            for player, value in round_scores.items():
                scores[player] += value

        for details in ensure_consistency(self.player_match_details, last_updated):
            details.score = scores[details.player.pk]
            details.save()

        return scores

    def __str__(self):
        return '#%d: %s' % (self.id, ', '.join([str(p) for p in self.players.all()]))

    class Meta:
        ordering = ('last_modified',)
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
    players = fields.RelatedSetField('Player', related_name='rounds')
    number = models.PositiveSmallIntegerField()
    is_current_round = models.BooleanField(default=False)
    status = fields.CharField(max_length=1, choices=ROUND_STATUSES, default=WAITING)
    story = fields.CharField(max_length=256, blank=True)
    last_modified = models.DateTimeField(auto_now=True)

    def check_status(self, last_updated=None):
        round_details = ensure_consistency(self.player_round_details, last_updated).all()
        storyteller_details = round_details.get(is_storyteller=True)

        if all(details.vote for details in round_details.exclude(is_storyteller=True)):
            self.status = Round.FINISHED

        elif all(details.image for details in round_details):
            self.status = Round.SUBMIT_VOTES

        elif storyteller_details.image and storyteller_details.story:
            self.status = Round.SUBMIT_OTHERS

        elif self.number == 1:
            match = (ensure_consistency(Match.objects, last_updated, self.match.pk)
                     .get(pk=self.match.pk) or self.match)
            self.status = (Round.SUBMIT_STORY if match.status == Match.IN_PROGESS
                           else Round.WAITING)

        else:
            prev_round = round_details.get(match_round__number=self.number - 1)
            self.status = (Round.SUBMIT_STORY if prev_round.status == Round.FINISHED
                           else Round.WAITING)

        self.is_current_round = self.status != Round.FINISHED and self.status != Round.WAITING

        self.save()

        return self

    def score(self, last_updated=None):
        if self.status != Round.FINISHED:
            return self

        round_details = ensure_consistency(self.player_round_details, last_updated).all()
        storyteller_details = round_details.get(is_storyteller=True)
        storyteller = storyteller_details.player

        scores = defaultdict(int)

        for details in round_details.exclude(is_storyteller=True).exclude(vote=storyteller):
            if scores[details.vote.pk] < Round.MAX_DECEIVED_VOTE_SCORE:
                scores[details.vote.pk] += Round.DECEIVED_VOTE_SCORE

        if all(details.vote.pk == storyteller.pk
               for details in round_details.exclude(is_storyteller=True)):
            scores[storyteller.pk] += Round.ALL_CORRECT_STORYTELLER_SCORE
            for details in round_details.exclude(is_storyteller=True):
                scores[details.player.pk] += Round.ALL_CORRECT_SCORE

        elif all(details.vote.pk != storyteller.pk
                 for details in round_details.exclude(is_storyteller=True)):
            scores[storyteller.pk] += Round.ALL_WRONG_STORYTELLER_SCORE
            for details in round_details.exclude(is_storyteller=True):
                scores[details.player.pk] += Round.ALL_WRONG_SCORE

        else:
            scores[storyteller.pk] += Round.NOT_ALL_CORRECT_OR_WRONG_STORYTELLER_SCORE
            for details in round_details.filter(vote=storyteller):
                scores[details.player.pk] += Round.NOT_ALL_CORRECT_OR_WRONG_SCORE

        for details in round_details:
            details.score = scores[details.player.pk]
            details.save()

        return scores

    def __str__(self):
        return 'Match #%d Round #%d' % (self.match.id, self.number)

    class Meta:
        ordering = ('number',)

# class User(GaeDatastoreUser):
#     username = CharField(
#         _('User ID'), unique=True, blank=True, null=True, default=None,
#         # max_length=21, validators=[validate_google_user_id]
#     )

class Player(models.Model):
    user = models.OneToOneField(GaeDatastoreUser, on_delete=models.CASCADE)
    # name = fields.CharField(max_length=10)
    avatar = models.ForeignKey('Image',
                               related_name='used_as_avatars',
                               blank=True, null=True,
                               on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    class Meta:
        ordering = ('user',)

class Image(models.Model):
    file = models.ImageField(upload_to='%Y/%m/%d/%H/%M/', storage=STORAGE)
    owner = models.ForeignKey(Player, related_name='images',
                              blank=True, null=True, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.file)

    class Meta:
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

    player = models.ForeignKey(Player, related_name='player_match_details', on_delete=models.PROTECT)
    match = models.ForeignKey(Match, related_name='player_match_details', on_delete=models.CASCADE)
    is_inviting_player = models.BooleanField(default=False)
    date_invited = models.DateTimeField(auto_now_add=True)
    invitation_status = fields.CharField(max_length=1, choices=INVITATION_STATUSES, default=INVITED)
    date_responded = models.DateTimeField(blank=True, null=True)
    score = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return '%s in Match #%d' % (self.player.user.username, self.match.id)

class PlayerRoundDetails(models.Model):
    player = models.ForeignKey(Player, related_name='player_round_details', on_delete=models.PROTECT)
    match_round = models.ForeignKey(Round, related_name='player_round_details', on_delete=models.CASCADE)
    is_storyteller = models.BooleanField(default=False)
    image = models.ForeignKey(Image,
                              related_name='used_in_round_details',
                              blank=True, null=True,
                              on_delete=models.PROTECT)
    score = models.PositiveSmallIntegerField(default=0)
    vote = models.ForeignKey(Player,
                             related_name='voted_by',
                             blank=True, null=True,
                             on_delete=models.PROTECT)

    def __str__(self):
        return '%s in %s' % (self.player.user.username, str(self.match_round))

    def submit_image(self, image, story=None):
        if self.image:
            raise ValueError('image already exists')

        if not image:
            # TODO other validations
            raise ValueError('image is required')

        if self.is_storyteller:
            if self.match_round.status != Round.SUBMIT_STORY:
                raise ValueError('not ready for submission')

            if not story:
                # TODO validate story further
                raise ValueError('story is required')

            self.match_round.story = story
            self.match_round.status = Round.SUBMIT_OTHERS

        else:
            if self.match_round.status != Round.SUBMIT_OTHERS:
                raise ValueError('not ready for submission')

            if all(details.image for details
                   in self.match_round.player_round_details.exclude(pk=self.pk)):
                self.match_round.status = Round.SUBMIT_VOTES

        self.image = image

        self.save()
        self.match_round.save()

    def submit_vote(self, player_pk):
        if self.is_storyteller:
            raise ValueError('storyteller cannot vote')

        if self.vote:
            raise ValueError('vote already exists')

        if not player_pk:
            # TODO other validations
            raise ValueError('player is required')

        if player_pk == self.player.pk:
            raise ValueError('players cannote vote for themselves')

        if self.match_round.status != Round.SUBMIT_VOTES:
            raise ValueError('not ready for submission')

        self.vote = player_pk
        self.save()

        if all(details.image for details
               in ensure_consistency(self.match_round.player_round_details, self.pk)
                  .exclude(pk=self.pk).exclude(is_storyteller=True)):
            self.match_round.check_status(self.pk)
            self.match_round.score(self.pk)
