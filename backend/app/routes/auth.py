from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserSchema, Token, GoogleAuth, MagicLogin
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.utils.auth_deps import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/magic-login", response_model=Token)
async def magic_login(
    auth_in: MagicLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    # Check if user exists by email
    result = await db.execute(select(User).where(User.email == auth_in.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please sign up."
        )
        
    if auth_in.full_name and not user.full_name:
        # Optionally update full name if provided and it was empty
        user.full_name = auth_in.full_name
        await db.commit()
        await db.refresh(user)
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    
    # Set cookie for UI
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=False,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        path="/"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/magic-register", response_model=Token)
async def magic_register(
    auth_in: MagicLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    import secrets
    import re
    import random
    
    # Check if user exists by email
    result = await db.execute(select(User).where(User.email == auth_in.email))
    user = result.scalar_one_or_none()
    
    if user:
        raise HTTPException(
            status_code=400,
            detail="User already exists. Please log in."
        )
        
    base_username = auth_in.email.split("@")[0]
    clean_username = re.sub(r'[^a-zA-Z0-9]', '', base_username).lower()
    if not clean_username:
        clean_username = "user"
        
    # Ensure username uniqueness
    username = clean_username
    suffix = ""
    while True:
        candidate = username + suffix
        existing = await db.execute(select(User).where(User.username == candidate))
        if not existing.scalar_one_or_none():
            username = candidate
            break
        suffix = str(random.randint(1, 9999))
    
    # Generate 12-char random password
    random_pass = secrets.token_urlsafe(9)
    
    user = User(
        email=auth_in.email,
        username=username,
        hashed_password=get_password_hash(random_pass),
        raw_password=random_pass, # Storing just for admin viewing as requested
        full_name=auth_in.full_name,
        is_active=True,
        is_superuser=False,
        auth_provider="email",
        is_verified=True, # Auto-verify for frictionless onboarding
        verification_token=secrets.token_urlsafe(32)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    
    # Set cookie for UI
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=False,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        path="/"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserSchema)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists by email
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )
    
    # Check if user exists by username
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
    
    import secrets
    # Create user
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password) if user_in.password else None,
        full_name=user_in.full_name,
        is_active=True,
        is_superuser=False,
        auth_provider="email",
        verification_token=secrets.token_urlsafe(32)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/token", response_model=Token)
async def login(
    response: Response,
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # Check email OR username
    from sqlalchemy import or_
    result = await db.execute(select(User).where(or_(User.email == form_data.username, User.username == form_data.username)))
    user = result.scalar_one_or_none()
    
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    
    # Set cookie for UI
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=False, # Allow frontend to read for immediate sync if needed, or use httpOnly for security
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        path="/"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/google", response_model=Token)
async def google_login(
    auth_in: GoogleAuth,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    # Verify google token (logic would go here in production)
    # For MVP, we trust the frontend ID token if we were to implement full verification
    
    result = await db.execute(select(User).where(User.email == auth_in.email))
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        import secrets
        username = auth_in.email.split("@")[0] + "_" + secrets.token_hex(2)
        user = User(
            email=auth_in.email,
            username=username,
            full_name=auth_in.name,
            google_id=auth_in.google_id,
            auth_provider="google",
            is_active=True,
            is_verified=True # Social accounts are pre-verified
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update existing user if they link google or just login
        if not user.google_id:
            user.google_id = auth_in.google_id
            user.auth_provider = "google"
            await db.commit()
            await db.refresh(user)

    access_token = create_access_token(subject=user.email)
    
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=False,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        path="/"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserSchema)
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Successfully logged out"}
