# AI 菜谱 FastAPI 应用部署与 CloudBase 集成指南

## 一、前言

本文档旨在为您提供一个清晰、详尽的步骤，指导您如何将现有的 **FastAPI AI 菜谱应用**成功部署到**腾讯云 CloudBase**，并集成其核心云服务，最终为您的 **iOS 客户端**提供稳定、可扩展的后端 API 接口。

我们将遵循以下技术路线：

- **计算服务**: 使用 **云托管 (Cloud Run)** 以容器化方式运行您的 FastAPI 应用。
- **数据存储**: 使用 **CloudBase MySQL 数据库**持久化存储菜谱数据。
- **文件存储**: 使用 **云存储 (Cloud Storage)** 存储用户上传的食材图片。
- **客户端交互**: iOS App 通过云托管提供的公网 HTTPS 地址调用 API，不直接与 CloudBase SDK 交互。

### 架构概览

```mermaid
graph TD
    subgraph "用户设备"
        A[iOS 客户端]
    end

    subgraph "腾讯云 CloudBase"
        B[云托管 Cloud Run<br>(运行 FastAPI 应用)]
        C[CloudBase MySQL<br>(存储菜谱数据)]
        D[云存储<br>(存储食材图片)]
    end

    A -- "HTTPS API 请求<br>(上传图片/获取菜谱)" --> B
    B -- "读写菜谱数据" --> C
    B -- "上传/读取图片" --> D

    style A fill:#cce5ff,stroke:#6b95ff
    style B fill:#f6ffed,stroke:#b7eb8f
    style C fill:#fff0f6,stroke:#ff85c0
    style D fill:#fffbe6,stroke:#ffe58f
```

---

## 二、Phase 1: CloudBase 控制台配置

在修改代码之前，我们需要先在 CloudBase 控制台中准备好所需的云资源。

### **步骤 1.1: 开通并配置 MySQL 数据库**

- **为什么这么做**: 您的应用需要一个持久化的数据库来存储生成的菜谱、用户信息（未来扩展）等。CloudBase MySQL 提供了与云托管内网连接的高性能数据库服务。

