import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 从环境变量中读取数据库连接信息
# CloudBase 会自动将这些变量注入到云托管环境中
DB_HOST = os.environ.get("MYSQL_ADDRESS", "").split(":")[0] if ":" in os.environ.get("MYSQL_ADDRESS", "") else os.environ.get("MYSQL_ADDRESS", "")
DB_PORT = os.environ.get("MYSQL_ADDRESS", "").split(":")[1] if ":" in os.environ.get("MYSQL_ADDRESS", "") else "3306"
DB_USER = os.environ.get("MYSQL_USERNAME")
DB_PASS = os.environ.get("MYSQL_PASSWORD")
DB_NAME = os.environ.get("MYSQL_DATABASE") or os.environ.get("DB_NAME") or "lxf"  # 默认lxf；建议在云托管里显式配置DB_NAME或MYSQL_DATABASE

# 构建数据库连接 URL
# f-string 用于动态构建字符串
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 创建数据库引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 创建一个数据库会话工厂 (Session Factory)
# autocommit=False 和 autoflush=False 是 SQLAlchemy 的标准实践，可以更好地控制事务
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建一个 ORM 模型基类，我们之后创建的所有模型类都需要继承这个 Base
Base = declarative_base()

# 提供一个依赖注入函数，用于在 API 路由中获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
