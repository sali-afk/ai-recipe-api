from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, text
from app.core.database import Base

class Recipe(Base):
    # 定义了数据表在数据库中的名字
    __tablename__ = "recipes"

    # 定义各个字段及其属性
    id = Column(Integer, primary_key=True, index=True)
    _openid = Column(String(64), nullable=False, default='')
    recipe_name = Column(String(255), nullable=False)
    ingredients = Column(Text)
    steps = Column(Text)
    image_url = Column(String(1024))
    cooking_time = Column(Integer, nullable=False, default=0)
    difficulty = Column(String(32), nullable=False, default='简单')
    # `server_default=text('CURRENT_TIMESTAMP')` 让数据库在创建记录时自动设置时间
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
