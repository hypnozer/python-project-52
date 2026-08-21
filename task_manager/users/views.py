from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from task_manager.users.forms import LoginForm, UserForm


class UserListView(ListView):
    model = User
    context_object_name = "users"
    template_name = "users/index.html"

    def get_queryset(self):
        return super().get_queryset().order_by("id")


class UserCreateView(CreateView):
    model = User
    form_class = UserForm
    template_name = "users/form.html"
    success_url = reverse_lazy("login")
    extra_context = {
        "title": "Регистрация",
        "button_text": "Зарегистрировать",
    }

    def form_valid(self, form):
        messages.success(self.request, "Пользователь успешно зарегистрирован")
        return super().form_valid(form)


class UserOwnerRequiredMixin(LoginRequiredMixin):
    permission_message = "У вас нет прав для изменения"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.pk != self.get_object().pk:
            messages.error(request, self.permission_message)
            return redirect("users:index")
        return super().dispatch(request, *args, **kwargs)


class UserUpdateView(UserOwnerRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = "users/form.html"
    success_url = reverse_lazy("users:index")
    extra_context = {
        "title": "Изменение пользователя",
        "button_text": "Изменить",
    }

    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, self.object)
        messages.success(self.request, "Пользователь успешно изменен")
        return response


class UserDeleteView(UserOwnerRequiredMixin, DeleteView):
    model = User
    template_name = "users/delete.html"
    success_url = reverse_lazy("users:index")

    def form_valid(self, form):
        messages.success(self.request, "Пользователь успешно удален")
        return super().form_valid(form)


class UserLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "users/form.html"
    next_page = reverse_lazy("index")
    redirect_field_name = None
    extra_context = {
        "title": "Вход",
        "button_text": "Войти",
    }

    def form_valid(self, form):
        messages.success(self.request, "Вы залогинены")
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("index")

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Вы разлогинены")
        return response
