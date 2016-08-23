# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-22 19:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('matches', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='match',
            old_name='players',
            new_name='player_details',
        ),
        migrations.RenameField(
            model_name='round',
            old_name='players',
            new_name='player_details',
        ),
        migrations.AlterField(
            model_name='player',
            name='avatar',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='used_as_avatars', to='matches.Image'),
        ),
        migrations.AlterField(
            model_name='playermatchdetails',
            name='player',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='match_details', to='matches.Player'),
        ),
        migrations.AlterField(
            model_name='playerrounddetails',
            name='image',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.PROTECT, related_name='used_in_story', to='matches.Image'),
        ),
        migrations.AlterField(
            model_name='playerrounddetails',
            name='player',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='round_details', to='matches.Player'),
        ),
        migrations.AlterField(
            model_name='playerrounddetails',
            name='vote',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.PROTECT, related_name='voted_by', to='matches.Player'),
        ),
        migrations.AlterField(
            model_name='round',
            name='match',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rounds', to='matches.Match'),
        ),
    ]
