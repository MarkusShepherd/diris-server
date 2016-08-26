# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-24 11:21
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_url', models.URLField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('created',),
            },
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_rounds', models.PositiveSmallIntegerField()),
                ('status', models.CharField(choices=[('w', 'waiting'), ('p', 'in progress'), ('f', 'finished')], default='w', max_length=1)),
                ('timeout', models.PositiveIntegerField(default=86400)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('created',),
            },
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.CharField(max_length=100, unique=True)),
                ('gcm_registration_id', models.CharField(blank=True, max_length=100)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('avatar', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='used_as_avatars', to='matches.Image')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('user',),
            },
        ),
        migrations.CreateModel(
            name='PlayerMatchDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_inviting_player', models.BooleanField(default=False)),
                ('date_invited', models.DateTimeField(auto_now_add=True)),
                ('invitation_status', models.CharField(choices=[('i', 'invited'), ('a', 'accepted'), ('d', 'declined')], default='i', max_length=1)),
                ('date_responded', models.DateTimeField(blank=True, null=True)),
                ('score', models.PositiveSmallIntegerField(default=0)),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='player_match_details', to='matches.Match')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='player_match_details', to='matches.Player')),
            ],
        ),
        migrations.CreateModel(
            name='PlayerRoundDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_storyteller', models.BooleanField(default=False)),
                ('score', models.PositiveSmallIntegerField(default=0)),
                ('image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='used_in_round_details', to='matches.Image')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='player_round_details', to='matches.Player')),
            ],
        ),
        migrations.CreateModel(
            name='Round',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveSmallIntegerField()),
                ('is_current_round', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[('w', 'waiting'), ('s', 'submit storyteller'), ('o', 'submit others'), ('v', 'submit votes'), ('f', 'finished')], default='w', max_length=1)),
                ('story', models.CharField(blank=True, max_length=256)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rounds', to='matches.Match')),
                ('players', models.ManyToManyField(related_name='rounds', through='matches.PlayerRoundDetails', to='matches.Player')),
            ],
            options={
                'ordering': ('number',),
            },
        ),
        migrations.AddField(
            model_name='playerrounddetails',
            name='round',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='player_round_details', to='matches.Round'),
        ),
        migrations.AddField(
            model_name='playerrounddetails',
            name='vote',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='voted_by', to='matches.Player'),
        ),
        migrations.AddField(
            model_name='match',
            name='players',
            field=models.ManyToManyField(related_name='matches', through='matches.PlayerMatchDetails', to='matches.Player'),
        ),
    ]
