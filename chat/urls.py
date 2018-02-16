import os
from django.conf import settings
from django.contrib import admin
from django.views.static import serve
from chat import views as chat_views
from django.conf.urls import include, url
from django.contrib.admin.views.decorators import staff_member_required

urlpatterns = [
    #
    #   Admin
    #
    url(r'^admin/', include(admin.site.urls)),

    #
    #  Slack
    #
    url(
        r'^slack/$',
        chat_views.SlackEventWebhook.as_view(),
        name='slack-event-webhook'
    ),

    url(
        r'^slack-slash/',
        chat_views.SlackSlashWebhook.as_view(),
        name='slack-slash-webhook'
    ),


    #
    # Chats
    #
    url(
        r'^live/(?P<channel>.*)$',
        staff_member_required(chat_views.ChatLive.as_view()),
        name='chat_live'
    ),
    url(
        r'^api/(?P<channel>.*)$',
        chat_views.ChatJson.as_view(),
        name='chat_api'
    ),

    #
    # Local JSONP
    #
    url(r'^json/(?P<path>.*)$', serve, {
        'document_root': os.path.join(settings.ROOT_DIR, 'chat', '.json'),
        'show_indexes': True,
    })
]


admin.site.site_header = ("Chat")
admin.site.site_title = ("Chat")
