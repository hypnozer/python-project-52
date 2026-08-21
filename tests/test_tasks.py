from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import resolve, reverse
from django.views import View

from task_manager.labels.models import Label
from task_manager.statuses.models import Status
from task_manager.tasks.models import Task

FIXTURES_DIR = Path(__file__).parent / "fixtures"

pytestmark = pytest.mark.django_db


@pytest.fixture
def task_records(django_db_setup, django_db_blocker):
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
        "alice": User.objects.get(username="alice"),
        "bob": User.objects.get(username="bob"),
        "new": Status.objects.get(name="Новый"),
        "in_progress": Status.objects.get(name="В работе"),
        "important": Label.objects.get(name="Важное"),
        "urgent": Label.objects.get(name="Срочное"),
        "report": Task.objects.get(name="Подготовить отчёт"),
        "docs": Task.objects.get(name="Проверить документацию"),
    }


def test_task_string_representation(task_records):
    assert str(task_records["report"]) == "Подготовить отчёт"


def test_task_routes_use_class_based_views(task_records):
    route_args = (
        ("tasks:index", ()),
        ("tasks:create", ()),
        ("tasks:update", (task_records["report"].pk,)),
        ("tasks:delete", (task_records["report"].pk,)),
        ("tasks:detail", (task_records["report"].pk,)),
    )

    for route_name, args in route_args:
        view_class = resolve(reverse(route_name, args=args)).func.view_class
        assert issubclass(view_class, View)


