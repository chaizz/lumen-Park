# Lumen Park - 技术架构文档

## 1. 系统概览
本系统采用现代化的 **FastAPI** 后端和 **Vue 3** 前端构建，并使用 Docker Compose 进行统一部署。

## 2. 目录结构

### 2.1 根目录
```text
Lumen-Park/
├── backend/            # Python FastAPI 项目
├── frontend/           # Vue 3 项目
├── deploy/             # Docker Compose 及基础设施配置
├── docs/               # 项目文档
├── AGENTS.md           # 角色定义
└── README.md           # 项目入口说明
```

### 2.2 后端 (`backend/`)
由 `uv` 管理。
```text
backend/
├── src/
│   ├── apps/           # 业务领域模块
│   │   ├── users/      # 认证、个人资料
│   │   ├── posts/      # 图片、配方管理
│   │   ├── interactions/ # 点赞、评论
│   │   ├── notifications/ # 消息中心
│   │   └── upload/     # 文件上传服务
│   ├── core/           # 框架核心扩展
│   │   ├── config.py   # 配置管理 (Pydantic)
│   │   ├── security.py # JWT, 哈希加密
│   │   └── exceptions.py
│   ├── database/       # 数据访问层
│   │   ├── session.py  # 异步引擎
│   │   └── base.py     # 声明式基类
│   ├── common/         # 通用枚举、常量
│   ├── utils/          # 工具库 (S3, EXIF)
│   ├── main.py         # FastAPI 应用工厂
│   └── run.py          # 启动脚本
├── tests/              # Pytest 测试套件
├── alembic/            # 数据库迁移
├── pyproject.toml      # 依赖管理 (uv)
├── alembic.ini
```

### 2.3 前端 (`frontend/`)
由 `pnpm` 管理。
```text
frontend/
├── src/
│   ├── assets/
│   ├── components/     # 可复用 UI 组件
│   ├── views/          # 页面级组件
│   ├── stores/         # Pinia 状态管理
│   ├── router/         # Vue Router 路由
│   ├── api/            # Axios 封装与接口
│   ├── types/          # TypeScript 类型定义
│   └── App.vue
├── public/
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
└── package.json
```

## 3. 数据库设计 (ERD)

### Users (用户表)
- `id`: UUID (主键)
- `username`: String (唯一)
- `email`: String (唯一)
- `hashed_password`: String
- `avatar`: String (URL)

### Posts (帖子表)
- `id`: 自增主键 (主键)
- `user_id`: UUID (外键)
- `image_path`: String (MinIO 路径)
- `title`: String
- `description`: Text
- `created_at`: Datetime

### ExifData (EXIF 数据表)
- `post_id`: UUID (主键, 外键)
- `camera_make`: String (相机厂商)
- `camera_model`: String (相机型号)
- `lens`: String (镜头)
- `iso`: Integer
- `aperture`: Float (光圈)
- `shutter_speed`: String (快门速度)
- `focal_length`: Float (焦距)

### FujiRecipes (富士配方表)
- `post_id`: UUID (主键, 外键)
- `simulation`: Enum (胶片模拟类型)
- `dynamic_range`: Enum (动态范围)
- `wb`: String (白平衡)
- `wb_shift_r`: Integer (白平衡偏移 R)
- `wb_shift_b`: Integer (白平衡偏移 B)
- `color`: Integer (色彩)
- `sharpness`: Integer (锐度)
- `highlights`: Integer (高光)
- `shadows`: Integer (阴影)
- `grain`: String (颗粒)
- `color_chrome`: String (色彩效果)

### Interactions (互动)
- `comments`: 用户与帖子的评论关联表。
- `likes`: 用户与帖子的点赞关联表。
- `bookmarks`: 用户与帖子的收藏关联表（新增）。

### Notifications (消息中心)
- `id`: UUID (主键)
- `recipient_id`: UUID (接收者, FK -> Users)
- `sender_id`: UUID (发送者, FK -> Users, 可空)
- `type`: Enum (like, comment, follow, system)
- `entity_id`: UUID (关联实体ID, 如 post_id, comment_id)
- `entity_type`: String (post, comment, user)
- `is_read`: Boolean (默认 False)
- `content`: Text (系统通知内容或评论摘要)
- `created_at`: Datetime

### 3.4 前端 (Frontend)
*   **框架**：Vue 3 + Vite
*   **状态管理**：Pinia
*   **UI 组件库**：Element Plus + Tailwind CSS
*   **交互逻辑**：
    *   使用 `vue-use` 实现无限滚动 (`useInfiniteScroll`)。
    *   组件懒加载与路由守卫。
*   **API 交互**：Axios 封装，支持请求拦截与错误处理。

## 4. 数据流设计 (Data Flow)
### 4.1 用户认证流程
1.  用户提交登录表单 (username, password)。
2.  后端验证密码，生成 JWT Token。
3.  前端存储 Token 至 LocalStorage 和 Pinia Store。
4.  后续请求携带 `Authorization: Bearer <token>`。

### 4.2 首页加载流程
1.  **初始化**：
    *   前端 `Home.vue` 发起 `GET /api/v1/posts/?skip=0&limit=20`。
    *   后端查询数据库，返回前 20 条帖子数据（包含 `views_count`, `likes_count`）。
2.  **滚动刷新**：
    *   当用户滚动至底部，触发 `loadMore`。
    *   前端计算新的 `skip` 值（当前列表长度）。
    *   发起请求获取下一页数据，并追加至 `posts` 列表。
    *   若返回数据为空，标记 `noMore`。

### 4.3 帖子详情浏览流程
1.  **进入详情页**：
    *   前端 `PostDetail.vue` 发起 `GET /api/v1/posts/{id}`。
2.  **后端处理**：
    *   查询数据库获取帖子详情。
    *   **浏览量统计**：自动将 `views_count` + 1（原子操作）。
    *   返回包含最新 `views_count` 的帖子数据。
3.  **前端展示**：
    *   更新 UI 上的浏览量和点赞量。
    *   并发请求获取点赞状态 (`/interactions/likes/status`) 和评论列表 (`/interactions/comments`)。

## 5. 技术栈
- **语言**: Python 3.12+, TypeScript 5+
- **框架**: FastAPI, Vue 3
- **数据库**: MySQL 8.0 (异步驱动: aiomysql/asyncmy)
- **ORM**: SQLAlchemy 2.0 (Async)
- **缓存**: Redis 7
- **存储**: MinIO (兼容 S3 协议)
- **工具**: UV, Ruff, Pytest, PNPM, Vite, TailwindCSS
