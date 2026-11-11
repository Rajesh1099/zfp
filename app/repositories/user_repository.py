
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:

    def get_by_email(
        self,
        db: Session,
        email: str,
    ):
        return (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

    def get_admin(
        self,
        db: Session,
    ):
        return (
            db.query(User)
            .filter(User.role == "ADMIN")
            .first()
        )

    def get_by_verification_token(
        self,
        db: Session,
        token: str,
    ):
        return (
            db.query(User)
            .filter(
                User.email_verification_token == token
            )
            .first()
        )

    def get_by_password_reset_token(
        self,
        db: Session,
        token: str,
    ):
        return (
            db.query(User)
            .filter(
                User.password_reset_token == token
            )
            .first()
        )

    def create(
        self,
        db: Session,
        email: str,
        password_hash: str,
        role: str,
        email_verification_token: str,
        email_verification_token_expires_at: datetime,
    ):
        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
            email_verification_token=email_verification_token,
            email_verification_token_expires_at=(
                email_verification_token_expires_at
            ),
        )

        db.add(user)
        db.flush()

        return user
