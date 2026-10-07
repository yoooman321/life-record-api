from sqlmodel import SQLModel
from life_record_api.db.session import engine
from life_record_api import models  # noqa: F401

SQLModel.metadata.create_all(engine)
