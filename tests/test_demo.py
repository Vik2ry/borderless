import pytest
from rest_framework.test import APIClient
from accounts.models import User


@pytest.mark.django_db
def test_fx_demo_public():
    client = APIClient()
    r = client.get('/auth/demo/fx/?from=USDx&to=cNGN')
    # service may return 200 with rate or 400 invalid currency
    assert r.status_code in (200, 400)


def test_auth_ping_requires_auth():
    client = APIClient()
    r = client.get('/auth/demo/auth-ping/')
    assert r.status_code == 401


@pytest.mark.django_db
def test_register_and_ping():
    client = APIClient()

    # Register with handle (not username)
    data = {
        'handle': 'testuser',
        'password': 'strongpassword123'
    }
    r = client.post('/auth/register/', data, format="json")
    assert r.status_code == 201, r.data

    # Login accepts handle as username alias
    r2 = client.post('/auth/login/', {
        'username': 'testuser',   # DRF SimpleJWT expects 'username'
        'password': 'strongpassword123'
    }, format="json")
    assert r2.status_code == 200, r2.data

    access = r2.data.get('access')
    assert access, "No access token returned"

    # Authenticated request
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    r3 = client.get('/auth/demo/auth-ping/')
    assert r3.status_code == 200
