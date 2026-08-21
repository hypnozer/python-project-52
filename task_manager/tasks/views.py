from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from task_manager.tasks.forms import TaskForm
from task_manager.tasks.models import Task


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    context_object_name = "tasks"
    template_name = "tasks/index.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("status", "author", "executor")
            .order_by("id")
        )


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    context_object_name = "task"
    template_name = "tasks/detail.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("status", "author", "executor")
            .prefetch_related("labels")
        )


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/form.html"
    success_url = reverse_lazy("tasks:index")
    extra_context = {
        "title": "Создать задачу",
        "button_text": "Создать",
    }

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Задача успешно создана")
        return response


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/form.html"
    success_url = reverse_lazy("tasks:index")
    extra_context = {
        "title": "Изменение задачи",
        "button_text": "Изменить",
    }

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Задача успешно изменена")
        return response


class TaskAuthorRequiredMixin(LoginRequiredMixin):
    permission_message = "Задачу может удалить только ее автор"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.get_object().author_id != request.user.pk:
            messages.error(request, self.permission_message)
            return redirect("tasks:index")
        return super().dispatch(request, *args, **kwargs)


class TaskDeleteView(TaskAuthorRequiredMixin, DeleteView):
    model = Task
    template_name = "tasks/delete.html"
    success_url = reverse_lazy("tasks:index")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Задача успешно удалена")
        return response
