from django.db import models

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

    players = models.ManyToManyField(Player, through='PlayerMatchDetails')
    total_rounds = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=1, choices=MATCH_STATUSES, default=WAITING)
    timeout = models.PositiveIntegerField(default=STANDARD_TIMEOUT)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return ', '.join(self.players)

    class Meta:
        ordering = ('created')

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

    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    players = models.ManyToManyField(Player, through='PlayerRoundDetails', through_fields=('player', 'round'))
    number = models.PositiveSmallIntegerField()
    is_current_round = models.BooleanField(default=False)
    status = models.CharField(max_length=1, choices=ROUND_STATUSES, default=WAITING)
    story = models.CharField(max_length=256, blank=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Round #%d' % self.number

    class Meta:
        ordering = ('number')

class Player(modes.Model):
    external_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    avatar = models.ForeignKey(Image, blank=True, null=True, on_delete=models.SET_NULL)
    gcm_registration_id = models.CharField(max_length=100, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name')

class Image(modes.Model):
    url = models.URLField()
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.url

    class Meta:
        ordering = ('created')

class PlayerMatchDetails(models.Model):
    INVITED = 'i'
    ACCEPTED = 'a'
    DECLINED = 'd'
    INVITATION_STATUSES = (
        (INVITED, 'invited'),
        (ACCEPTED, 'accepted'),
        (DECLINED, 'declined'),
    )

    player = models.ForeignKey(Player, on_delete=models.PROTECT)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    is_inviting_player = models.BooleanField(default=False)
    date_invited = models.DateTimeField(auto_now_add=True)
    invitation_status = models.CharField(max_length=1, choices=INVITATION_STATUSES, default=INVITED)
    date_responded = models.DateTimeField(blank=True)
    score = models.PositiveSmallIntegerField(default=0)

class PlayerRoundDetails(models.Model):
    player = models.ForeignKey(Player, on_delete=models.PROTECT)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    is_storyteller = models.BooleanField(default=False)
    image = models.ForeignKey(Image, blank=True, on_delete=models.PROTECT)
    score = models.PositiveSmallIntegerField(default=0)
    vote = models.ForeignKey(Player, blank=True, on_delete=models.PROTECT)

