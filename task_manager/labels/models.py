from django.db import models
from django.db.models.deletion import ProtectedError


class Label(models.Model):
    name = models.CharField("Имя", max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if self.tasks.exists():
            raise ProtectedError("Label is linked to tasks", [self])
        return super().delete(*args, **kwargs)
