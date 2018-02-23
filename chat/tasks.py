import re
import json
import os
import views as chat_views
from chat.models import ChatChannel, ChatUser, ChatMessage
from django.conf import settings
from slackclient import SlackClient

CHAT_COMMENT_TAG = '&lt;#&gt;'


def new_message(channel, data):
    simple_text = data.get('text', '')
    comment_regex = r'^\s*{}'.format(CHAT_COMMENT_TAG)
    if not re.match(comment_regex, simple_text):
        user, c = ChatUser.objects.get_or_create(
            user_id=data['user']
        )
        m = ChatMessage(
            data=json.dumps(data),
            user=user,
            channel=channel
        )
        m.save()


def update_message(data):
    m = ChatMessage.objects.get(ts=data['message']['ts'])
    m.data = json.dumps(data['message'])
    m.save()


def delete_message(data):
    try:
        m = ChatMessage.objects.get(ts=data['deleted_ts'])
    except ChatMessage.DoesNotExist:
        m = None
    if m:
        m.live = False
        m.save()


def post_slack_message(channel, text=None, attachments=None):
    sc = SlackClient(settings.SLACK_BOT_TOKEN)
    sc.api_call(
      "chat.postMessage",
      channel=channel,
      text=text,
      attachments=attachments
    )


def publish_json(channel_id, callback="callback"):
    """
    Render and publish a JSON feed representation of a channel
    to a local file
    """
    # Get the Channel obj
    channel = ChatChannel.objects.get(channel_id=channel_id)

    # Get the JSON from the ChatJson and convert to JSONP
    json_string = chat_views.ChatJson.as_string(channel)
    jsonp_string = "%s(%s);" % (callback, json_string)

    # Used for development or small server load.
    # Consider uploading to a server bucket instead for optimal performance.
    with open(os.path.join(settings.ROOT_DIR, 'chat', '.json', '%s.jsonp' % channel_id), 'w') as f:
        f.write(jsonp_string)
