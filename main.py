"""
AI菜谱应用后端服务 V2 - 清理版
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import time

from app.api import chat

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用实例
app = FastAPI(
    title="AI菜谱应用API",
    description="基于通义千问多模态模型的智能菜谱服务",
    version="2.0.0"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置为您的iOS App域名或IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 中间件：记录请求处理时间
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Request: {request.method} {request.url.path} - Completed in {process_time:.4f}s")
    return response


# 注册API路由
app.include_router(chat.router)


# 根路径，提供一个简单的欢迎信息
@app.get("/")
async def root():
    return {
        "message": "Welcome to the AI Chef API! Visit /docs for documentation."
    }

# 全局异常处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"请求验证错误: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "VALIDATION_ERROR",
            "message": "请求参数无效",
            "detail": exc.errors()
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"服务器内部错误: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "INTERNAL_SERVER_ERROR",
            "message": "服务器发生未知错误。"
        },
    )


# 应用启动事件：初始化数据库
@app.on_event("startup")
async def startup_event():
    logger.info("AI菜谱应用后端服务启动中...")
    try:
        from app.core import database as db_core
        from app.models.recipe import Base

        if db_core.is_db_configured():
            logger.info("正在初始化数据库，检查并创建数据表...")
            engine = db_core.get_engine()
            Base.metadata.create_all(bind=engine)
            logger.info("数据库表结构初始化完成。")
        else:
            logger.warning("未检测到 MySQL 配置，跳过数据库初始化（请在云托管绑定 MySQL，并设置 DB_NAME 或 MYSQL_DATABASE）。")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}", exc_info=True)
        # 生产环境中，如果数据库是关键依赖，您可能希望在此处引发异常以停止启动
    logger.info("应用启动完成")



# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("AI菜谱应用后端服务已关闭。")


# 本地开发时运行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

