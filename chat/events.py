import json
import tasks
from django.conf import settings
from slackclient import SlackClient
from models import ChatChannel, ChatUser, ChatMessage
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse


class SlackEventHandler(object):
    slack = SlackClient(settings.SLACK_APP_TOKEN)

    def handle(self, request):
        payload = self.parse_request(request)
        token = payload['token']

        if not self.authorize(token):
            return HttpResponseForbidden()

        request_type = payload['type']
        if request_type == 'url_verification':
            event_function = self.url_verification
        elif request_type == 'event_callback':
            self.log_request(payload)
            event_name = payload['event']['type']
            event_function_name = 'event_%s' % event_name
            try:
                event_function = getattr(self, event_function_name)
            except AttributeError:
                return HttpResponse('SlackEventHandler: %s event does not exist.' % event_name, status=200)
        else:
            return HttpResponse(status=400)

        return event_function(payload)

    def parse_request(self, request):
        payload = json.loads(request.body)
        return payload

    def authorize(self, token):
        verify = False
        if token == settings.SLACK_VERIFICATION_TOKEN:
            verify = True

        return verify

    def log_request(self, payload):
        pass
        # from pprint import pprint
        # with open("slack_log.txt", "a") as f:
        #     f.write('\n\n~~~~~~~~~~~~~~~~~~~~~~~~\n')
        #     f.write('New Request: %s\n' % payload['event']['type'])
        #     f.write('~~~~~~~~~~~~~~~~~~~~~~~~\n')
        #     pprint(payload, f)

    def url_verification(self, payload):
        response_data = {}
        response_data['challenge'] = payload['challenge']

        return JsonResponse(response_data)

    def event_message(self, payload):
        data = payload['event']
        channel_id = data['channel']
        channel = ChatChannel.objects.filter(channel_id=channel_id)

        if channel:
            channel = channel[0]
            subtype = data.get('subtype', None)
            if subtype:
                subtype_function_name = 'message_%s' % subtype
                try:
                    subtype_function = getattr(self, subtype_function_name)
                except AttributeError:
                    return HttpResponse(
                        'SlackEventHandler: %s event message subtype does not exist.' % subtype,
                        status=200
                    )
                return subtype_function(channel, data)
            else:
                return self.message_message_added(channel, data)

        return HttpResponse(status=200)

    def message_message_added(self, channel, data):
        tasks.new_message(channel, data)
        return HttpResponse(status=200)

    def message_message_changed(self, channel, data):
        tasks.update_message(data)
        return HttpResponse(status=200)

    def message_message_deleted(self, channel, data):
        tasks.delete_message(data)
        return HttpResponse(status=200)

    def message_file_share(self, channel, data):
        self.slack.api_call(
            'files.sharedPublicURL',
            file=data['file']['id']
        )

        user, c = ChatUser.objects.get_or_create(
            user_id=data['user']
        )
        m = ChatMessage(
            data=data,
            user=user,
            channel=channel
        )
        m.save()

        return HttpResponse(status=200)
