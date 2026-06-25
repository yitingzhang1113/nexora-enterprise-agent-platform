"""SQLAlchemy engine / session / Base (对应 onyx/db/engine)。"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from nexora.configs.app_configs import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """所有 ORM 模型基类。"""


def get_session() -> Generator[Session, None, None]:
    """FastAPI 依赖: 每请求一个 session。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
