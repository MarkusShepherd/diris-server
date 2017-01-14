from django.db import models
# from django.contrib.auth.models import User
from diris.settings import AUTH_USER_MODEL
from django.utils import timezone
import random

class MatchManager(models.Manager):
    def create_match(self, player_details=None, players=None, total_rounds=0, timeout=0):
        if not player_details:
            if not players:
                raise ValueError('Need to give players in the match')

            player_details = [{'player': player, 'is_inviting_player': False}
                for player in players]
            player_details[0]['is_inviting_player'] = True

        if len(player_details) < Match.MINIMUM_PLAYER:
            raise ValueError('Not enough players - need to give at least %d players to create a match'
                % Match.MINIMUM_PLAYER)

        if not total_rounds:
            total_rounds = len(player_details)
        data = {'total_rounds': total_rounds}

        if timeout:
            data['timeout'] = timeout

        match = self.create(**data)

        for player_detail in player_details:
            is_inviting_player = player_detail.get('is_inviting_player', False)
            player_detail['match'] = match
            player_detail['invitation_status'] = (PlayerMatchDetails.ACCEPTED
                if is_inviting_player else PlayerMatchDetails.INVITED)
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
            round = Round.objects.create(**data)

            for player in players:
                data = {
                    'player': player,
                    'round': round,
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

    players = models.ManyToManyField('Player', related_name='matches', through='PlayerMatchDetails')
    total_rounds = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=1, choices=MATCH_STATUSES, default=WAITING)
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

        if all([detail.invitation_status == PlayerMatchDetails.ACCEPTED
            for detail in self.player_match_details.all()]):
            self.status = Match.IN_PROGESS
            self.save()

            first_round = self.rounds.get(number=1)
            first_round.is_current_round = True
            first_round.status = Round.SUBMIT_STORY
            first_round.save()

        return self

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

    match = models.ForeignKey(Match, related_name='rounds', on_delete=models.CASCADE)
    players = models.ManyToManyField('Player',
        related_name='rounds',
        through='PlayerRoundDetails',
        through_fields=('round', 'player'))
    number = models.PositiveSmallIntegerField()
    is_current_round = models.BooleanField(default=False)
    status = models.CharField(max_length=1, choices=ROUND_STATUSES, default=WAITING)
    story = models.CharField(max_length=256, blank=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Match #%d Round #%d' % (self.match.id, self.number)

    class Meta:
        ordering = ('number',)

class Player(models.Model):
    user = models.OneToOneField(AUTH_USER_MODEL, on_delete=models.CASCADE)
    external_id = models.CharField(max_length=100, unique=True)
    gcm_registration_id = models.CharField(max_length=100, blank=True)
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
    image_url = models.URLField()
    file = models.FileField(upload_to='uploads/%Y/%m/%d/%H/%M/', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.image_url

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
    invitation_status = models.CharField(max_length=1, choices=INVITATION_STATUSES, default=INVITED)
    date_responded = models.DateTimeField(blank=True, null=True)
    score = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return '%s in Match #%d' % (self.player.user.username, self.match.id)

class PlayerRoundDetails(models.Model):
    player = models.ForeignKey(Player, related_name='player_round_details', on_delete=models.PROTECT)
    round = models.ForeignKey(Round, related_name='player_round_details', on_delete=models.CASCADE)
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
        return '%s in %s' % (self.player.user.username, str(self.round))
