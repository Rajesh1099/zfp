
import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_role
from app.core.roles import UserRole
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    UserCreate,
    UserResponse,
)
from app.services.auth_service import AuthService


app = FastAPI(
    title="ZFP Auth Service",
    version="1.0.0",
)

auth_service = AuthService()


@app.get("/health")
def health_check():
    return {
        "service": "auth",
        "status": "healthy",
    }


@app.get("/internal/validate-token")
def validate_token(
    x_service_secret: str = Header(),
    current_user: User = Depends(get_current_user),
):
    expected_secret = os.getenv("INTERNAL_SERVICE_SECRET", "")

    if not expected_secret or not secrets.compare_digest(
        x_service_secret,
        expected_secret,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid service credentials",
        )

    return {
        "user_id": current_user.id,
        "role": current_user.role,
    }


@app.post(
    "/api/v1/users",
    response_model=UserResponse,
)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return auth_service.create_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role,
    )


@app.post("/api/v1/auth/login")
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    return auth_service.login(
        db=db,
        email=login_data.email,
        password=login_data.password,
    )


@app.post("/api/v1/auth/refresh")
def refresh_access_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    return auth_service.refresh_access_token(
        db=db,
        refresh_token=refresh_request.refresh_token,
    )


@app.post("/api/v1/auth/logout")
def logout(
    logout_request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    return auth_service.logout(
        db=db,
        refresh_token=logout_request.refresh_token,
    )


@app.post("/api/v1/auth/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return auth_service.change_password(
        db=db,
        user_id=current_user.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )


@app.get("/api/v1/auth/verify-email")
def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
    return auth_service.verify_email(
        db=db,
        token=token,
    )


@app.post("/api/v1/auth/forgot-password")
def forgot_password(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    return auth_service.request_password_reset(
        db=db,
        email=reset_request.email,
    )


@app.post("/api/v1/auth/reset-password")
def reset_password(
    reset_request: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    return auth_service.reset_password(
        db=db,
        token=reset_request.token,
        new_password=reset_request.new_password,
    )
