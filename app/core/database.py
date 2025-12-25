import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

_engine = None
_SessionLocal = None


def _read_mysql_env() -> tuple[str, str, str, str, str]:
    mysql_address = os.getenv("MYSQL_ADDRESS", "")
    if ":" in mysql_address:
        host, port = mysql_address.split(":", 1)
    else:
        host, port = mysql_address, "3306"

    user = os.getenv("MYSQL_USERNAME") or ""
    password = os.getenv("MYSQL_PASSWORD") or ""
    db_name = os.getenv("MYSQL_DATABASE") or os.getenv("DB_NAME") or ""
    return host, port, user, password, db_name


def is_db_configured() -> bool:
    host, port, user, password, db_name = _read_mysql_env()
    return bool(host and port and user and password and db_name)


def get_engine():
    """懒加载创建 Engine，避免在未绑定 MySQL 时应用启动直接崩溃。"""
    global _engine, _SessionLocal
    if _engine is not None and _SessionLocal is not None:
        return _engine

    host, port, user, password, db_name = _read_mysql_env()
    if not (host and user and password and db_name):
        raise RuntimeError("MySQL 未配置：请在云托管绑定 MySQL，并设置 DB_NAME 或 MYSQL_DATABASE")

    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    _engine = create_engine(url, pool_pre_ping=True)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        get_engine()
    return _SessionLocal


def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

