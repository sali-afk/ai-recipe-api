"""
服务层模块的入口
此文件用于提供服务的单例实例，确保在整个应用中只有一个服务实例，以节省资源。
"""
from typing import Optional
from .qwen_vision_client import QwenVisionClient

_vision_service_instance: Optional[QwenVisionClient] = None


def get_vision_service() -> QwenVisionClient:
    """
    获取QwenVisionClient服务单例
    
    Returns:
        QwenVisionClient: 服务实例
    """
    global _vision_service_instance
    if _vision_service_instance is None:
        # 首次调用时创建实例
        _vision_service_instance = QwenVisionClient()
    return _vision_service_instance


# 使 get_vision_service 可以从 app.services 导入
__all__ = ["get_vision_service"]
