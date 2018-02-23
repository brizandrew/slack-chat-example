import logging
import calendar
from django.views.generic import View, TemplateView
from chat.models import ChatChannel, ChatMessage
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.test.client import RequestFactory
from django.utils.decorators import classonlymethod
from django.views.generic.detail import SingleObjectMixin
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import get_template
from django.conf import settings
from events import SlackEventHandler


logger = logging.getLogger(__name__)


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


class ChatMessageMixin(object):
    """
    Mixin for class-based views which require live messages for a particular channel.
    """
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


class ChatLive(TemplateView, ChatMessageMixin):
    """
    View to preview a Chat channel and its messages.
    """
    template_name = 'preview.html'

    def get_context_data(self, **kwargs):
        context = super(ChatLive, self).get_context_data(**kwargs)

        context.update({
            'development': settings.DEVELOPMENT,
            'bucket': settings.AWS_BUCKET_NAME,
            'channel': self.channel,
            'messages': self.messages
        })
        return context

    def get(self, request, *args, **kwargs):
        if self.get_chat_messages(self.kwargs['channel']):
            return super(ChatLive, self).get(request, *args, **kwargs)
        else:
            html = get_template('404.html').render()
            return HttpResponse(
                html,
                status=404
            )


class ChatJson(View, ChatMessageMixin):
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

    def get_json(self):
        """
        Creates the JSON feed structure with the necessary elements.
        """
        output_messages = []
        for message in self.messages:
            last_modified_datetime = None
            if message.last_modified_datetime is not None:
                last_modified_datetime = calendar.timegm(
                    message.last_modified_datetime.utctimetuple()
                )

            output_message = {
                'html': message.html,
                'ts': message.ts,
                'last_modified_datetime': last_modified_datetime,
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
            html = get_template('404.html').render()
            return HttpResponse(
                html,
                status=404
            )


class SlackSlashWebhook(SingleObjectMixin, View):
    """
    Receives the Slack slash commands and processes them.
    """
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(
            SlackSlashWebhook, self
        ).dispatch(request, *args, **kwargs)

    def post(self, request):
        """
        Handles the slash command request, and routes it to the right method.
        """
        print request.POST
        token = request.POST.get('token', '')
        channel_name = request.POST.get('channel_name', '')
        channel_id = request.POST.get('channel_id', '')
        command = request.POST.get('command', None)

        # Verify it's a Slack request
        if token != settings.SLACK_VERIFICATION_TOKEN:
            return HttpResponseForbidden()

        # Verify that a command was sent in the request
        if not command:
            return HttpResponse('No command found.', status=400)

        # Verifty the command is a valid command
        command_func_name = command[1:].replace('-', '_')
        try:
            command_func = getattr(self, command_func_name)
        except AttributeError:
            return HttpResponse('SlackSlashWebhook: %s command does not exist.' % command_func_name, status=200)

        # Run the command
        return command_func(request, channel_id, channel_name)

    def verify_channel_exists(self, channel_id):
        """
        Verifies that the channel is a Chat channel.
        Returns True and the channel if it is.
        Retrns False and an error response if it isn't.
        """
        if ChatChannel.objects.filter(channel_id=channel_id).exists():
            channel = ChatChannel.objects.get(channel_id=channel_id)
            return True, channel
        else:
            resp = 'Sorry. It looks like this channel isn\'t a Chat channel yet.'
            resp += ' To make it one, use the `/chat-new slug-of-channel` slash command.'
            return False, resp

    def validate_slug(self, slug):
        """
        Validates a slug entry and returns whether it's valid and
        an error message if applicable.
        """
        admin_url = settings.SITE_URL + '/admin/chat/chatchannel/'
        resp = None

        # Validate it exists
        if slug is None:
            resp = 'Please provide a slug for the channel and story.'
            resp += ' Simply add the slug after the slash command like this:'
            resp += ' `/chat-new slug-of-chat-channel`.'

        # Validate it's not taken
        elif ChatChannel.objects.filter(slug=slug).exists():
            resp = 'The slug `{}` is already taken.'.format(slug)
            resp += ' Go to <{l}|the channel admin panel> to see all the channels,'.format(
                l=admin_url
            )
            resp += ' or try another slug.'

        # Validate it doesn't have invalid characters
        else:
            invalid_characters = [' ', '_', '&', '%']
            for char in invalid_characters:
                if char in slug:
                    resp = 'The slug `{s}` has a `{c}` character in it, which isn\'t allowed.'.format(
                        s=slug,
                        c=char
                    )
                    resp += ' Try again without it.'
                    break

        if resp is None:
            return True, resp
        else:
            return False, resp

    def chat_id(self, request, channel_id, channel_name):
        """
        Usage: "/chat-id"
        Returns the channel id, usable on any channel.
        """
        resp = 'Channel Id: `%s`.' % (
            channel_id
        )
        return HttpResponse(resp, status=200)

    def chat_new(self, request, channel_id, channel_name):
        """
        Usage: "/chat-new [slug-of-channel]"
        Creates a new Chat channel if it doesn't exist.
        """
        admin_url = settings.SITE_URL + '/admin/chat/chatchannel/'
        exists, channel_or_resp = self.verify_channel_exists(channel_id)
        if exists:
            resp = 'This channel is already a Chat channel.'
            resp += ' Go to <{l}|the channel admin panel> to see all the channels.'.format(
                l=admin_url
            )
            return HttpResponse(resp, status=200)

        slug = request.POST.get('text', None)
        slug_valid, invalid_slug_resp = self.validate_slug(slug)
        if not slug_valid:
            return HttpResponse(invalid_slug_resp, status=200)

        try:
            c = ChatChannel(
                channel_id=channel_id,
                slug=slug,
                headline=slug.title()
            )
            c.save()
            admin_url = settings.SITE_URL + '/admin/chat/chatchannel/{}/change'.format(c.pk)
            resp = 'This channel is now a Chat channel.'
            resp += ' You should see a public confirmation message in the channel shortly.'
            resp += ' Go to the <{l}|channel\'s admin> to update this channel\'s'.format(
                l=admin_url
            )
            resp += ' headline, body intro, and live content.'
            return HttpResponse(resp, status=200)
        except:
            resp = 'Sorry, something went wrong trying to create this channel.'
            resp += ' Try going to the <{l}|channel\'s admin> to make it manually.'.format(
                l=admin_url
            )
            return HttpResponse(resp, status=200)
