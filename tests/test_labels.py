from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import resolve, reverse
from django.views import View

from task_manager.labels.models import Label

FIXTURES_DIR = Path(__file__).parent / "fixtures"

pytestmark = pytest.mark.django_db


@pytest.fixture
def label_records(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            FIXTURES_DIR / "users.json",
            FIXTURES_DIR / "statuses.json",
            FIXTURES_DIR / "labels.json",
            FIXTURES_DIR / "tasks.json",
            verbosity=0,
        )
    return {
        "user": User.objects.get(username="alice"),
        "important": Label.objects.get(name="Важное"),
        "urgent": Label.objects.get(name="Срочное"),
        "unused": Label.objects.get(name="Без задачи"),
    }


def test_label_string_representation(label_records):
    assert str(label_records["important"]) == "Важное"


def test_label_routes_use_class_based_views(label_records):
    route_args = (
        ("labels:index", ()),
        ("labels:create", ()),
        ("labels:update", (label_records["important"].pk,)),
        ("labels:delete", (label_records["important"].pk,)),
    )

    for route_name, args in route_args:
        view_class = resolve(reverse(route_name, args=args)).func.view_class
        assert issubclass(view_class, View)


@pytest.mark.parametrize(
    ("method", "route_name", "args"),
    (
        ("get", "labels:index", ()),
        ("get", "labels:create", ()),
        ("post", "labels:create", ()),
        ("get", "labels:update", (1,)),
        ("post", "labels:update", (1,)),
        ("get", "labels:delete", (1,)),
        ("post", "labels:delete", (1,)),
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


def test_authenticated_user_can_view_labels(client, label_records):
    client.force_login(label_records["user"])

    response = client.get(reverse("labels:index"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Метки" in content
    assert "Создать метку" in content
    assert "Важное" in content
    assert "Срочное" in content
    assert reverse(
        "labels:update",
        args=[label_records["important"].pk],
    ) in content
    assert reverse(
        "labels:delete",
        args=[label_records["unused"].pk],
    ) in content
    assert "Изменить" in content
    assert "Удалить" in content


def test_labels_menu_link_is_visible_only_after_login(client, label_records):
    guest_content = client.get(reverse("index")).content.decode()
    assert ">Метки<" not in guest_content

    client.force_login(label_records["user"])
    authenticated_content = client.get(reverse("index")).content.decode()

    assert ">Метки<" in authenticated_content
    assert f'href="{reverse("labels:index")}"' in authenticated_content


def test_label_creation_form_has_expected_field(client, label_records):
    client.force_login(label_records["user"])

    response = client.get(reverse("labels:create"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Создать метку" in content
    assert 'name="name"' in content
    assert 'id="id_name"' in content
    assert "Имя" in content
    assert ">Создать<" in content


def test_authenticated_user_can_create_label(client, label_records):
    client.force_login(label_records["user"])

    response = client.post(
        reverse("labels:create"),
        {"name": "Фича"},
        follow=True,
    )
    content = response.content.decode()

    assert response.redirect_chain == [(reverse("labels:index"), 302)]
    assert Label.objects.filter(name="Фича").exists()
    assert "Метка успешно создана" in content
    assert 'role="alert"' in content


def test_duplicate_label_name_shows_validation_error(client, label_records):
    client.force_login(label_records["user"])

    response = client.post(
        reverse("labels:create"),
        {"name": "Важное"},
    )

    assert response.status_code == 200
    assert "уже существует" in response.content.decode()


def test_authenticated_user_can_update_label(client, label_records):
    client.force_login(label_records["user"])
    label = label_records["unused"]
    update_url = reverse("labels:update", args=[label.pk])

    form_response = client.get(update_url)
    form_content = form_response.content.decode()
    assert form_response.status_code == 200
    assert "Изменение метки" in form_content
    assert ">Изменить<" in form_content

    response = client.post(
        update_url,
        {"name": "Документация"},
        follow=True,
    )
    label.refresh_from_db()

    assert response.redirect_chain == [(reverse("labels:index"), 302)]
    assert label.name == "Документация"
    assert "Метка успешно изменена" in response.content.decode()


def test_authenticated_user_can_delete_unused_label(client, label_records):
    client.force_login(label_records["user"])
    label = label_records["unused"]
    delete_url = reverse("labels:delete", args=[label.pk])

    form_response = client.get(delete_url)
    form_content = form_response.content.decode()
    assert form_response.status_code == 200
    assert "Удаление метки" in form_content
    assert "Да, удалить" in form_content

    response = client.post(delete_url, follow=True)

    assert response.redirect_chain == [(reverse("labels:index"), 302)]
    assert not Label.objects.filter(pk=label.pk).exists()
    assert "Метка успешно удалена" in response.content.decode()


def test_label_linked_to_task_cannot_be_deleted(client, label_records):
    client.force_login(label_records["user"])
    label = label_records["important"]

    response = client.post(
        reverse("labels:delete", args=[label.pk]),
        follow=True,
    )
    content = response.content.decode()

    assert response.redirect_chain == [(reverse("labels:index"), 302)]
    assert Label.objects.filter(pk=label.pk).exists()
    assert "Невозможно удалить метку" in content
    assert 'role="alert"' in content


def test_task_form_allows_multiple_labels(client, label_records):
    client.force_login(label_records["user"])

    response = client.get(reverse("tasks:create"))
    content = response.content.decode()

    assert response.status_code == 200
    assert '<select name="labels"' in content
    assert " multiple" in content
