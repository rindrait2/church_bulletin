from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from database import get_db
from dependencies import get_current_user, require_admin
from models.user import User
from schemas.common import APIResponse

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: int
    username: str
    role: str
    active: bool


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "viewer"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("viewer", "editor", "admin"):
            raise ValueError("role must be viewer, editor, or admin")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("password must be at least 6 characters")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("new_password must be at least 6 characters")
        return v


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    active: Optional[bool] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("viewer", "editor", "admin"):
            raise ValueError("role must be viewer, editor, or admin")
        return v


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return access and refresh tokens."""
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )
    access_token = create_access_token({"sub": user.username, "role": user.role})
    refresh_token = create_refresh_token({"sub": user.username, "role": user.role})
    return APIResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        ),
    )


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh an access token using a valid refresh token."""
    payload = decode_token(body.refresh_token)
    username = payload.get("sub")
    token_type = payload.get("type")
    if not username or token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    access_token = create_access_token({"sub": user.username, "role": user.role})
    return APIResponse(
        success=True,
        data=TokenResponse(access_token=access_token, token_type="bearer"),
    )


@router.get("/me", response_model=APIResponse[UserInfo])
async def me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user's info."""
    return APIResponse(
        success=True,
        data=UserInfo(
            id=current_user.id,
            username=current_user.username,
            role=current_user.role,
            active=current_user.active,
        ),
    )


@router.post("/register", response_model=APIResponse[UserInfo], status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Register a new user. Admin only."""
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(
        username=body.username,
        hashed_password=get_password_hash(body.password),
        role=body.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return APIResponse(
        success=True,
        data=UserInfo(id=user.id, username=user.username, role=user.role, active=user.active),
        message="User registered",
    )


@router.put("/password", response_model=APIResponse)
async def change_password(
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the current user's password."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = get_password_hash(body.new_password)
    await db.flush()
    return APIResponse(success=True, message="Password changed successfully")


@router.get("/users", response_model=APIResponse[list[UserInfo]])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """List all users. Admin only."""
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return APIResponse(
        success=True,
        data=[UserInfo(id=u.id, username=u.username, role=u.role, active=u.active) for u in users],
    )


@router.put("/users/{user_id}", response_model=APIResponse[UserInfo])
async def update_user(
    user_id: int,
    body: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Update a user's role or active status. Admin only."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.role is not None:
        user.role = body.role
    if body.active is not None:
        user.active = body.active
    await db.flush()
    await db.refresh(user)
    return APIResponse(
        success=True,
        data=UserInfo(id=user.id, username=user.username, role=user.role, active=user.active),
    )
