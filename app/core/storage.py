import os
import uuid
from typing import Optional

from qcloud_cos import CosConfig, CosS3Client

# 存储桶信息（当前环境 iosapp01 已知）
BUCKET_NAME = "696f-iosapp01-3gzwkfxgc5fa8d9e-1392987112"
REGION = "ap-shanghai"

_cos_client: Optional[CosS3Client] = None


def _get_cos_client() -> CosS3Client:
    """懒加载 COS 客户端，避免在环境变量未注入时应用启动直接崩溃。"""
    global _cos_client
    if _cos_client is not None:
        return _cos_client

    secret_id = os.getenv("TENCENTCLOUD_SECRETID") or ""
    secret_key = os.getenv("TENCENTCLOUD_SECRETKEY") or ""
    token = os.getenv("TENCENTCLOUD_SESSIONTOKEN") or ""

    if not (secret_id and secret_key and token):
        raise RuntimeError("COS 凭证未注入：请确认云托管运行环境已获得临时密钥（TENCENTCLOUD_* 环境变量）")

    config = CosConfig(Region=REGION, SecretId=secret_id, SecretKey=secret_key, Token=token)
    _cos_client = CosS3Client(config)
    return _cos_client


def upload_to_cos(file_content: bytes, file_name: str) -> str:
    """上传文件到 COS，并返回可访问的 URL。"""
    if not file_content:
        raise ValueError("文件内容为空")

    unique_key = f"uploads/{uuid.uuid4().hex}-{file_name}"

    client = _get_cos_client()
    client.put_object(
        Bucket=BUCKET_NAME,
        Body=file_content,
        Key=unique_key,
    )

    return f"https://{BUCKET_NAME}.cos.{REGION}.myqcloud.com/{unique_key}"


