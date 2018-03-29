import os
from django.conf import settings
from django.contrib import admin
from django.views.static import serve
from chat import views as chat_views
from django.conf.urls import include, url

urlpatterns = [
    #
    #   Admin
    #
    url(r'^admin/', include(admin.site.urls)),

    #
    #  Slack
    #
    url(
        r'^slack/',
        chat_views.SlackEventWebhook.as_view(),
        name='slack-event-webhook'
    ),


    #
    # Chats
    #
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
