import os
import uuid
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.cos.v5.cos_client import CosClient

# 从环境变量获取腾讯云临时密钥和会话令牌
# CloudBase 云托管会自动注入这些变量，无需手动配置
secret_id = os.environ.get("TENCENTCLOUD_SECRETID")
secret_key = os.environ.get("TENCENTCLOUD_SECRETKEY")
token = os.environ.get("TENCENTCLOUD_SESSIONTOKEN")

# 您的存储桶信息
# BUCKET_NAME 和 REGION 已根据您的环境信息自动填充
BUCKET_NAME = "696f-iosapp01-3gzwkfxgc5fa8d9e-1392987112"
REGION = "ap-shanghai"

# 初始化腾讯云身份凭证
cred = credential.Credential(secret_id, secret_key, token)
http_profile = HttpProfile()
http_profile.endpoint = f'cos.{REGION}.myqcloud.com'
client_profile = ClientProfile(httpProfile=http_profile)

# 初始化 COS 客户端
cos_client = CosClient(conf=client_profile, credential=cred)

def upload_to_cos(file_content: bytes, file_name: str) -> str:
    """
    上传文件到腾讯云对象存储(COS)并返回可公开访问的URL。

    :param file_content: 文件的二进制内容.
    :param file_name: 原始文件名.
    :return: 文件上传后在COS上的公开访问URL.
    """
    
    # 使用 uuid 生成一个全球唯一的文件名，避免因文件名重复而覆盖旧文件
    unique_key = f"uploads/{uuid.uuid4().hex}-{file_name}"
    
    # 执行上传
    cos_client.put_object(
        Bucket=BUCKET_NAME,
        Body=file_content,
        Key=unique_key,
        EnableMD5=False
    )
    
    # 返回文件的公网访问 URL
    # 您的存储桶默认开启了 CDN 加速，使用 .cdn.dnsv1.com 后缀可以获得更好的访问速度
    return f"https://{BUCKET_NAME}.cos.{REGION}.myqcloud.com/{unique_key}"

