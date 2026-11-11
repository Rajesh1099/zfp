
from unittest.mock import patch

from app.core.roles import UserRole
from app.core.security import hash_password, create_access_token
from app.models.user import User
from datetime import datetime, timedelta, timezone

import jwt

from datetime import datetime, timedelta, timezone

from app.core.security import (
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken

from app.core.config import settings


def test_studies_requires_authentication(client):
    response = client.get("/api/v1/studies")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_studies_rejects_invalid_token(client):
    response = client.get(
        "/api/v1/studies",
        headers={
            "Authorization": "Bearer invalid_token"
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired access token"


def test_radiologist_cannot_create_user(client, db_session):
    user = User(
        email="radiologist-test@example.com",
        password_hash=hash_password("TestPassword123!"),
        role=UserRole.RADIOLOGIST.value,
        active=True,
        email_verified=True,
    )

    db_session.add(user)
    db_session.flush()

    access_token = create_access_token(
        user_id=user.id,
        role=UserRole.RADIOLOGIST.value,
    )

    response = client.post(
        "/api/v1/users",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "email": "another-user@example.com",
            "password": "AnotherPassword123!",
            "role": "RADIOLOGIST",
        },
    )

    assert response.status_code == 403


def test_admin_can_create_user(client, db_session):
    admin = User(
        email="admin-test@example.com",
        password_hash=hash_password("AdminPassword123!"),
        role=UserRole.ADMIN.value,
        active=True,
        email_verified=True,
    )

    db_session.add(admin)
    db_session.flush()

    access_token = create_access_token(
        user_id=admin.id,
        role=UserRole.ADMIN.value,
    )

    with patch(
        "app.services.auth_service.EmailService.send_verification_email"
    ):
        response = client.post(
            "/api/v1/users",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            json={
                "email": "new-radiologist@example.com",
                "password": "NewPassword123!",
                "role": "RADIOLOGIST",
            },
        )

    assert response.status_code == 200
    assert response.json()["email"] == "new-radiologist@example.com"
    assert response.json()["role"] == "RADIOLOGIST"
    
def test_radiologist_can_access_studies(client, db_session):
    radiologist = User(
        email="radiologist-access@example.com",
        password_hash=hash_password("TestPassword123!"),
        role=UserRole.RADIOLOGIST.value,
        active=True,
        email_verified=True,
    )

    db_session.add(radiologist)
    db_session.flush()

    access_token = create_access_token(
        user_id=radiologist.id,
        role=UserRole.RADIOLOGIST.value,
    )

    with patch(
        "app.api.dependencies.OrthancService.get_studies",
        return_value=[],
    ):
        response = client.get(
            "/api/v1/studies",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
        )

    assert response.status_code == 200
    assert response.json() == []    

def test_unverified_user_cannot_access_studies(client, db_session):
    user = User(
        email="unverified-test@example.com",
        password_hash=hash_password("TestPassword123!"),
        role=UserRole.RADIOLOGIST.value,
        active=True,
        email_verified=False,
    )

    db_session.add(user)
    db_session.flush()

    access_token = create_access_token(
        user_id=user.id,
        role=UserRole.RADIOLOGIST.value,
    )

    response = client.get(
        "/api/v1/studies",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "User account is not eligible for access"
    )    

def test_inactive_user_cannot_access_studies(client, db_session):
    user = User(
        email="inactive-test@example.com",
        password_hash=hash_password("TestPassword123!"),
        role=UserRole.RADIOLOGIST.value,
        active=False,
        email_verified=True,
    )

    db_session.add(user)
    db_session.flush()

    access_token = create_access_token(
        user_id=user.id,
        role=UserRole.RADIOLOGIST.value,
    )

    response = client.get(
        "/api/v1/studies",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "User account is not eligible for access"
    )    


def test_studies_rejects_expired_token(client, db_session):
    user = User(
        email="expired-token@example.com",
        password_hash=hash_password("TestPassword123!"),
        role=UserRole.RADIOLOGIST.value,
        active=True,
        email_verified=True,
    )

    db_session.add(user)
    db_session.flush()

    now = datetime.now(timezone.utc)

    expired_token = jwt.encode(
        {
            "sub": str(user.id),
            "role": UserRole.RADIOLOGIST.value,
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        },
        settings.jwt_secret_key,
        algorithm="HS256",
    )

    response = client.get(
        "/api/v1/studies",
        headers={
            "Authorization": f"Bearer {expired_token}"
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid or expired access token"
    )    

def test_old_access_token_is_rejected(client, db_session):
    user = User(
        email="old-token@example.com",
        password_hash=hash_password("TestPassword123!"),
        role=UserRole.RADIOLOGIST.value,
        active=True,
        email_verified=True,
        tokens_valid_after=datetime.now(timezone.utc),
    )

    db_session.add(user)
    db_session.flush()

    old_issued_at = datetime.now(timezone.utc) - timedelta(minutes=5)

    old_token = jwt.encode(
        {
            "sub": str(user.id),
            "role": UserRole.RADIOLOGIST.value,
            "iat": old_issued_at,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        },
        settings.jwt_secret_key,
        algorithm="HS256",
    )

    response = client.get(
        "/api/v1/studies",
        headers={
            "Authorization": f"Bearer {old_token}"
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Access token is no longer valid. Please log in again."
    )

def test_login_success(client, db_session):
    user = User(
        email="login-test@example.com",
        password_hash=hash_password("TestPassword123!"),
        role=UserRole.RADIOLOGIST.value,
        active=True,
        email_verified=True,
    )

    db_session.add(user)
    db_session.flush()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login-test@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1800   

def test_login_rejects_inactive_user(client, db_session):
    user = User(
        email="inactive-login@example.com",
        password_hash=hash_password("TestPassword123!"),
        role=UserRole.RADIOLOGIST.value,
        active=False,
        email_verified=True,
    )

    db_session.add(user)
    db_session.flush()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "inactive-login@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "User account is inactive"    

def test_refresh_token_success(client, db_session):
    user = User(
        email="refresh-test@example.com",
        password_hash=hash_password("TestPassword123!"),
        role=UserRole.RADIOLOGIST.value,
        active=True,
        email_verified=True,
    )

    db_session.add(user)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "refresh-test@example.com",
            "password": "TestPassword123!",
        },
    )

    old_refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["refresh_token"] != old_refresh_token

    old_record = db_session.query(RefreshToken).filter(
        RefreshToken.token_hash == hash_refresh_token(old_refresh_token)
    ).first()

    assert old_record.revoked is True


def test_refresh_token_rejects_invalid_token(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-refresh-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"


def test_refresh_token_rejects_expired_token(client, db_session):
    user = User(
        email="expired-refresh@example.com",
        password_hash=hash_password("TestPassword123!"),
        role=UserRole.RADIOLOGIST.value,
        active=True,
        email_verified=True,
    )

    db_session.add(user)
    db_session.flush()

    token = "expired-refresh-token"

    record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(token),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        revoked=False,
        created_at=datetime.now(timezone.utc) - timedelta(days=8),
    )

    db_session.add(record)
    db_session.flush()

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": token},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token has expired"         
