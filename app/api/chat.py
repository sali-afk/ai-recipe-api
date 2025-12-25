"""
聊天API路由 V4 - 最终清理版
"""
import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import Dict, Any
import logging
from sqlalchemy.orm import Session

from app.models import schemas as api_schemas
from app.models import recipe as db_models
from app.core import database, storage
from app.services import get_vision_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"]
)


@router.post("/image", response_model=api_schemas.RecipeCreationResponse)
async def image_upload(
    file: UploadFile = File(..., description="上传的图片文件"),
    db: Session = Depends(database.get_db)
):
    """
    图片上传端点 (V4 - 统一模型)
    接收图片, 调用AI生成菜谱, 存入数据库并返回。
    """
    logger.info(f"收到图片上传请求 (V4): {file.filename}")

    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="不支持的图片格式，请上传JPG、PNG等图片格式")

    # 步骤1: 读取图片并上传到云存储
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="图片数据为空")
        image_url = storage.upload_to_cos(image_bytes, file.filename)
        logger.info(f"图片成功上传到云存储: {image_url}")
    except Exception as e:
        logger.error(f"图片上传至云存储失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="图片上传失败")

    # 步骤2: 调用AI服务从图片直接生成菜谱
    try:
        vision_service = get_vision_service()
        recipe_obj = await vision_service.generate_recipe_from_image(image_bytes)
        logger.info(f"AI成功生成菜谱对象: {recipe_obj.dish_name}")
    except Exception as e:
        logger.error(f"AI服务调用失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI服务处理失败: {str(e)}")

    # 步骤3: 将菜谱存入数据库
    try:
        # BUG修复：正确地将Pydantic对象列表转换为JSON字符串
        ingredients_json = json.dumps([i.model_dump() for i in recipe_obj.ingredients], ensure_ascii=False)
        steps_json = json.dumps([s.model_dump() for s in recipe_obj.steps], ensure_ascii=False)

        new_recipe_db = db_models.Recipe(
            recipe_name=recipe_obj.dish_name,
            ingredients=ingredients_json,
            steps=steps_json,
            image_url=image_url,
            cooking_time=recipe_obj.cooking_time,
            difficulty=recipe_obj.difficulty,
            _openid=""  # 暂时留空
        )
        
        db.add(new_recipe_db)
        db.commit()
        db.refresh(new_recipe_db)
        logger.info(f"菜谱 '{new_recipe_db.recipe_name}' 已成功存入数据库, ID为: {new_recipe_db.id}")
    except Exception as e:
        logger.error(f"数据库存储失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="服务器内部错误，无法保存菜谱")

    # 步骤4: 返回成功响应
    return api_schemas.RecipeCreationResponse(
        success=True,
        data=new_recipe_db,
        message="菜谱已根据您的图片生成并成功保存！"
    )


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """
    健康检查端点
    """
    logger.info("收到健康检查请求 (V4)")
    all_ok = True
    components = {}

    try:
        get_vision_service()
        components["qwen_vision_service"] = "healthy"
    except Exception as e:
        components["qwen_vision_service"] = f"unhealthy: {str(e)}"
        all_ok = False
    
    # 数据库连接检查（确保会话正确关闭）
    try:
        from sqlalchemy import text as sql_text

        SessionLocal = database.get_session_local()
        db = SessionLocal()
        try:
            db.execute(sql_text("SELECT 1"))
        finally:
            db.close()

        components["database"] = "healthy"
    except Exception as e:
        components["database"] = f"unhealthy: {str(e)}"
        all_ok = False


    return {
        "success": all_ok,
        "data": {
            "service": "running",
            "components": components
        },
        "message": "服务运行正常" if all_ok else "服务存在问题，请检查组件状态"
    }