1.  **访问控制台**: 请点击以下链接，前往您环境的 MySQL 控制台页面。
    > [前往 CloudBase 控制台开通 MySQL](https://tcb.cloud.tencent.com/dev?envId=iosapp01-3gzwkfxgc5fa8d9e#/db/mysql/table/default/)

2.  **开通服务**: 在页面中，点击“开通服务”并按照指引完成。CloudBase 会为您创建一个 MySQL 实例。

3.  **关键信息**: 开通后，CloudBase 会将数据库的**私网连接地址、用户名、密码**等信息以**环境变量**的形式自动注入到您的云托管服务中。这意味着您的代码**无需硬编码**这些敏感信息，更加安全和灵活。

### **步骤 1.2: 创建 `recipes` 数据表**

- **为什么这么做**: 为了规范地存储菜谱数据，我们需要预先定义一个数据表结构。

1.  **进入 SQL 编辑器**: 在 MySQL 管理页面，找到“SQL操作”或类似的在线查询工具。

2.  **执行建表语句**: 复制并执行以下 SQL 语句，以创建一个名为 `recipes` 的数据表。

    ```sql
    CREATE TABLE `recipes` (
      `id` INT AUTO_INCREMENT PRIMARY KEY,
      `_openid` VARCHAR(64) DEFAULT '' NOT NULL, -- **关键字段**：为未来集成用户系统做准备，存储用户唯一标识
      `recipe_name` VARCHAR(255) NOT NULL,
      `ingredients` TEXT,
      `steps` TEXT,
      `image_url` VARCHAR(1024),
      `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ```
    
    > **注释**:
    > - `_openid`: 这是 CloudBase 的标准实践，用于关联数据和用户。即使现在不做登录功能，预留此字段也能方便未来平滑升级。
    - `id`: 每条菜谱的唯一主键。
    - 其他字段用于存储菜谱的核心信息。

### **步骤 1.3: 了解云存储配置**

- **为什么这么做**: 您的应用允许用户上传图片，这些图片文件需要一个安全、可靠的地方进行存储和访问。

1.  **服务状态**: 云存储服务通常在环境创建时**默认开启**。您可以在 CloudBase 控制台左侧导航栏的“存储”菜单中看到它。

2.  **权限说明**:
    - **默认私有读写**: 出于安全考虑，存储桶默认为私有。
    - **服务内部访问**: 您的云托管 FastAPI 服务会被自动授予一个**服务角色 (Service Role)**，该角色拥有访问云存储的权限。因此，您的后端代码可以直接读写云存储，而无需额外配置复杂的访问策略。最终图片可以通过云存储的 CDN 加速域名被 iOS 客户端访问。

---

## 三、Phase 2: 应用程序代码修改

现在，我们来修改您的 FastAPI 项目代码，以集成刚刚配置好的云服务。

### **步骤 2.1: 更新项目依赖**

- **为什么这么做**: 我们需要添加新的 Python 库来帮助应用连接 MySQL 数据库和操作云存储。

1.  **编辑 `requirements.txt`**: 打开此文件，并添加以下三行：

    ```text
    # ... 您原有的依赖 ...
    PyMySQL
    SQLAlchemy
    tencent-cloud-sdk-python
    ```
    > **注释**:
    > - `PyMySQL`: FastAPI (底层为 Starlette) 连接 MySQL 需要的数据库驱动程序。
    - `SQLAlchemy`: 一个强大的 ORM (对象关系映射) 工具，可以让我们用 Python 对象来操作数据库，而不是手写 SQL，更高效且不易出错。
    - `tencent-cloud-sdk-python`: 腾讯云官方 SDK，我们将用它来操作云存储（上传图片）。

### **步骤 2.2: 封装数据库连接**

- **为什么这么做**: 创建一个专门的模块来管理数据库连接和会话，可以使代码结构更清晰，并遵循“关注点分离”的原则。

1.  **创建 `app/database.py` 文件**:

    ```python
    import os
    from sqlalchemy import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker

    # 从环境变量中读取数据库连接信息
    # CloudBase 会自动将这些变量注入到云托管环境中
    DB_HOST = os.environ.get("MYSQL_ADDRESS", "").split(":")[0]
    DB_PORT = os.environ.get("MYSQL_ADDRESS", "").split(":")[1]
    DB_USER = os.environ.get("MYSQL_USERNAME")
    DB_PASS = os.environ.get("MYSQL_PASSWORD")
    DB_NAME = "lxf" # 这是您的数据库名

    # 构建数据库连接 URL
    SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # 创建数据库引擎
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

    # 创建一个数据库会话工厂
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # 创建一个 ORM 模型基类
    Base = declarative_base()

    # 提供一个依赖注入函数，用于在 API 路由中获取数据库会话
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    ```
    > **注释**: 这是集成 SQLAlchemy 的标准模式。我们从环境变量安全地获取凭据，创建连接引擎，并定义一个 `get_db` 函数，FastAPI 将用它来为每个 API 请求提供一个独立的数据库会d话。

2.  **创建数据模型 `app/models.py`** (如果已有请修改):

    ```python
    from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
    from .database import Base

    class Recipe(Base):
        __tablename__ = "recipes"

        id = Column(Integer, primary_key=True, index=True)
        _openid = Column(String(64), nullable=False, default='')
        recipe_name = Column(String(255), nullable=False)
        ingredients = Column(Text)
        steps = Column(Text)
        image_url = Column(String(1024))
        created_at = Column(TIMESTAMP)
    ```
    > **注释**: 这个 `Recipe` 类映射到我们之前创建的 `recipes` 表，使 SQLAlchemy 知道如何操作它。

### **步骤 2.3: 重构图片上传接口**

- **为什么这么做**: 原接口只在内存中处理图片。我们需要修改它，将图片持久化到云存储，并将菜谱信息存入数据库。

1.  **创建云存储服务模块 `app/storage.py`**:

    ```python
    import os
    import uuid
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.cos.v5.cos_client import CosClient

    # 从环境变量获取腾讯云临时密钥和会话令牌
    # CloudBase 云托管会自动注入这些变量
    secret_id = os.environ.get("TENCENTCLOUD_SECRETID")
    secret_key = os.environ.get("TENCENTCLOUD_SECRETKEY")
    token = os.environ.get("TENCENTCLOUD_SESSIONTOKEN")
    
    # 您的存储桶信息
    # 格式为： bucketname-appid, 例如：'iosapp01-3gzwkfxgc5fa8d9e-12567890'
    # AppId 您可以在 https://console.cloud.tencent.com/developer 中找到
    BUCKET_NAME = "iosapp01-3gzwkfxgc5fa8d9e-xxxxxxxxx" # <--- 请替换为您的 Bucket 全名
    REGION = "ap-shanghai" # 请根据您的环境所在地域修改

    cred = credential.Credential(secret_id, secret_key, token)
    http_profile = HttpProfile()
    http_profile.endpoint = f'cos.{REGION}.myqcloud.com'
    client_profile = ClientProfile(httpProfile=http_profile)
    
    cos_client = CosClient(conf=client_profile, credential=cred)

    def upload_to_cos(file_content: bytes, file_name: str) -> str:
        """上传文件到云存储并返回可访问的 URL"""
        
        # 生成一个唯一的文件名，避免冲突
        unique_key = f"uploads/{uuid.uuid4().hex}-{file_name}"
        
        # 执行上传
        cos_client.put_object(
            Bucket=BUCKET_NAME,
            Body=file_content,
            Key=unique_key,
            EnableMD5=False
        )
        
        # 返回文件的公网访问 URL
        return f"https://{BUCKET_NAME}.cos.{REGION}.myqcloud.com/{unique_key}"

    ```
    > **重要提示**: 请务必将 `BUCKET_NAME` 和 `REGION` 替换为您的环境的正确信息。存储桶名称通常是 `环境名称-AppId`，地域可以在环境设置中找到。

2.  **修改 `main.py` (或相关路由文件) 中的 `/api/chat/image` 接口**:

    ```python
    # ... 其他 import ...
    from fastapi import Depends
    from sqlalchemy.orm import Session
    from app import models, database, storage
    from app.services.qwen_client import some_qwen_image_function # 假设这是您调用通义千问的函数

    # ... app = FastAPI() ...

    @app.post("/api/chat/image")
    async def create_recipe_from_image(
        file: UploadFile = File(...),
        db: Session = Depends(database.get_db) # 依赖注入数据库会话
    ):
        # 1. 读取上传的文件内容
        contents = await file.read()

        # 2. 将图片上传到云存储
        # 这个操作会将图片持久化，并返回一个公网可访问的 URL
        image_url = storage.upload_to_cos(contents, file.filename)

        # 3. 调用 AI 模型生成菜谱
        # 注意：您可能需要修改您的 AI 客户端，让它接受一个图片 URL 而不是文件内容
        recipe_data = await some_qwen_image_function(image_url) 
        
        # 4. 创建 Recipe 对象并存入数据库
        new_recipe = models.Recipe(
            recipe_name=recipe_data.get("name"),
            ingredients=recipe_data.get("ingredients"),
            steps=recipe_data.get("steps"),
            image_url=image_url # 保存图片的云存储链接
        )
        db.add(new_recipe)
        db.commit()
        db.refresh(new_recipe)

        return new_recipe
    ```

---

## 四、Phase 3: 部署到云托管

代码修改完成后，最后一步就是将其部署到云端。

### **步骤 3.1: 确认 `Dockerfile`**

- **为什么这么做**: `Dockerfile` 是构建容器镜像的“说明书”。云托管会根据它的指令来打包您的应用。

您的项目已包含 `Dockerfile`。请确保它至少包含以下内容：

```dockerfile
# 使用官方 Python 镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有应用代码
COPY . .

# 暴露端口，确保与 uvicorn 启动端口一致
EXPOSE 8000

# 启动应用的命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
> **注释**: 关键是 `EXPOSE` 和 `CMD` 中的端口号。云托管会捕获这个端口，并将其映射到公网的 80/443 端口。

### **步骤 3.2: 一键部署**

- **为什么这么做**: 使用 CloudBase 提供的工具可以简化部署流程，它会自动处理代码上传、镜像构建和版本发布。

我可以直接使用 `manageCloudRun` 工具来为您完成部署。部署参数大致如下：

- **服务名称**: `ai-recipe-api` (或您指定)
- **代码路径**: `.` (当前项目根目录)
- **Dockerfile 路径**: `Dockerfile`
- **端口**: `8000` (与 Dockerfile 中 EXPOSE 的端口匹配)

部署成功后，**CloudBase 会提供一个公网域名**，例如 `https://ai-recipe-api-xxxx.service.tcloudbase.com`。这个 URL 就是您的 iOS 客户端需要调用的 API 地址。

---

## 五、Phase 4: iOS 客户端集成

- **为什么这么做**: 让您的原生 iOS 应用能与新部署的后端服务通信。

您的 iOS 代码无需任何 CloudBase SDK。它只需要像调用普通 RESTful API 一样，向云托管提供的公网 URL 发送 HTTPS 请求。

**示例 (Swift - `URLSession`)**:

```swift
import Foundation

// 向 /api/chat/image 发送图片
func uploadImage(imageData: Data, to urlString: String) {
    guard let url = URL(string: urlString) else { return }

    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    
    let boundary = "Boundary-\(UUID().uuidString)"
    request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

    var body = Data()
    
    // 添加图片数据
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"file\"; filename=\"recipe_image.jpg\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
    body.append(imageData)
    body.append("\r\n".data(using: .utf8)!)
    
    body.append("--\(boundary)--\r\n".data(using: .utf8)!)
    
    request.httpBody = body

    let task = URLSession.shared.dataTask(with: request) { data, response, error in
        // 处理服务器返回的数据 (JSON)
        if let data = data {
            // ... 解析菜谱 JSON ...
        }
    }
    task.resume()
}

// 使用方法
// let imageUrl = "https://<您的云托管域名>/api/chat/image"
// uploadImage(imageData: yourImageData, to: imageUrl)
```

## 六、总结

通过以上步骤，您的 FastAPI 应用就成功地迁移到了 CloudBase，并具备了数据库和对象存储能力，形成了一个完整的、生产级的后端服务。

**下一步是什么？**
当您准备好后，请告诉我，我将开始执行**Phase 3**的部署操作。
