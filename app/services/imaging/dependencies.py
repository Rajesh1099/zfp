
import os

import httpx

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.roles import UserRole


bearer_scheme = HTTPBearer(auto_error=False)

AUTH_SERVICE_URL = "http://127.0.0.1:8001"


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        response = httpx.get(
            f"{AUTH_SERVICE_URL}/internal/validate-token",
            headers={
                "Authorization": f"Bearer {credentials.credentials}",
                "X-Service-Secret": os.getenv(
                    "INTERNAL_SERVICE_SECRET",
                    "",
                ),
            },
            timeout=5.0,
        )

        response.raise_for_status()

        return response.json()

    except (httpx.ConnectError, httpx.TimeoutException):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth Service is unavailable",
        )

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Invalid service credentials",
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(*allowed_roles: UserRole):
    def role_checker(
        current_user: dict = Depends(get_current_user),
    ):
        allowed_role_values = {
            role.value for role in allowed_roles
        }

        if current_user["role"] not in allowed_role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return current_user

    return role_checker
