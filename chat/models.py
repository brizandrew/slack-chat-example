#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import slackdown
import json
from chat import managers
from django.db import models


class ChatChannel(models.Model):
    """
    A Slack channel logged by this application.
    """
    #
    # Slack fields
    #
    channel_id = models.CharField(
        unique=True,
        max_length=300,
        help_text="The id of the channel on Slack."
    )

    #
    # Website fields
    #
    slug = models.SlugField(
        max_length=300,
        unique=True,
        help_text="A slug for the HTML story."
    )
    headline = models.CharField(
        max_length=300,
        help_text="Display headline for the channel."
    )
    description = models.TextField(
        max_length=1000,
        help_text="HTML for the introductory content.",
        blank=True,
    )
    live_content = models.TextField(
        max_length=1000,
        help_text="HTML for the live content.",
        blank=True,
    )

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        import tasks
        if not self.pk:
            msg = '{c} This is now a `Chat` channel. All messages from now will be recorded in Chat.'
            msg += ' Start a message with a `{c}` if you don\'t want it recorded and potentially published.'
            msg = msg.format(
                c=tasks.CHAT_COMMENT_TAG
            )
            tasks.post_slack_message(self.channel_id, text=msg)

        super(ChatChannel, self).save(*args, **kwargs)

        tasks.publish_json(self.channel_id)


class ChatUser(models.Model):
    """
    A Slack user that creates messages.
    """
    user_id = models.CharField(
        max_length=300,
        unique=True
    )
    name = models.CharField(
        max_length=300,
        blank=True,
        help_text='The Slack username'
    )
    real_name = models.CharField(
        max_length=300,
        blank=True,
        help_text="The user's real name from Slack",
    )
    image_24 = models.URLField(max_length=1000)
    image_32 = models.URLField(max_length=1000)
    image_48 = models.URLField(max_length=1000)
    image_72 = models.URLField(max_length=1000)
    image_192 = models.URLField(max_length=1000)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        """
        Return `real_name` or `name` if there is no `real_name`.
        """
        return self.real_name or self.name


class ChatMessage(models.Model):
    """
    A Slack message posted to a channel by a user.
    """
    #
    # Slack fields
    #
    ts = models.CharField(
        max_length=300,
        help_text='Timestamp of the original message used by Slack as unique identifier.'
    )
    user = models.ForeignKey(
        ChatUser,
        on_delete=models.CASCADE,
        help_text='Slack user the message was posted by.'
    )
    channel = models.ForeignKey(
        ChatChannel,
        on_delete=models.CASCADE,
        help_text='Slack channel the message was posted in.'
    )
    data = models.TextField(
        max_length=6000,
        help_text="The message's data"
    )

    #
    # Website fields
    #
    live = models.BooleanField(
        default=True,
        help_text='Is this message live, or was it deleted on Slack?'
    )

    html = models.TextField(
        max_length=3000,
        help_text='HTML code representation of the message.'
    )

    override_text = models.TextField(
        max_length=3000,
        blank=True,
        help_text="Override the message by putting text here."
    )

    objects = models.Manager()
    messages = managers.ChatMessageManager()

    class Meta:
        ordering = ("-ts",)
        get_latest_by = "ts"

    def __str__(self):
        return self.ts

    def update_html(self):
        """
        Updates the html field with the Slack data or
        with the override_text if it's not blank.
        """
        if self.override_text != '':
            override_text_obj = {
                'text': self.override_text
            }
            self.html = slackdown.parse(override_text_obj)
        else:
            self.html = slackdown.parse(json.loads(self.data))

        # convert user references with full names (or usernames as a fallback)
        users = re.finditer(r'@([\w\d]*)', self.html)
        for u in users:
            match = u.group(1)
            if ChatUser.objects.filter(user_id=match).exists():
                user_obj = ChatUser.objects.get(user_id=match)
                name = "@{}".format(user_obj.display_name).replace(" ", "")
                self.html = u"{}<span class='chat-mention'>{}</span>{}".format(
                    self.html[:u.start()],
                    name,
                    self.html[u.end():]
                )

    def save(self, *args, **kwargs):
        self.update_html()

        super(ChatMessage, self).save(*args, **kwargs)

        import tasks
        tasks.publish_json(self.channel.channel_id)
