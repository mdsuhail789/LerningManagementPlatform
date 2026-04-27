from typing import Callable

from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.db.mongodb import get_database
from app.models.user import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _serialize_user(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "email": doc["email"],
        "full_name": doc["full_name"],
        "role": doc["role"],
    }


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise credentials_exception
    return _serialize_user(user)


def require_role(*roles: UserRole) -> Callable:
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        current_role = str(current_user.get("role", "")).strip().lower()
        allowed_roles = {role.value.lower() for role in roles}
        if current_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return role_checker
