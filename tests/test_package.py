from task_manager import settings


def test_settings_are_importable():
    assert "webserver" in settings.ALLOWED_HOSTS


def test_index(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Привет от Хекслета!" in response.content.decode()
