from django.db import models
from django.contrib.auth.models import User

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

    players = models.ManyToManyField('Player', related_name='matches', through='PlayerMatchDetails')
    total_rounds = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=1, choices=MATCH_STATUSES, default=WAITING)
    timeout = models.PositiveIntegerField(default=STANDARD_TIMEOUT)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '#%d: %s' % (self.id, ', '.join([str(p) for p in self.players.all()]))

    class Meta:
        ordering = ('created',)

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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
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
