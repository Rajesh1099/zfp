
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService


class AuthService:

    def __init__(self):
        self.user_repository = UserRepository()
        self.email_service = EmailService()

    def create_user(
        self,
        db: Session,
        email: str,
        password: str,
        role: UserRole,
    ):
        if role == UserRole.ADMIN:
            existing_admin = self.user_repository.get_admin(db)

            if existing_admin:
                raise HTTPException(
                    status_code=400,
                    detail="ADMIN user already exists",
                )

        existing_user = self.user_repository.get_by_email(
            db,
            email,
        )

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered",
            )

        password_hash = hash_password(password)
        verification_token = secrets.token_urlsafe(32)

        token_expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=15)
        )

        try:
            user = self.user_repository.create(
                db=db,
                email=email,
                password_hash=password_hash,
                role=role.value,
                email_verification_token=verification_token,
                email_verification_token_expires_at=token_expires_at,
            )

            db.commit()

        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Unable to create user account",
            )

        try:
            self.email_service.send_verification_email(
                recipient_email=user.email,
                verification_token=verification_token,
            )
        except Exception:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Account was created, but the verification email "
                    "could not be sent. Please retry email delivery."
                ),
            )

        return user

    def verify_email(
        self,
        db: Session,
        token: str,
    ):
        user = self.user_repository.get_by_verification_token(
            db,
            token,
        )

        if not user:
            raise HTTPException(
                status_code=400,
                detail="Invalid email verification token",
            )

        if user.email_verified:
            raise HTTPException(
                status_code=400,
                detail="Email is already verified",
            )

        expires_at = user.email_verification_token_expires_at

        if (
            expires_at is None
            or expires_at <= datetime.now(timezone.utc)
        ):
            raise HTTPException(
                status_code=400,
                detail="Email verification token has expired",
            )

        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_token_expires_at = None

        try:
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Unable to verify email",
            )

        return {
            "message": "Email verified successfully",
        }

    def request_password_reset(
        self,
        db: Session,
        email: str,
    ):
        user = self.user_repository.get_by_email(
            db,
            email,
        )

        success_response = {
            "message": (
                "If an eligible account exists, "
                "a password reset email will be sent."
            )
        }

        if not user or not user.active or not user.email_verified:
            return success_response

        reset_token = secrets.token_urlsafe(32)

        reset_token_expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=15)
        )

        user.password_reset_token = reset_token
        user.password_reset_token_expires_at = (
            reset_token_expires_at
        )

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=503,
                detail="Unable to process the password reset request.",
            )

        try:
            self.email_service.send_password_reset_email(
                recipient_email=user.email,
                reset_token=reset_token,
            )
        except Exception:
            raise HTTPException(
                status_code=503,
                detail=(
                    "The reset request was saved, but the email could "
                    "not be sent. Please retry the request."
                ),
            )

        return success_response

    def reset_password(
        self,
        db: Session,
        token: str,
        new_password: str,
    ):
        user = self.user_repository.get_by_password_reset_token(
            db,
            token,
        )

        if not user:
            raise HTTPException(
                status_code=400,
                detail="Invalid password reset token",
            )

        expires_at = user.password_reset_token_expires_at

        if (
            expires_at is None
            or expires_at <= datetime.now(timezone.utc)
        ):
            raise HTTPException(
                status_code=400,
                detail="Password reset token has expired",
            )

        if not user.active or not user.email_verified:
            raise HTTPException(
                status_code=400,
                detail="Account is not eligible for password reset",
            )

        now = datetime.now(timezone.utc)

        user.password_hash = hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_token_expires_at = None
        user.tokens_valid_after = (
            now.replace(microsecond=0) + timedelta(seconds=1)
        )

        try:
            db.query(RefreshToken).filter(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked.is_(False),
            ).update(
                {RefreshToken.revoked: True},
                synchronize_session=False,
            )

            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Unable to reset password",
            )

        return {
            "message": (
                "Password reset successfully. "
                "Please log in again on your devices."
            ),
        }

    def change_password(
        self,
        db: Session,
        user_id: int,
        current_password: str,
        new_password: str,
    ):
        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        if not user.active or not user.email_verified:
            raise HTTPException(
                status_code=403,
                detail="User account is not eligible",
            )

        if not verify_password(
            current_password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=400,
                detail="Current password is incorrect",
            )

        if verify_password(
            new_password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "New password must be different from current password"
                ),
            )

        now = datetime.now(timezone.utc)

        user.password_hash = hash_password(new_password)
        user.tokens_valid_after = (
            now.replace(microsecond=0) + timedelta(seconds=1)
        )

        try:
            db.query(RefreshToken).filter(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked.is_(False),
            ).update(
                {RefreshToken.revoked: True},
                synchronize_session=False,
            )

            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Unable to change password",
            )

        return {
            "message": (
                "Password changed successfully. "
                "Please log in again on your devices."
            ),
        }

    def login(
        self,
        db: Session,
        email: str,
        password: str,
    ):
        user = self.user_repository.get_by_email(
            db,
            email,
        )

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
            )

        if not user.active:
            raise HTTPException(
                status_code=401,
                detail="User account is inactive",
            )

        if not user.email_verified:
            raise HTTPException(
                status_code=403,
                detail="Email address is not verified",
            )

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
            )

        now = datetime.now(timezone.utc)

        access_token = create_access_token(
            user_id=user.id,
            role=user.role,
        )

        refresh_token = generate_refresh_token()

        refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=now + timedelta(days=7),
            revoked=False,
            created_at=now,
        )

        try:
            db.add(refresh_token_record)
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Unable to create login session",
            )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "expires_in": 1800,
        }

    def refresh_access_token(
        self,
        db: Session,
        refresh_token: str,
    ):
        now = datetime.now(timezone.utc)
        token_hash = hash_refresh_token(refresh_token)

        token_record = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .with_for_update()
            .first()
        )

        if not token_record or token_record.revoked:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token",
            )

        if token_record.expires_at <= now:
            raise HTTPException(
                status_code=401,
                detail="Refresh token has expired",
            )

        user = (
            db.query(User)
            .filter(User.id == token_record.user_id)
            .first()
        )

        if not user or not user.active or not user.email_verified:
            raise HTTPException(
                status_code=401,
                detail="User account is not eligible for refresh",
            )

        session_expires_at = token_record.expires_at
        new_refresh_token = generate_refresh_token()

        replacement_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(new_refresh_token),
            expires_at=session_expires_at,
            revoked=False,
            created_at=now,
        )

        access_token = create_access_token(
            user_id=user.id,
            role=user.role,
        )

        try:
            token_record.revoked = True
            db.add(replacement_record)
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Unable to refresh login session",
            )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": new_refresh_token,
            "expires_in": 1800,
        }

    def logout(
        self,
        db: Session,
        refresh_token: str,
    ):
        token_hash = hash_refresh_token(refresh_token)

        token_record = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .with_for_update()
            .first()
        )

        # Return the same response for unknown or already-revoked
        # tokens so logout does not reveal token validity.
        if not token_record or token_record.revoked:
            return {
                "message": "Logged out successfully",
            }

        token_record.revoked = True

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Unable to log out",
            )

        return {
            "message": "Logged out successfully",
        }
