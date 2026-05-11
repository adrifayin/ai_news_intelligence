from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uuid

from backend.database import get_db, User, UserInterest

router = APIRouter(prefix="/api/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    username: str
    password: str
    region: Optional[str] = None
    interests: List[str] = []

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    region: Optional[str] = None
    interests: List[str] = []

@router.post("/register", response_model=UserResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # Simple clear-text password for this demo (ideally use passlib/bcrypt)
    existing_user = db.query(User).filter(User.username == req.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = User(
        username=req.username,
        password_hash=req.password,  # Storing as is for simplicity in this demo
        region=req.region
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Add interests
    for interest in req.interests:
        ui = UserInterest(user_id=new_user.id, category=interest)
        db.add(ui)
    
    db.commit()
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        region=new_user.region,
        interests=req.interests
    )

@router.post("/login", response_model=UserResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or user.password_hash != req.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    interests = [ui.category for ui in user.interests]
    
    return UserResponse(
        id=user.id,
        username=user.username,
        region=user.region,
        interests=interests
    )
