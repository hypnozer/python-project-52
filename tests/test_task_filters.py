from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import resolve, reverse
from django_filters.views import FilterView

from task_manager.labels.models import Label
from task_manager.statuses.models import Status
from task_manager.tasks.models import Task

FIXTURES_DIR = Path(__file__).parent / "fixtures"

pytestmark = pytest.mark.django_db


@pytest.fixture
def filter_records(django_db_setup, django_db_blocker):
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


def get_task_names(response):
    return [task.name for task in response.context["tasks"]]


def test_task_list_uses_filter_view(filter_records):
    view_class = resolve(reverse("tasks:index")).func.view_class

    assert issubclass(view_class, FilterView)


def test_filter_form_has_expected_fields_and_labels(client, filter_records):
    client.force_login(filter_records["alice"])

    response = client.get(reverse("tasks:index"))
    content = response.content.decode()

    assert response.status_code == 200
    for field_name in ("status", "executor", "labels", "self_tasks"):
        assert f'name="{field_name}"' in content
        assert f'id="id_{field_name}"' in content
    for label in ("Статус", "Исполнитель", "Метка", "Только свои задачи"):
        assert label in content
    assert ">Показать<" in content


@pytest.mark.parametrize(
    ("parameter", "value", "expected_task"),
    (
        ("status", "new", "report"),
        ("status", "in_progress", "docs"),
        ("executor", "bob", "report"),
        ("labels", "important", "report"),
        ("labels", "urgent", "report"),
    ),
)
def test_tasks_can_be_filtered_by_related_objects(
    client,
    filter_records,
    parameter,
    value,
    expected_task,
):
    client.force_login(filter_records["alice"])

    response = client.get(
        reverse("tasks:index"),
        {parameter: filter_records[value].pk},
    )

    assert response.status_code == 200
    assert get_task_names(response) == [filter_records[expected_task].name]


def test_user_can_view_only_tasks_they_created(client, filter_records):
    client.force_login(filter_records["alice"])

    response = client.get(
        reverse("tasks:index"),
        {"self_tasks": "on"},
    )

    assert response.status_code == 200
    assert get_task_names(response) == [filter_records["report"].name]


def test_filters_can_be_combined(client, filter_records):
    client.force_login(filter_records["alice"])

    response = client.get(
        reverse("tasks:index"),
        {
            "status": filter_records["new"].pk,
            "executor": filter_records["bob"].pk,
            "labels": filter_records["urgent"].pk,
            "self_tasks": "on",
        },
    )

    assert get_task_names(response) == [filter_records["report"].name]


def test_unchecked_self_tasks_filter_keeps_all_tasks(client, filter_records):
    client.force_login(filter_records["alice"])

    response = client.get(
        reverse("tasks:index"),
        {"self_tasks": "false"},
    )

    assert get_task_names(response) == [
        filter_records["report"].name,
        filter_records["docs"].name,
    ]
