
import jwt
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User
from app.services.orthanc_service import OrthancService


bearer_scheme = HTTPBearer(auto_error=False)


def get_orthanc_service():
    return OrthancService()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = decode_access_token(token)

        user_id = int(payload["sub"])
        issued_at = float(payload["iat"])

    except (
        jwt.InvalidTokenError,
        KeyError,
        ValueError,
        TypeError,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user or not user.active or not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not eligible for access",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.tokens_valid_after is not None:
        issued_at_datetime = datetime.fromtimestamp(
            issued_at,
            tz=timezone.utc,
        )

        if issued_at_datetime < user.tokens_valid_after:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Access token is no longer valid. "
                    "Please log in again."
                ),
                headers={"WWW-Authenticate": "Bearer"},
            )

    return user


def require_role(*allowed_roles: UserRole):
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        allowed_role_values = {
            role.value for role in allowed_roles
        }

        if current_user.role not in allowed_role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return current_user

    return role_checker
