import asyncio
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

from fastapi import HTTPException

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.mongodb import get_database
from app.models.user import UserRole
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse


async def signup(payload: SignupRequest) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    existing = await db.users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_doc = {
        "email": payload.email.lower(),
        "full_name": payload.full_name,
        "password_hash": get_password_hash(payload.password),
        "role": UserRole.USER.value,
        "created_at": datetime.now(timezone.utc),
        "learnflow": {},
        "tier_label": "Learner",
    }
    result = await db.users.insert_one(user_doc)
    uid = str(result.inserted_id)

    # Ensure new users can add tasks immediately: create a default course.
    # The UI requires a course to attach tasks to.
    now = datetime.now(timezone.utc)
    await db.courses.insert_one(
        {
            "owner_id": uid,
            "title": "General",
            "description": "Default course created for your tasks.",
            "created_at": now,
            "category": "General",
            "category_theme": "blue",
            "cta_theme": "blue",
            "theme_color": "blue",
            "author": payload.full_name,
            "module_count": 0,
            "certificate_eligible": False,
            "course_status": "in_progress",
            "saved": False,
            "hours_remaining_label": None,
            "image_url": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800",
        }
    )
    return {
        "id": uid,
        "email": user_doc["email"],
        "full_name": user_doc["full_name"],
        "role": user_doc["role"],
    }


async def login(payload: LoginRequest) -> TokenResponse:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    user = await db.users.find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(subject=str(user["_id"]))
    return TokenResponse(access_token=token)


def _send_reset_email(to_email: str, token: str):
    server = settings.smtp_server
    port = settings.smtp_port or 587
    username = settings.smtp_username
    password = settings.smtp_password

    link = f"http://localhost:5173/reset-password?token={token}"
    msg_body = f"Hello,\n\nPlease click the following link to reset your password:\n{link}\n\nThis link will expire in 1 hour.\nIf you did not request this, please ignore this email."

    msg = MIMEText(msg_body)
    msg["Subject"] = "Password Reset Request"
    msg["From"] = username or "noreply@learnflow.local"
    msg["To"] = to_email

    if not server or not username or not password:
        # Fallback to console print if no SMTP configured
        print("\n" + "="*50)
        print("MOCK EMAIL SENT (SMTP not configured in .env):")
        print(f"To: {to_email}")
        print(f"Body:\n{msg_body}")
        print("="*50 + "\n")
        return

    try:
        with smtplib.SMTP(server, port) as smtp:
            smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {e}")


async def forgot_password(email: str) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    user = await db.users.find_one({"email": email.lower()})
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")
        
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    await db.password_resets.insert_one({
        "user_id": str(user["_id"]),
        "token": token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })
    
    await asyncio.to_thread(_send_reset_email, email.lower(), token)
    return {"message": "If an account with that email exists, we have sent a password reset link."}


async def reset_password(token: str, new_password: str) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    reset_doc = await db.password_resets.find_one({"token": token})
    if not reset_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
    # Check expiration
    expires_at = reset_doc["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        await db.password_resets.delete_one({"_id": reset_doc["_id"]})
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
    user_id = reset_doc["user_id"]
    from bson import ObjectId
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    new_hash = get_password_hash(new_password)
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"password_hash": new_hash}})
    await db.password_resets.delete_many({"user_id": user_id})
    
    return {"message": "Password has been successfully reset."}
