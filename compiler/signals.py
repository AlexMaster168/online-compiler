"""Сброс кеша проектов: при сохранении/удалении — сам проект и профиль владельца,
при форке — ещё и проект-источник (у него поменялось число форков) и профиль его автора."""
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver

from .cache import invalidate_snippet
from .models import Snippet


def _invalidate(snippet: Snippet) -> None:
    invalidate_snippet(snippet.pk, snippet.owner_id)
    if snippet.forked_from_id:
        source_owner = Snippet.objects.filter(pk=snippet.forked_from_id).values_list("owner_id", flat=True).first()
        invalidate_snippet(snippet.forked_from_id, source_owner)


@receiver(post_save, sender=Snippet, dispatch_uid="oc-snippet-saved")
def snippet_saved(sender, instance: Snippet, **kwargs) -> None:
    _invalidate(instance)


@receiver(post_delete, sender=Snippet, dispatch_uid="oc-snippet-deleted")
def snippet_deleted(sender, instance: Snippet, **kwargs) -> None:
    _invalidate(instance)


@receiver(pre_delete, sender=Snippet, dispatch_uid="oc-snippet-forks")
def forks_lose_source(sender, instance: Snippet, **kwargs) -> None:
    """У форков удаляемого проекта БД обнулит forked_from (SET_NULL) без сигналов — сбрасываем их сами."""
    for fork_id, owner_id in Snippet.objects.filter(forked_from=instance).values_list("pk", "owner_id"):
        invalidate_snippet(fork_id, owner_id)
