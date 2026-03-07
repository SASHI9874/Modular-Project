from sqlalchemy.orm import Session
from app.entities.user_entity import User
from app.core.security import get_password_hash
from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str

class UserRepository:
    def get_by_email(self, db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, user_in: UserCreate):
        db_user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

user_repo = UserRepository()