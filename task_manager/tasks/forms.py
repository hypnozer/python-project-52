from django import forms
from django.contrib.auth import get_user_model

from task_manager.tasks.models import Task

User = get_user_model()


class UserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, user):
        return user.get_full_name() or user.get_username()


class TaskForm(forms.ModelForm):
    executor = UserChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Исполнитель",
    )

    class Meta:
        model = Task
        fields = (
            "name",
            "description",
            "status",
            "executor",
            "labels",
        )
