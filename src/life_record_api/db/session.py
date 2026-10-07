from sqlmodel import create_engine, Session

DATABASE_URL = "postgresql+psycopg://postgres:devpassword@localhost:5432/life_record"

engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session
