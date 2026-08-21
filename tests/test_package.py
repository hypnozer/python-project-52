from task_manager import settings


def test_settings_are_importable():
    assert "webserver" in settings.ALLOWED_HOSTS
    assert "django.contrib.auth.middleware.AuthenticationMiddleware" in (
        settings.MIDDLEWARE
    )
    assert "django.contrib.messages.middleware.MessageMiddleware" in (
        settings.MIDDLEWARE
    )


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
