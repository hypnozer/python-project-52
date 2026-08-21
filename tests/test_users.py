from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import resolve, reverse
from django.views import View

PASSWORD = "SecurePass123!"
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "users.json"

pytestmark = pytest.mark.django_db


@pytest.fixture
def users(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("loaddata", FIXTURE_PATH, verbosity=0)
    return User.objects.get(username="alice"), User.objects.get(username="bob")


def registration_data(username="charlie"):
    return {
        "first_name": "Чарли",
        "last_name": "Петров",
        "username": username,
        "password1": PASSWORD,
        "password2": PASSWORD,
    }


def test_user_routes_use_class_based_views():
    route_names = (
        "users:index",
        "users:create",
        "login",
        "logout",
    )

    for route_name in route_names:
        view_class = resolve(reverse(route_name)).func.view_class
        assert issubclass(view_class, View)


def test_admin_is_enabled(client):
    response = client.get("/admin/")

    assert response.status_code == 302
    assert response.url.startswith("/admin/login/")


def test_user_list_is_public(client, users):
    alice, bob = users

    response = client.get(reverse("users:index"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Пользователи" in content
    assert "Алиса Смирнова" in content
    assert "Борис Иванов" in content
    assert reverse("users:update", args=[alice.pk]) in content
    assert reverse("users:delete", args=[bob.pk]) in content
    assert "Изменить" in content
    assert "Удалить" in content


def test_registration_form_uses_standard_field_names_and_ids(client):
    response = client.get(reverse("users:create"))
    content = response.content.decode()

    assert response.status_code == 200
    for field_name in (
        "first_name",
        "last_name",
        "username",
        "password1",
        "password2",
    ):
        assert f'name="{field_name}"' in content
        assert f'id="id_{field_name}"' in content
    for text in (
        "Имя",
        "Фамилия",
        "Имя пользователя",
        "Пароль",
        "Подтверждение пароля",
        "Зарегистрировать",
    ):
        assert text in content


def test_user_can_register(client):
    response = client.post(
        reverse("users:create"),
        registration_data(),
        follow=True,
    )
    content = response.content.decode()

    assert response.redirect_chain == [(reverse("login"), 302)]
    assert User.objects.filter(username="charlie").exists()
    assert "Пользователь успешно зарегистрирован" in content
    assert 'role="alert"' in content


def test_user_can_register_with_password_similar_to_username(client):
    data = registration_data(username="e2e-user-123")
    data["password1"] = "e2e-user-123!"
    data["password2"] = "e2e-user-123!"

    response = client.post(reverse("users:create"), data)

    assert response.status_code == 302
    assert response.url == reverse("login")


def test_duplicate_username_shows_validation_error(client, users):
    response = client.post(
        reverse("users:create"),
        registration_data(username="alice"),
    )

    assert response.status_code == 200
    assert "уже существует" in response.content.decode()


def test_login_form_uses_standard_field_names_and_ids(client):
    response = client.get(reverse("login"))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'name="username"' in content
    assert 'id="id_username"' in content
    assert 'name="password"' in content
    assert 'id="id_password"' in content
    assert "Имя пользователя" in content
    assert "Пароль" in content
    assert ">Войти<" in content


def test_user_can_log_in_and_log_out(client, users):
    response = client.post(
        reverse("login"),
        {"username": "alice", "password": PASSWORD},
        follow=True,
    )
    content = response.content.decode()

    assert response.redirect_chain == [(reverse("index"), 302)]
    assert "Вы залогинены" in content
    assert "Выход" in content
    assert "Регистрация" not in content
    assert 'role="alert"' in content

    response = client.post(reverse("logout"), follow=True)
    content = response.content.decode()

    assert response.redirect_chain == [(reverse("index"), 302)]
    assert "Вы разлогинены" in content
    assert "Вход" in content
    assert "Регистрация" in content


def test_logout_does_not_accept_get(client):
    response = client.get(reverse("logout"))

    assert response.status_code == 405


def test_user_can_update_self(client, users):
    alice, _ = users
    client.login(username=alice.username, password=PASSWORD)
    update_url = reverse("users:update", args=[alice.pk])

    form_response = client.get(update_url)
    form_content = form_response.content.decode()
    assert form_response.status_code == 200
    assert "Изменение пользователя" in form_content
    assert ">Изменить<" in form_content

    response = client.post(
        update_url,
        {
            "first_name": "Алёна",
            "last_name": "Смирнова",
            "username": "alice-new",
            "password1": PASSWORD,
            "password2": PASSWORD,
        },
        follow=True,
    )
    alice.refresh_from_db()

    assert response.redirect_chain == [(reverse("users:index"), 302)]
    assert alice.username == "alice-new"
    assert alice.first_name == "Алёна"
    assert alice.check_password(PASSWORD)
    assert "Пользователь успешно изменен" in response.content.decode()


def test_user_cannot_update_another_user(client, users):
    alice, bob = users
    client.login(username=alice.username, password=PASSWORD)

    response = client.get(
        reverse("users:update", args=[bob.pk]),
        follow=True,
    )

    assert response.redirect_chain == [(reverse("users:index"), 302)]
    assert "У вас нет прав для изменения" in response.content.decode()


def test_anonymous_user_is_redirected_from_update(client, users):
    alice, _ = users
    update_url = reverse("users:update", args=[alice.pk])

    response = client.get(update_url)

    assert response.status_code == 302
    assert response.url == f"{reverse('login')}?next={update_url}"


def test_user_can_delete_self(client, users):
    alice, _ = users
    client.login(username=alice.username, password=PASSWORD)
    delete_url = reverse("users:delete", args=[alice.pk])

    form_response = client.get(delete_url)
    form_content = form_response.content.decode()
    assert form_response.status_code == 200
    assert "Удаление пользователя" in form_content
    assert "Да, удалить" in form_content

    response = client.post(delete_url, follow=True)

    assert response.redirect_chain == [(reverse("users:index"), 302)]
    assert not User.objects.filter(pk=alice.pk).exists()
    assert "Пользователь успешно удален" in response.content.decode()


def test_user_cannot_delete_another_user(client, users):
    alice, bob = users
    client.login(username=alice.username, password=PASSWORD)

    response = client.post(
        reverse("users:delete", args=[bob.pk]),
        follow=True,
    )

    assert response.redirect_chain == [(reverse("users:index"), 302)]
    assert User.objects.filter(pk=bob.pk).exists()
    assert "У вас нет прав для изменения" in response.content.decode()
