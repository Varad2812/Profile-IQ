from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.database import get_db, User
from models.schemas import UserCreate, UserLogin, Token, UserOut, GenericResponse
from utils.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=GenericResponse[UserOut], status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "Email already registered", "error_code": 400}
        )
    user = User(
        email=payload.email,
        password=hash_password(payload.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"success": True, "data": user}


@router.post("/login", response_model=GenericResponse[Token])
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=401,
            detail={"success": False, "message": "Invalid credentials", "error_code": 401}
        )
    token = create_access_token({"sub": str(user.id)})
    return {
        "success": True, 
        "data": {"access_token": token, "token_type": "bearer", "user": user}
    }
