# 需求文档

## 简介

本系统是一个iOS AI菜谱应用，通过集成通义千问视觉模型API和ChefTransformer模型，为用户提供智能菜谱推荐和烹饪指导。系统采用前后端分离架构，后端模型服务部署在阿里云Linux服务器上，前端使用SwiftUI构建类似AI助手的对话界面，全程使用中文交互。

## 术语表

- **AI菜谱应用 (AI Recipe App)**: 本系统的iOS客户端应用程序
- **通义千问视觉模型 (Qwen Vision Model)**: 阿里云提供的多模态AI模型API
- **ChefTransformer模型 (ChefTransformer Model)**: 专门用于菜谱生成和烹饪建议的AI模型
- **后端服务 (Backend Service)**: 部署在阿里云Linux服务器上的模型推理服务，使用FastAPI框架构建
- **FastAPI框架 (FastAPI Framework)**: 用于构建后端RESTful API的现代Python Web框架
- **Docker容器 (Docker Container)**: 用于打包和部署后端服务的容器化环境
- **SwiftUI界面 (SwiftUI Interface)**: iOS应用的用户界面框架
- **模型API (Model API)**: 后端服务暴露的RESTful API接口
- **对话界面 (Chat Interface)**: 类似AI助手的用户交互界面

## 需求

### 需求 1

**用户故事:** 作为用户，我想要通过对话界面与AI助手交互，以便获取菜谱建议和烹饪指导

#### 验收标准

1. WHEN 用户启动应用 THEN AI菜谱应用 SHALL 显示一个对话界面，包含消息列表和输入框
2. WHEN 用户在输入框中输入文本消息并发送 THEN AI菜谱应用 SHALL 将消息显示在对话列表中并发送到后端服务
3. WHEN 后端服务返回响应 THEN AI菜谱应用 SHALL 在对话列表中显示AI助手的回复消息
4. WHEN 显示消息内容 THEN AI菜谱应用 SHALL 使用中文格式化所有文本内容
5. WHEN 用户滚动消息列表 THEN AI菜谱应用 SHALL 保持流畅的滚动体验并正确显示历史消息

### 需求 2

**用户故事:** 作为用户，我想要上传食材或菜品的图片，以便AI识别并提供相关的菜谱建议

#### 验收标准

1. WHEN 用户点击图片上传按钮 THEN AI菜谱应用 SHALL 打开系统相册或相机选择器
2. WHEN 用户选择一张图片 THEN AI菜谱应用 SHALL 将图片上传到后端服务进行识别
3. WHEN 后端服务处理图片 THEN 后端服务 SHALL 调用通义千问视觉模型API识别图片中的食材或菜品
4. WHEN 图片识别完成 THEN 后端服务 SHALL 返回识别结果和相关菜谱建议
5. WHEN 图片上传或识别失败 THEN AI菜谱应用 SHALL 显示友好的错误提示信息

### 需求 3

**用户故事:** 作为用户，我想要获得基于AI生成的详细菜谱，以便学习如何烹饪特定菜品

#### 验收标准

1. WHEN 用户请求特定菜品的菜谱 THEN 后端服务 SHALL 调用ChefTransformer模型生成详细的烹饪步骤
2. WHEN 生成菜谱内容 THEN 后端服务 SHALL 包含食材列表、用量、烹饪步骤和时间估算
3. WHEN 返回菜谱内容 THEN 后端服务 SHALL 使用结构化的中文格式组织信息
4. WHEN AI菜谱应用接收到菜谱 THEN AI菜谱应用 SHALL 以清晰易读的格式展示菜谱内容
5. WHEN 用户查看菜谱 THEN AI菜谱应用 SHALL 支持滚动浏览完整的菜谱信息

### 需求 4

**用户故事:** 作为开发者，我想要将AI模型打包成Docker容器并部署到阿里云服务器，以便提供稳定的后端服务

#### 验收标准

1. WHEN 构建后端服务 THEN 后端服务 SHALL 使用FastAPI框架构建RESTful API，并将通义千问视觉模型API集成和ChefTransformer模型打包在同一个Docker镜像中
2. WHEN Docker容器启动 THEN 后端服务 SHALL 加载所有必需的模型文件和Python依赖项
3. WHEN 部署到阿里云Linux服务器 THEN 后端服务 SHALL 通过FastAPI在指定端口上启动并监听HTTP请求
4. WHEN 接收到API请求 THEN FastAPI框架 SHALL 验证请求格式并路由到相应的模型处理逻辑
5. WHEN 模型推理完成 THEN FastAPI框架 SHALL 返回JSON格式的响应数据

### 需求 5

**用户故事:** 作为开发者，我想要定义清晰的API接口规范，以便前端和后端能够正确通信

#### 验收标准

1. WHEN 前端发送文本查询请求 THEN 模型API SHALL 接受包含用户消息的JSON请求体
2. WHEN 前端上传图片 THEN 模型API SHALL 接受multipart/form-data格式的图片文件
3. WHEN 后端处理请求 THEN 模型API SHALL 返回统一格式的JSON响应，包含状态码和数据字段
4. WHEN API调用失败 THEN 模型API SHALL 返回包含错误代码和中文错误描述的响应
5. WHEN 前端调用API THEN 模型API SHALL 支持HTTPS加密传输以保护数据安全

### 需求 6

**用户故事:** 作为用户，我想要应用能够处理网络异常和错误情况，以便获得稳定的使用体验

#### 验收标准

1. WHEN 网络连接失败 THEN AI菜谱应用 SHALL 显示网络错误提示并允许用户重试
2. WHEN 后端服务响应超时 THEN AI菜谱应用 SHALL 在30秒后显示超时提示
3. WHEN 服务器返回错误状态码 THEN AI菜谱应用 SHALL 解析错误信息并显示给用户
4. WHEN 图片上传失败 THEN AI菜谱应用 SHALL 保留用户输入的文本内容并提示重新上传
5. WHEN 应用处于离线状态 THEN AI菜谱应用 SHALL 显示离线提示并禁用发送功能

### 需求 7

**用户故事:** 作为用户，我想要应用界面美观且符合iOS设计规范，以便获得良好的视觉体验

#### 验收标准

1. WHEN 用户查看界面 THEN SwiftUI界面 SHALL 遵循iOS Human Interface Guidelines设计规范
2. WHEN 显示消息气泡 THEN SwiftUI界面 SHALL 区分用户消息和AI消息的视觉样式
3. WHEN 应用适配不同设备 THEN SwiftUI界面 SHALL 在iPhone和iPad上正确显示和布局
4. WHEN 系统切换深色模式 THEN SwiftUI界面 SHALL 自动适配深色和浅色主题
5. WHEN 用户交互时 THEN SwiftUI界面 SHALL 提供适当的动画和视觉反馈

### 需求 8

**用户故事:** 作为开发者，我想要后端服务具有良好的性能和可扩展性，以便支持多用户并发访问

#### 验收标准

1. WHEN 多个用户同时发送请求 THEN FastAPI框架 SHALL 使用异步处理机制处理并发请求
2. WHEN 模型推理执行 THEN 后端服务 SHALL 在合理时间内返回响应（文本查询5秒内，图片识别15秒内）
3. WHEN 服务器资源不足 THEN FastAPI框架 SHALL 返回服务繁忙状态码并建议用户稍后重试
4. WHEN Docker容器重启 THEN 后端服务 SHALL 自动恢复并重新加载模型
5. WHEN 监控服务状态 THEN FastAPI框架 SHALL 提供健康检查端点返回服务运行状态
