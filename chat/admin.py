from django.contrib import admin
from .models import ChatChannel, ChatMessage, ChatUser


@admin.register(ChatChannel)
class ChatChannelAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Metadata", {
            'fields': (
                'headline',
                'slug',
                'channel_id',
                'description',
                'live_content',
            )
        }),
    )
    list_display = (
        'channel_id',
        'headline',
        'slug',
    )
    search_fields = ('headline', 'slug', 'channel_id')

    save_on_top = True


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    def overridden(self, obj):
        return obj.override_text != ''
    overridden.boolean = True

    fieldsets = (
        (None, {
            'fields': (
                'html',
                'override_text',
                'user',
                'live',
            )
        }),
    )
    list_display = (
        'ts',
        'html',
        'channel',
        'user',
        'live',
        'overridden',
    )
    search_fields = ('text', 'user')
    save_on_top = True

    list_filter = ('channel__slug', 'live')

    readonly_fields = [
        'html',
        'user',
        'live',
        'overridden',
    ]


@admin.register(ChatUser)
class ChatUserAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Metadata", {
            'fields': (
                'name',
                'real_name',
                'image_24',
                'image_32',
                'image_48',
                'image_72',
                'image_192',
            )
        }),
    )
    list_display = (
        'user_id',
        'name',
        'real_name',
    )
    search_fields = ('user_id', 'name', 'real_name')
    save_on_top = True
