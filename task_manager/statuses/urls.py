from django.urls import path

from task_manager.statuses.views import (
    StatusCreateView,
    StatusDeleteView,
    StatusListView,
    StatusUpdateView,
)

app_name = "statuses"

urlpatterns = [
    path("", StatusListView.as_view(), name="index"),
    path("create/", StatusCreateView.as_view(), name="create"),
    path("<int:pk>/update/", StatusUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", StatusDeleteView.as_view(), name="delete"),
]
