from django.db import models


class ChatMessageQuerySet(models.QuerySet):
    """
    A custom QuerySet for the ChatMessage model that adds some extra features.
    """
    def live(self):
        return self.filter(live=True).order_by('-ts')


class ChatMessageManager(models.Manager):
    """
    A custom Manager for the ChatMessage model that adds some extra features.
    """
    def get_queryset(self):
        return ChatMessageQuerySet(self.model, using=self._db)

    def live(self):
        return self.get_queryset().live()
