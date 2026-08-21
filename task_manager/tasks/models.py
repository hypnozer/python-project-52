from django.conf import settings
from django.db import models

from task_manager.labels.models import Label
from task_manager.statuses.models import Status


class Task(models.Model):
    name = models.CharField("Имя", max_length=200, unique=True)
    description = models.TextField("Описание")
    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        related_name="tasks",
        verbose_name="Статус",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tasks",
        verbose_name="Автор",
    )
    executor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="assigned_tasks",
        verbose_name="Исполнитель",
    )
    labels = models.ManyToManyField(
        Label,
        blank=True,
        related_name="tasks",
        verbose_name="Метки",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
