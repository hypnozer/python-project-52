from django import forms
from django.contrib.auth import get_user_model
from django_filters import BooleanFilter, FilterSet, ModelChoiceFilter

from task_manager.labels.models import Label
from task_manager.statuses.models import Status
from task_manager.tasks.forms import UserChoiceField
from task_manager.tasks.models import Task

User = get_user_model()


class UserChoiceFilter(ModelChoiceFilter):
    field_class = UserChoiceField


class TaskFilter(FilterSet):
    status = ModelChoiceFilter(
        queryset=Status.objects.all(),
        label="Статус",
        empty_label="Не выбрано",
    )
    executor = UserChoiceFilter(
        queryset=User.objects.all(),
        label="Исполнитель",
        empty_label="Не выбрано",
    )
    labels = ModelChoiceFilter(
        queryset=Label.objects.all(),
        label="Метка",
        empty_label="Не выбрано",
    )
    self_tasks = BooleanFilter(
        method="filter_self_tasks",
        label="Только свои задачи",
        widget=forms.CheckboxInput,
    )

    class Meta:
        model = Task
        fields = ("status", "executor", "labels")

    def filter_self_tasks(self, queryset, name, value):
        if value:
            return queryset.filter(author=self.request.user)
        return queryset
