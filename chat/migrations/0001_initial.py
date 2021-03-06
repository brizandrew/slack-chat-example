# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-02-23 20:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChatChannel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel_id', models.CharField(help_text=b'The id of the channel on Slack.', max_length=300, unique=True)),
                ('slug', models.SlugField(help_text=b'A slug for the HTML story.', max_length=300, unique=True)),
                ('headline', models.CharField(help_text=b'Display headline for the channel.', max_length=300)),
                ('description', models.TextField(blank=True, help_text=b'HTML for the introductory content.', max_length=1000)),
                ('live_content', models.TextField(blank=True, help_text=b'HTML for the live content.', max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ts', models.CharField(help_text=b'Timestamp of the original message used by Slack as unique identifier.', max_length=300)),
                ('data', models.TextField(help_text=b"The message's data", max_length=6000)),
                ('live', models.BooleanField(default=True, help_text=b'Is this message live, or was it deleted on Slack?')),
                ('html', models.TextField(help_text=b'HTML code representation of the message.', max_length=3000)),
                ('override_text', models.TextField(blank=True, help_text=b'Override the message by putting text here.', max_length=3000)),
                ('channel', models.ForeignKey(help_text=b'Slack channel the message was posted in.', on_delete=django.db.models.deletion.CASCADE, to='chat.ChatChannel')),
            ],
            options={
                'ordering': ('-ts',),
                'get_latest_by': 'ts',
            },
        ),
        migrations.CreateModel(
            name='ChatUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(max_length=300, unique=True)),
                ('name', models.CharField(blank=True, help_text=b'The Slack username', max_length=300)),
                ('real_name', models.CharField(blank=True, help_text=b"The user's real name from Slack", max_length=300)),
                ('image_24', models.URLField(max_length=1000)),
                ('image_32', models.URLField(max_length=1000)),
                ('image_48', models.URLField(max_length=1000)),
                ('image_72', models.URLField(max_length=1000)),
                ('image_192', models.URLField(max_length=1000)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='user',
            field=models.ForeignKey(help_text=b'Slack user the message was posted by.', on_delete=django.db.models.deletion.CASCADE, to='chat.ChatUser'),
        ),
    ]
