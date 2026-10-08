import bcrypt
import jwt
from sqlmodel import Session, select
from life_record_api.models.user import Users
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from life_record_api.schemas.user import UserCreate, UserLogin, UserRead
from life_record_api.exceptions import AppException
from life_record_api.config import settings
from datetime import datetime, timedelta, timezone
from life_record_api.services.accounting.category import create_default_categories

security = HTTPBearer()
ACCESS_TOKEN_EXPIRE_DAYS = 30


# - bcrypt.hashpw 要吃 bytes,不是 str,所以密碼要先 .encode();算出來的結果也是 bytes,要 .decode() 成字串才能存進 hashed_password: str 這個欄位
# - bcrypt.gensalt() 就是上面講的「隨機鹽」,每次呼叫都會產生不同的值,所以就算兩次傳一模一樣的密碼進去,_hash_password 兩次算出來的結果也會不一樣——這是正常的,不是 bug,之後驗證密碼不是比對雜湊字串相不相等,是用
# bcrypt.checkpw(密碼, 雜湊值) 這個專用函式去比對(這個函式會自動從雜湊值裡還原出鹽、用同樣方式重算一次再比較),等寫 login 的時候會用到
def _hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode()


def _validate_email_not_registered(session: Session, email: str) -> None:
    existing = session.exec(select(Users).where(email == Users.email)).first()
    if existing is not None:
        raise AppException(
            status_code=409, error_code="E03001", detail="這個 email 已經註冊過了"
        )


def _create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def _validate_access_token(token: str) -> dict:
    # decode 後會是： {sub: 當初的 user_id, exp: 剩餘時間}
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AppException(
            status_code=401, error_code="E03003", detail="登入已過期,請重新登入"
        )
    except jwt.InvalidTokenError:
        raise AppException(
            status_code=401, error_code="E03004", detail="無效的登入憑證"
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    token = credentials.credentials  # Bearer 後面那串 token
    payload = _validate_access_token(token)

    return int(payload["sub"])


def insert_user(session: Session, data: UserCreate) -> UserRead:
    _validate_email_not_registered(session, data.email)

    user = Users(
        name=data.name,
        email=data.email,
        hashed_password=_hash_password(data.password),
        birthday=data.birthday if data.birthday is not None else None,
    )

    session.add(user)
    session.flush()

    create_default_categories(session, user.id)

    session.commit()
    session.refresh(user)

    return UserRead(access_token=_create_access_token(user.id))


def login_user(session: Session, data: UserLogin) -> UserRead:
    user = session.exec(select(Users).where(Users.email == data.email)).first()

    if user is None or not bcrypt.checkpw(
        data.password.encode(), user.hashed_password.encode()
    ):
        raise AppException(
            status_code=401, error_code="E03002", detail="email 或密碼錯誤"
        )

    return UserRead(access_token=_create_access_token(user.id))
