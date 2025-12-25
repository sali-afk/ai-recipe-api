"""
数据模型定义
使用Pydantic进行数据验证和序列化
需求: 5.1, 5.2, 5.3
"""
from typing import Optional, List, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID, uuid4


# ============================================================================
# 请求模型 (Request Models)
# ============================================================================

class TextQueryRequest(BaseModel):
    """
    文本查询请求模型
    需求: 5.1 - 接受包含用户消息的JSON请求体
    """
    message: str = Field(..., min_length=1, max_length=1000, description="用户输入的文本消息")
    conversation_id: Optional[str] = Field(None, description="会话ID，用于关联对话历史")
    
    @validator('message')
    def message_not_empty(cls, v):
        """验证消息不能为空或只包含空白字符"""
        if not v or not v.strip():
            raise ValueError('消息内容不能为空')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "推荐一道川菜",
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class ImageUploadRequest(BaseModel):
    """
    图片上传请求模型
    需求: 5.2 - 接受multipart/form-data格式的图片文件
    注意: 实际的图片文件通过FastAPI的UploadFile处理，此模型用于元数据
    """
    conversation_id: Optional[str] = Field(None, description="会话ID")
    description: Optional[str] = Field(None, max_length=500, description="图片描述或用户备注")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "description": "这是我冰箱里的食材"
            }
        }


# ============================================================================
# 响应数据模型 (Response Data Models)
# ============================================================================

class Ingredient(BaseModel):
    """
    食材模型
    需求: 3.2 - 包含食材列表、用量
    """
    name: str = Field(..., description="食材名称")
    amount: str = Field(..., description="用量")
    unit: str = Field(..., description="单位")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "猪肉",
                "amount": "300",
                "unit": "克"
            }
        }


class CookingStep(BaseModel):
    """
    烹饪步骤模型
    需求: 3.2 - 包含烹饪步骤
    """
    step_number: int = Field(..., ge=1, description="步骤序号")
    description: str = Field(..., description="步骤描述")
    duration: Optional[int] = Field(None, ge=0, description="步骤耗时（分钟）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "step_number": 1,
                "description": "将猪肉切成薄片，加入料酒和淀粉腌制10分钟",
                "duration": 10
            }
        }


class Recipe(BaseModel):
    """
    菜谱模型
    需求: 3.1, 3.2 - 生成详细的烹饪步骤，包含食材列表、用量、烹饪步骤和时间估算
    """
    dish_name: str = Field(..., description="菜品名称")
    ingredients: List[Ingredient] = Field(..., description="食材列表")
    steps: List[CookingStep] = Field(..., description="烹饪步骤列表")
    cooking_time: int = Field(..., ge=0, description="总烹饪时间（分钟）")
    difficulty: str = Field(..., description="难度等级：简单、中等、困难")
    
    @validator('difficulty')
    def validate_difficulty(cls, v):
        """验证难度等级"""
        valid_difficulties = ['简单', '中等', '困难']
        if v not in valid_difficulties:
            raise ValueError(f'难度等级必须是以下之一: {", ".join(valid_difficulties)}')
        return v
    
    @validator('steps')
    def validate_steps_order(cls, v):
        """验证步骤序号连续性"""
        if not v:
            raise ValueError('烹饪步骤不能为空')
        for i, step in enumerate(v, start=1):
            if step.step_number != i:
                raise ValueError(f'步骤序号不连续，期望 {i}，实际 {step.step_number}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "dish_name": "鱼香肉丝",
                "ingredients": [
                    {"name": "猪肉", "amount": "300", "unit": "克"},
                    {"name": "木耳", "amount": "50", "unit": "克"},
                    {"name": "胡萝卜", "amount": "1", "unit": "根"}
                ],
                "steps": [
                    {
                        "step_number": 1,
                        "description": "将猪肉切成细丝，加入料酒和淀粉腌制",
                        "duration": 10
                    },
                    {
                        "step_number": 2,
                        "description": "热锅凉油，炒香葱姜蒜",
                        "duration": 2
                    }
                ],
                "cooking_time": 30,
                "difficulty": "中等"
            }
        }


class VisionResult(BaseModel):
    """
    图片识别结果模型
    需求: 2.3, 2.4 - 识别图片中的食材或菜品
    """
    recognized_items: List[str] = Field(..., description="识别到的食材或菜品列表")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="识别置信度")
    description: Optional[str] = Field(None, description="图片整体描述")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recognized_items": ["番茄", "鸡蛋", "葱"],
                "confidence": 0.95,
                "description": "图片中包含新鲜的番茄、鸡蛋和葱"
            }
        }


class HealthStatus(BaseModel):
    """
    健康检查状态模型
    需求: 8.5 - 提供健康检查端点返回服务运行状态
    """
    status: str = Field(..., description="服务状态：healthy, unhealthy, degraded")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    models_loaded: bool = Field(..., description="模型是否已加载")
    version: str = Field(..., description="API版本")
    details: Optional[Dict[str, Any]] = Field(None, description="详细状态信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00",
                "models_loaded": True,
                "version": "1.0.0",
                "details": {
                    "chef_transformer": "loaded",
                    "qwen_api": "connected"
                }
            }
        }


# ============================================================================
# 通用响应模型 (Generic Response Model)
# ============================================================================

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """
    统一的API响应格式
    需求: 5.3 - 返回统一格式的JSON响应，包含状态码和数据字段
    需求: 5.4 - 返回包含错误代码和中文错误描述的响应
    """
    success: bool = Field(..., description="请求是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    error: Optional[str] = Field(None, description="错误代码")
    message: str = Field(..., description="响应消息（中文）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"dish_name": "鱼香肉丝"},
                "error": None,
                "message": "菜谱生成成功"
            }
        }


# ============================================================================
# 具体响应类型别名 (Response Type Aliases)
# ============================================================================

class RecipeResponse(APIResponse[Recipe]):
    """菜谱响应"""
    pass


class VisionResponse(APIResponse[VisionResult]):
    """图片识别响应"""
    pass


class HealthResponse(APIResponse[HealthStatus]):
    """健康检查响应"""
    pass


class TextResponse(APIResponse[Dict[str, Any]]):
    """文本响应"""
    pass


# ============================================================================
# 新增：数据库交互模型 (Database-Interfacing Models)
# ============================================================================

class RecipeDBBase(BaseModel):
    """用于数据库记录的基础模型"""
    recipe_name: str
    # 将复杂的对象/列表序列化为JSON字符串后存入数据库是一种常见的模式
    ingredients: Optional[str] = None
    steps: Optional[str] = None
    image_url: Optional[str] = None
    cooking_time: Optional[int] = None
    difficulty: Optional[str] = None

class RecipeCreate(RecipeDBBase):
    """用于在数据库中创建新菜谱的模型"""
    pass

class RecipeSchema(RecipeDBBase):
    """用于代表从数据库中检索到的菜谱记录的模型"""
    id: int
    _openid: str
    created_at: datetime

    class Config:
        from_attributes = True # Pydantic V2+ a.k.a. orm_mode

# 用于成功创建菜谱后的特定响应模型，继承自通用的APIResponse
class RecipeCreationResponse(APIResponse[RecipeSchema]):
    """成功创建菜谱后的响应模型"""
    pass
