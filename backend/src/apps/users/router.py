from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from src.apps.users import service
from src.apps.users import schemas
from src.apps.users import models
from src.core import security
from src.core import deps

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse)
async def register(
    user_in: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    user = await service.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    user = await service.get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )

    user = await service.create_user(db, user=user_in)
    return user

@router.post("/login/access-token", response_model=schemas.Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = await service.get_user_by_username(db, username=form_data.username)
    # Important: verify_password inside security.py now expects plain_password to be sha256 hashed before bcrypt verification
    # But wait, the user input form_data.password is PLAIN.
    # The security.verify_password function I just modified handles the hashing internally.
    # So we just pass form_data.password directly.
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = security.create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    return current_user

@router.put("/me", response_model=schemas.UserResponse)
async def update_user_me(
    user_in: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    # Check if username exists if it's being updated
    if user_in.username and user_in.username != current_user.username:
        user = await service.get_user_by_username(db, username=user_in.username)
        if user:
            raise HTTPException(
                status_code=400,
                detail="The user with this username already exists in the system.",
            )
            
    # Check if email exists if it's being updated
    if user_in.email and user_in.email != current_user.email:
        user = await service.get_user_by_email(db, email=user_in.email)
        if user:
            raise HTTPException(
                status_code=400,
                detail="The user with this email already exists in the system.",
            )
            
    user = await service.update_user(db, db_user=current_user, user_in=user_in)
    return user

@router.get("/{user_id}", response_model=schemas.UserResponse)
async def read_user_by_id(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    user = await service.get_user(db, user_id=user_id)
    if user == None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
