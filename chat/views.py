from django.views.generic import View
from chat.models import ChatChannel, ChatMessage
from django.http import JsonResponse
from django.test.client import RequestFactory
from django.utils.decorators import classonlymethod
from django.views.generic.detail import SingleObjectMixin
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
from events import SlackEventHandler


class SlackEventWebhook(SingleObjectMixin, View):
    """
    Receives the Slack Events API calls and passes it to the events handler.
    """
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(
            SlackEventWebhook, self
        ).dispatch(request, *args, **kwargs)

    def post(self, request):
        return SlackEventHandler().handle(request)


class ChatJson(View):
    """
    Local JSON feed for a particular Chat channel and its messages.
    """
    @classonlymethod
    def as_string(self, object):
        """
        Renders and returns the JSON response as a plain string.
        """
        request = RequestFactory().get('')
        response = self.as_view()(request, channel=object.channel_id)
        return response.content

    def get_chat_messages(self, channel):
        """
        Get all the messages from channel not marked as deleted.
        """
        if ChatChannel.objects.filter(channel_id=channel).exists():
            self.channel = ChatChannel.objects.get(channel_id=channel)
            self.messages = ChatMessage.messages.live().filter(
                channel__channel_id=channel
            )
            return True
        else:
            return False

    def get_json(self):
        """
        Creates the JSON feed structure with the necessary elements.
        """
        output_messages = []
        for message in self.messages:
            output_message = {
                'html': message.html,
                'ts': message.ts,
                'user': {
                    'image_48': message.user.image_48,
                    'display_name': message.user.display_name
                }
            }
            output_messages.append(output_message)

        return JsonResponse({
            'channel': {
                'id': self.channel.channel_id,
                'headline': self.channel.headline,
                'slug': self.channel.slug,
                'description': self.channel.description,
                'live_content': self.channel.live_content,
            },
            'messages': output_messages
        })

    def get(self, request, *args, **kwargs):
        """
        Returns the latest JSON feed.
        """
        if self.get_chat_messages(self.kwargs['channel']):
            return self.get_json()
        else:
            raise Http404("Channel does not exist")