@pytest.mark.parametrize(
    ("method", "route_name", "args"),
    (
        ("get", "tasks:index", ()),
        ("get", "tasks:create", ()),
        ("post", "tasks:create", ()),
        ("get", "tasks:update", (1,)),
        ("post", "tasks:update", (1,)),
        ("get", "tasks:delete", (1,)),
        ("post", "tasks:delete", (1,)),
        ("get", "tasks:detail", (1,)),
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


def test_authenticated_user_can_view_tasks(client, task_records):
    client.force_login(task_records["alice"])

    response = client.get(reverse("tasks:index"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Создать задачу" in content
    assert "Подготовить отчёт" in content
    assert "Проверить документацию" in content
    assert "Новый" in content
    assert "alice" in content
    assert "bob" in content
    assert reverse(
        "tasks:detail",
        args=[task_records["report"].pk],
    ) in content
    assert reverse(
        "tasks:update",
        args=[task_records["report"].pk],
    ) in content
    assert reverse(
        "tasks:delete",
        args=[task_records["docs"].pk],
    ) in content
    for action_text in ("Показать", "Изменить", "Удалить"):
        assert action_text in content


def test_tasks_menu_link_is_visible_only_after_login(client, task_records):
    guest_content = client.get(reverse("index")).content.decode()
    assert ">Задачи<" not in guest_content

    client.force_login(task_records["alice"])
    authenticated_content = client.get(reverse("index")).content.decode()

    assert ">Задачи<" in authenticated_content
    assert f'href="{reverse("tasks:index")}"' in authenticated_content


def test_task_creation_form_has_expected_fields(client, task_records):
    client.force_login(task_records["alice"])

    response = client.get(reverse("tasks:create"))
    content = response.content.decode()

    assert response.status_code == 200
    for field_name in (
        "name",
        "description",
        "status",
        "executor",
        "labels",
    ):
        assert f'name="{field_name}"' in content
        assert f'id="id_{field_name}"' in content
    for label in ("Имя", "Описание", "Статус", "Исполнитель", "Метки"):
        assert label in content
    assert 'name="author"' not in content
    assert ">Создать<" in content


def test_authenticated_user_can_create_task(client, task_records):
    client.force_login(task_records["alice"])

    response = client.post(
        reverse("tasks:create"),
        {
            "name": "Протестировать задачу",
            "description": "Проверить новый CRUD.",
            "status": task_records["new"].pk,
            "executor": task_records["bob"].pk,
            "labels": [
                task_records["important"].pk,
                task_records["urgent"].pk,
            ],
        },
        follow=True,
    )
    task = Task.objects.get(name="Протестировать задачу")
    content = response.content.decode()

    assert response.redirect_chain == [(reverse("tasks:index"), 302)]
    assert task.author == task_records["alice"]
    assert task.executor == task_records["bob"]
    assert set(task.labels.all()) == {
        task_records["important"],
        task_records["urgent"],
    }
    assert "Задача успешно создана" in content
    assert 'role="alert"' in content


def test_duplicate_task_name_shows_validation_error(client, task_records):
    client.force_login(task_records["alice"])

    response = client.post(
        reverse("tasks:create"),
        {
            "name": "Подготовить отчёт",
            "description": "Повтор задачи.",
            "status": task_records["new"].pk,
        },
    )

    assert response.status_code == 200
    assert "уже существует" in response.content.decode()


def test_authenticated_user_can_view_task_details(client, task_records):
    client.force_login(task_records["bob"])

    response = client.get(
        reverse("tasks:detail", args=[task_records["report"].pk]),
    )
    content = response.content.decode()

    assert response.status_code == 200
    for text in (
        "Просмотр задачи",
        "Подготовить отчёт",
        "Собрать данные и подготовить итоговый отчёт.",
        "alice",
        "bob",
        "Новый",
        "Метки:",
        "Важное",
        "Срочное",
        "Изменить",
        "Удалить",
    ):
        assert text in content


def test_authenticated_user_can_update_any_task(client, task_records):
    client.force_login(task_records["bob"])
    task = task_records["report"]
    update_url = reverse("tasks:update", args=[task.pk])

    form_response = client.get(update_url)
    form_content = form_response.content.decode()
    assert form_response.status_code == 200
    assert "Изменение задачи" in form_content
    assert ">Изменить<" in form_content

    response = client.post(
        update_url,
        {
            "name": "Обновлённый отчёт",
            "description": "Новое описание.",
            "status": task_records["in_progress"].pk,
            "executor": task_records["alice"].pk,
            "labels": [task_records["urgent"].pk],
        },
        follow=True,
    )
    task.refresh_from_db()

    assert response.redirect_chain == [(reverse("tasks:index"), 302)]
    assert task.name == "Обновлённый отчёт"
    assert task.author == task_records["alice"]
    assert task.executor == task_records["alice"]
    assert list(task.labels.all()) == [task_records["urgent"]]
    assert "Задача успешно изменена" in response.content.decode()


def test_only_author_can_delete_task(client, task_records):
    client.force_login(task_records["bob"])
    task = task_records["report"]

    response = client.post(
        reverse("tasks:delete", args=[task.pk]),
        follow=True,
    )
    content = response.content.decode()

    assert response.redirect_chain == [(reverse("tasks:index"), 302)]
    assert Task.objects.filter(pk=task.pk).exists()
    assert "Задачу может удалить только ее автор" in content
    assert 'role="alert"' in content


def test_author_can_delete_task(client, task_records):
    client.force_login(task_records["alice"])
    task = task_records["report"]
    delete_url = reverse("tasks:delete", args=[task.pk])

    form_response = client.get(delete_url)
    form_content = form_response.content.decode()
    assert form_response.status_code == 200
    assert "Удаление задачи" in form_content
    assert "Да, удалить" in form_content

    response = client.post(delete_url, follow=True)

    assert response.redirect_chain == [(reverse("tasks:index"), 302)]
    assert not Task.objects.filter(pk=task.pk).exists()
    assert "Задача успешно удалена" in response.content.decode()


def test_task_prevents_linked_status_deletion(client, task_records):
    client.force_login(task_records["alice"])
    status = task_records["new"]

    response = client.post(
        reverse("statuses:delete", args=[status.pk]),
        follow=True,
    )

    assert response.redirect_chain == [(reverse("statuses:index"), 302)]
    assert Status.objects.filter(pk=status.pk).exists()
    assert "Невозможно удалить статус" in response.content.decode()


@pytest.mark.parametrize("username", ("alice", "bob"))
def test_task_prevents_linked_user_deletion(
    client,
    task_records,
    username,
):
    user = task_records[username]
    client.force_login(user)

    response = client.post(
        reverse("users:delete", args=[user.pk]),
        follow=True,
    )

    assert response.redirect_chain == [(reverse("users:index"), 302)]
    assert User.objects.filter(pk=user.pk).exists()
    assert "Невозможно удалить пользователя" in response.content.decode()
