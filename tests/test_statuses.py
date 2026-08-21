from pathlib import Path
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db.models.deletion import ProtectedError
from django.urls import resolve, reverse
from django.views import View

from task_manager.statuses.models import Status

FIXTURES_DIR = Path(__file__).parent / "fixtures"

pytestmark = pytest.mark.django_db


@pytest.fixture
def status_records(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            FIXTURES_DIR / "users.json",
            FIXTURES_DIR / "statuses.json",
            verbosity=0,
        )
    return {
        "user": User.objects.get(username="alice"),
        "new": Status.objects.get(name="Новый"),
        "in_progress": Status.objects.get(name="В работе"),
    }


def test_status_string_representation(status_records):
    assert str(status_records["new"]) == "Новый"


def test_status_routes_use_class_based_views(status_records):
    route_args = (
        ("statuses:index", ()),
        ("statuses:create", ()),
        ("statuses:update", (status_records["new"].pk,)),
        ("statuses:delete", (status_records["new"].pk,)),
    )

    for route_name, args in route_args:
        view_class = resolve(reverse(route_name, args=args)).func.view_class
        assert issubclass(view_class, View)


@pytest.mark.parametrize(
    ("method", "route_name", "args"),
    (
        ("get", "statuses:index", ()),
        ("get", "statuses:create", ()),
        ("post", "statuses:create", ()),
        ("get", "statuses:update", (1,)),
        ("post", "statuses:update", (1,)),
        ("get", "statuses:delete", (1,)),
        ("post", "statuses:delete", (1,)),
    ),
)
def test_anonymous_user_is_redirected_to_login(
    client,
    method,
    route_name,
    args,
):
    url = reverse(route_name, args=args)

    response = getattr(client, method)(url)

    assert response.status_code == 302
    assert response.url == f"{reverse('login')}?next={url}"


def test_authenticated_user_can_view_statuses(client, status_records):
    client.force_login(status_records["user"])

    response = client.get(reverse("statuses:index"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Статусы" in content
    assert "Создать статус" in content
    assert "Новый" in content
    assert "В работе" in content
    assert reverse(
        "statuses:update",
        args=[status_records["new"].pk],
    ) in content
    assert reverse(
        "statuses:delete",
        args=[status_records["in_progress"].pk],
    ) in content
    assert "Изменить" in content
    assert "Удалить" in content


def test_statuses_menu_link_is_visible_only_after_login(
    client,
    status_records,
):
    guest_content = client.get(reverse("index")).content.decode()
    assert "Статусы" not in guest_content

    client.force_login(status_records["user"])
    authenticated_content = client.get(reverse("index")).content.decode()

    assert "Статусы" in authenticated_content
    assert f'href="{reverse("statuses:index")}"' in authenticated_content


def test_status_creation_form_has_expected_field(client, status_records):
    client.force_login(status_records["user"])

    response = client.get(reverse("statuses:create"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Создать статус" in content
    assert 'name="name"' in content
    assert 'id="id_name"' in content
    assert "Имя" in content
    assert ">Создать<" in content


def test_authenticated_user_can_create_status(client, status_records):
    client.force_login(status_records["user"])

    response = client.post(
        reverse("statuses:create"),
        {"name": "На тестировании"},
        follow=True,
    )
    content = response.content.decode()

    assert response.redirect_chain == [(reverse("statuses:index"), 302)]
    assert Status.objects.filter(name="На тестировании").exists()
    assert "Статус успешно создан" in content
    assert 'role="alert"' in content


def test_duplicate_status_name_shows_validation_error(client, status_records):
    client.force_login(status_records["user"])

    response = client.post(
        reverse("statuses:create"),
        {"name": "Новый"},
    )

    assert response.status_code == 200
    assert "уже существует" in response.content.decode()


def test_authenticated_user_can_update_status(client, status_records):
    client.force_login(status_records["user"])
    status = status_records["new"]
    update_url = reverse("statuses:update", args=[status.pk])

    form_response = client.get(update_url)
    form_content = form_response.content.decode()
    assert form_response.status_code == 200
    assert "Изменение статуса" in form_content
    assert ">Изменить<" in form_content

    response = client.post(
        update_url,
        {"name": "Завершен"},
        follow=True,
    )
    status.refresh_from_db()

    assert response.redirect_chain == [(reverse("statuses:index"), 302)]
    assert status.name == "Завершен"
    assert "Статус успешно изменен" in response.content.decode()


def test_authenticated_user_can_delete_status(client, status_records):
    client.force_login(status_records["user"])
    status = status_records["new"]
    delete_url = reverse("statuses:delete", args=[status.pk])

    form_response = client.get(delete_url)
    form_content = form_response.content.decode()
    assert form_response.status_code == 200
    assert "Удаление статуса" in form_content
    assert "Да, удалить" in form_content

    response = client.post(delete_url, follow=True)

    assert response.redirect_chain == [(reverse("statuses:index"), 302)]
    assert not Status.objects.filter(pk=status.pk).exists()
    assert "Статус успешно удален" in response.content.decode()


def test_status_linked_to_task_cannot_be_deleted(client, status_records):
    client.force_login(status_records["user"])
    status = status_records["new"]
    protected_error = ProtectedError("Status is in use", [status])

    with patch.object(Status, "delete", side_effect=protected_error):
        response = client.post(
            reverse("statuses:delete", args=[status.pk]),
            follow=True,
        )

    assert response.redirect_chain == [(reverse("statuses:index"), 302)]
    assert Status.objects.filter(pk=status.pk).exists()
    content = response.content.decode()
    assert "Невозможно удалить статус" in content
    assert 'role="alert"' in content
