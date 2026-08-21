from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from task_manager.labels.forms import LabelForm
from task_manager.labels.models import Label


class LabelListView(LoginRequiredMixin, ListView):
    model = Label
    context_object_name = "labels"
    template_name = "labels/index.html"

    def get_queryset(self):
        return super().get_queryset().order_by("id")


class LabelCreateView(LoginRequiredMixin, CreateView):
    model = Label
    form_class = LabelForm
    template_name = "labels/form.html"
    success_url = reverse_lazy("labels:index")
    extra_context = {
        "title": "Создать метку",
        "button_text": "Создать",
    }

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Метка успешно создана")
        return response


class LabelUpdateView(LoginRequiredMixin, UpdateView):
    model = Label
    form_class = LabelForm
    template_name = "labels/form.html"
    success_url = reverse_lazy("labels:index")
    extra_context = {
        "title": "Изменение метки",
        "button_text": "Изменить",
    }

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Метка успешно изменена")
        return response


class LabelDeleteView(LoginRequiredMixin, DeleteView):
    model = Label
    template_name = "labels/delete.html"
    success_url = reverse_lazy("labels:index")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "Невозможно удалить метку")
            return redirect("labels:index")
        messages.success(self.request, "Метка успешно удалена")
        return response
