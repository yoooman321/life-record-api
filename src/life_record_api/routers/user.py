from fastapi import APIRouter, Depends, Form, Query
from life_record_api.schemas.user import UserRead, UserCreate, UserLogin
from life_record_api.db.session import get_session
from life_record_api.services.users import insert_user, login_user

router = APIRouter(tags=["users"])


@router.post("/register", response_model=UserRead)
def create_user(data: UserCreate, session=Depends(get_session)):
    return insert_user(session, data)


@router.post("/login", response_model=UserRead)
def user_login(data: UserLogin, session=Depends(get_session)):
    return login_user(session, data)
