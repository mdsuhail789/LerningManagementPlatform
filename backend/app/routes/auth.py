from fastapi import APIRouter, HTTPException, Request, status
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.user import UserOut
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest) -> dict:
    return await auth_service.signup(payload)


@router.post("/login", response_model=TokenResponse)
async def login(request: Request) -> TokenResponse:
    content_type = (request.headers.get("content-type") or "").lower()
    payload_data: dict[str, str]

    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        payload_data = {
            "email": str(form.get("email") or form.get("username") or ""),
            "password": str(form.get("password") or ""),
        }
    else:
        body = await request.json()
        if not isinstance(body, dict):
            raise HTTPException(status_code=422, detail="Invalid login payload")
        payload_data = {
            "email": str(body.get("email") or body.get("username") or ""),
            "password": str(body.get("password") or ""),
        }

    try:
        payload = LoginRequest(**payload_data)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    return await auth_service.login(payload)


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest) -> dict:
    return await auth_service.forgot_password(payload.email)


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest) -> dict:
    return await auth_service.reset_password(payload.token, payload.new_password)
