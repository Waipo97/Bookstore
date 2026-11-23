import pytest
from django.contrib.auth.models import User
from model_bakery import baker
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def tmp_media(settings, tmp_path):
    """Uploaded files in tests go to a temp folder, not to ./media."""
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def user(db):
    return baker.make(User, username="reader")


@pytest.fixture
def other_user(db):
    return baker.make(User, username="stranger")


@pytest.fixture
def superuser(db):
    return baker.make(User, username="boss", is_superuser=True, is_staff=True)


@pytest.fixture
def api(user):
    """API client logged in as a normal user."""
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def super_api(superuser):
    client = APIClient()
    client.force_authenticate(superuser)
    return client
