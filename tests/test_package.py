from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from task_manager import settings
from task_manager.views import index


def test_settings_are_importable():
    assert "webserver" in settings.ALLOWED_HOSTS


def test_index(client):
    response = client.get("/")
    content = response.content.decode()

    assert response.status_code == 200
    assert "Привет от Хекслета!" in content
    for link_text in (
        "Менеджер задач",
        "Пользователи",
        "Вход",
        "Регистрация",
    ):
        assert link_text in content


def test_messages_are_rendered_as_alerts():
    request = RequestFactory().get("/")
    request.session = {}
    request._messages = FallbackStorage(request)
    messages.success(request, "Готово")

    response = index(request)
    content = response.content.decode()

    assert 'role="alert"' in content
    assert "Готово" in content
