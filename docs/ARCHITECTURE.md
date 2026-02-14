# Lumen Park - 技术架构文档

## 1. 架构概览
Lumen Park 采用现代化的前后端分离架构，注重性能、可维护性和开发效率。
- **后端**: FastAPI (Python) 提供高性能的 RESTful API。
- **前端**: Vue 3 + Vite 提供响应式、组件化的用户界面。
- **数据**: MySQL (业务数据) + Redis (缓存/会话) + MinIO (对象存储)。
- **AI**: 本地部署的 Transformers 模型进行内容识别。

## 2. 后端架构 (Backend)

### 2.1 技术栈
- **Framework**: FastAPI (基于 Starlette 和 Pydantic)
- **Database ORM**: SQLAlchemy 2.0 (AsyncIO)
- **Migration**: Alembic
- **Validation**: Pydantic v2
- **Task Queue**: BackgroundTasks (轻量级) / Celery (规划中)
- **AI Inference**: PyTorch + Transformers (Hugging Face)

### 2.2 目录结构 (`backend/src`)
```
src/
├── apps/               # 业务模块
│   ├── ai/             # AI 服务 (CLIP 模型加载与推理)
│   ├── auth/           # 认证 (JWT, Login)
│   ├── interactions/   # 互动 (Like, Comment, Follow)
│   ├── notifications/  # 通知系统
│   ├── posts/          # 作品管理
│   ├── tags/           # 标签管理
│   ├── upload/         # 文件上传
│   └── users/          # 用户管理
├── common/             # 公共常量、枚举 (如 TAG_CATEGORIES)
├── core/               # 核心配置
│   ├── config.py       # 环境变量加载
│   ├── deps.py         # 依赖注入 (DB Session, Current User)
│   ├── security.py     # 密码哈希, Token 生成
│   └── model/          # 本地 AI 模型文件存储
├── database/           # 数据库连接
└── utils/              # 工具函数 (EXIF 解析等)
```

### 2.3 核心设计模式
- **依赖注入 (Dependency Injection)**: 广泛用于数据库会话获取 (`get_db`) 和当前用户验证 (`get_current_user`)。
- **Repository/Service Pattern**: Controller (Router) -> Service (业务逻辑) -> Model (数据访问)，保持代码解耦。
- **异步编程 (Asynchronous)**: 全链路 `async/await`，最大化 I/O 密集型任务的并发能力。

### 2.4 数据模型关系 (ER Diagram 简述)
- `User` 1:N `Post`
- `User` 1:N `Comment`
- `User` N:N `User` (Follows)
- `Post` 1:N `PostImage`
- `Post` N:N `Tag` (通过 `post_tags` 关联表)
- `Post` 1:N `Like`
- `Post` 1:N `Comment`

## 3. 前端架构 (Frontend)

### 3.1 技术栈
- **Framework**: Vue 3 (Composition API)
- **Build Tool**: Vite
- **State Management**: Pinia
- **Router**: Vue Router 4
- **UI Library**: Element Plus + TailwindCSS
- **HTTP Client**: Axios

### 3.2 目录结构 (`frontend/src`)
```
src/
├── api/            # API 接口封装
├── assets/         # 静态资源
├── components/     # 通用组件 (NavBar, UserList, etc.)
├── router/         # 路由配置
├── stores/         # Pinia 状态管理 (Auth, etc.)
├── views/          # 页面级组件 (Home, Profile, Submit, etc.)
└── App.vue
```

### 3.3 关键实现
- **响应式布局**: 结合 TailwindCSS 的 Utility Classes 和 Element Plus 的 Grid 系统。
- **组件通信**: 使用 `props` 和 `emit` 进行父子通信，使用 Pinia 进行跨组件状态共享（如用户信息）。
- **动态路由**: 基于用户登录状态的路由守卫 (`beforeEach`)。

## 4. 基础设施与部署

### 4.1 容器化
项目使用 Docker Compose 进行编排，包含以下服务：
- `backend`: Python 应用容器。
- `frontend`: Nginx 容器（生产环境）或 Node 开发服务器。
- `db`: MySQL 8.0。
- `redis`: Redis 7.0。
- `minio`: S3 兼容的对象存储。

### 4.2 AI 模型部署策略
- **本地加载**: 为了节省 API 成本并保护隐私，CLIP 模型直接下载到 `backend/src/core/model` 目录。
- **初始化**: 应用启动时检查模型文件，如果不存在则自动从 Hugging Face 下载。
- **单例模式**: `ImageTagger` 类为单例，避免重复加载模型占用内存。

## 5. 接口规范
遵循 RESTful API 设计原则：
- `GET /resource`: 获取列表
- `GET /resource/{id}`: 获取详情
- `POST /resource`: 创建
- `PUT /resource/{id}`: 全量更新
- `PATCH /resource/{id}`: 部分更新
- `DELETE /resource/{id}`: 删除

统一响应结构：
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```
*(注：目前直接返回数据或 Pydantic 模型，未来可考虑封装统一 Response)*
