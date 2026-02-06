import os

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool


_engine = None
_SessionLocal = None

def _is_sqlite_url(url: str) -> bool:
    return url.startswith("sqlite://")

def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./local.db")

def create_new_engine(db_url: str | None = None, *, echo: bool = False) -> Engine:
    url = db_url or get_database_url()
    if _is_sqlite_url(url):
        return create_engine(
            url,
            echo=echo,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )
    else:
        return create_engine(
            url,
            echo=echo,
            future=True,
            pool_pre_ping=True,
        )

def init_engine(db_url: str | None = None, *, echo: bool = False) -> Engine:
    global _engine, _SessionLocal
    if _engine is not None:
        return _engine

    _engine = create_new_engine(db_url, echo=echo)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True, expire_on_commit=False)
    return _engine

def get_engine() -> Engine:
    global _engine
    if _engine is None:
        init_engine()
    assert _engine is not None
    return _engine
