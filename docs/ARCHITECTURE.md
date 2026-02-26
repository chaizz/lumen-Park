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

## 6. 核心功能技术实现

### 6.1 3D 展厅技术设计 (3D Gallery)
- **前端 3D 引擎**: TresJS (Vue 3 + Three.js 封装)。
- **核心依赖**: `three`, `@tresjs/core`, `@tresjs/cientos`, `@tresjs/post-processing`.
- **渲染管线**: WebGL Renderer, PBR 材质系统, Shadow Mapping, Post-processing.
- **性能优化**:
    - **LOD (Level of Detail)**: 根据距离调整模型和纹理质量。
    - **纹理优化**: 使用 WebP/KTX2 格式，动态分辨率。
    - **资源管理**: 懒加载非关键资源，及时 Dispose 清理内存。
    - **设备适配**: 根据设备性能（Mobile/Desktop）自动调整渲染参数（抗锯齿、阴影质量）。

### 6.2 SSE 消息推送 (Server-Sent Events)
- **选型**: 采用 SSE 而非 WebSocket，因其轻量级、HTTP 兼容性好，适合单向通知场景。
- **后端实现**:
    - **ConnectionManager**: 维护 `user_id -> List[asyncio.Queue]` 映射。
    - **消息分发**: 业务层触发 -> 写入 DB -> 同步调用 Manager 推送 -> SSE Endpoint (`/stream`) 读取 Queue 并 Yield 数据。
    - **数据格式**: `text/event-stream`，Event 类型包括 `message` (通知), `ping` (心跳)。
- **前端实现**: 使用 `EventSource` API 连接 `/api/v1/notifications/stream`，监听 `onmessage` 更新 Store。

### 6.3 AI 标签识别实现 (AI Tagging)
- **模型**: `openai/clip-vit-base-patch32` (Zero-shot Classification).
- **库**: `transformers`, `torch`, `pillow`.
- **流程**:
    - `ImageTagger` 单例服务加载模型。
    - 预设候选标签列表（光线、地点、主题）。
    - 图片上传后，异步计算图片与标签的相似度，返回 Top-K。
- **API**: `POST /upload/image` 返回 `{ url: "...", suggested_tags: ["sunny", "sea"] }`.

### 6.4 消息中心实现 (Message Center)
- **数据库设计 (`notifications` 表)**:
    - `id`, `recipient_id` (FK), `sender_id` (FK), `type` (Enum: like, comment, follow, system), `post_id` (FK), `comment_id`, `content`, `is_read`, `created_at`.
    - 索引: `(recipient_id, is_read)`, `(recipient_id, created_at)`.
- **接口**:
    - `GET /unread-count`: 获取未读数。
    - `GET /`: 获取列表（分页）。
    - `POST /{id}/read`: 标记已读。
    - `POST /read-all`: 全部已读。

### 6.5 场景与分类实现 (Scenes & Categories)
- **数据结构**:
    - **`tags` 表**: `id`, `name`, `type` (Enum: lighting, subject, location, other), `count`.
    - **`post_tags` 表**: `post_id`, `tag_id` (M:N 关联).
- **API 变更**:
    - `POST /posts/`: 接收 `tags` 列表。
    - `GET /posts/`: 支持 `tags` 查询参数（多选）。
    - `GET /tags/`: 获取按类型分组的热门标签。
- **预设数据**: 后端初始化脚本预置常用标签及其 Type。

### 6.6 社交列表实现 (Social Lists)
- **接口**:
    - `GET /users/{id}/following`: 获取关注列表。
    - `GET /users/{id}/followers`: 获取粉丝列表。
- **数据增强**: 返回的 User 对象需包含 `is_following` 字段（针对当前登录用户），以便前端显示正确的按钮状态（关注/已关注/互相关注）。
