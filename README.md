# Lumen Park

**Lumen Park** 是一个专注于分享“胶片配方”和技术细节的摄影社交平台。它主要面向摄影师，特别是富士（Fujifilm）相机用户，旨在让用户不仅能分享最终的照片，还能分享用于创作该照片的机内设置（即“配方”），从而实现风格的复刻与交流。

## 🌟 功能特点

*   **首页瀑布流**: 沉浸式浏览体验，支持无限滚动，清晰展示作品的热度（浏览量/点赞量）。
*   **作品详情**:
    *   **富士配方可视化**: 直观展示胶片模拟、动态范围、白平衡偏移等详细参数。
    *   **EXIF 信息**: 自动解析并展示相机型号、镜头、光圈、快门、ISO 等元数据。
    *   **互动**: 点赞、收藏、关注作者。
    *   **评论系统**: 支持无限层级回复，构建良好的社区交流氛围。
*   **个人中心**:
    *   展示个人资料及统计数据（关注/粉丝/获赞）。
    *   管理我的作品、我喜欢的、我收藏的内容。
    *   支持编辑个人资料（头像、昵称、简介）。
*   **图片上传**: 支持多图上传，自动提取 EXIF 信息。

## 🛠 技术栈

### 后端 (Backend)
*   **框架**: FastAPI (Python 3.12+)
*   **数据库**: MySQL 8.0 (异步驱动 asyncmy)
*   **ORM**: SQLAlchemy 2.0 (Async)
*   **验证**: Pydantic v2
*   **缓存**: Redis
*   **对象存储**: MinIO
*   **包管理**: uv

### 前端 (Frontend)
*   **框架**: Vue 3 (Composition API)
*   **构建工具**: Vite
*   **UI 库**: Element Plus
*   **样式**: TailwindCSS
*   **状态管理**: Pinia
*   **路由**: Vue Router

### 部署 (Deployment)
*   **容器化**: Docker & Docker Compose

## 📂 项目结构

```
Lumen-Park/
├── backend/                # Python FastAPI 后端
│   ├── src/
│   │   ├── apps/           # 业务模块 (users, posts, interactions)
│   │   ├── core/           # 核心配置
│   │   ├── database/       # 数据库连接
│   │   └── ...
│   ├── alembic/            # 数据库迁移脚本
│   └── ...
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/            # 接口请求
│   │   ├── components/     # 公共组件
│   │   ├── views/          # 页面组件
│   │   ├── stores/         # Pinia 状态
│   │   └── ...
├── deploy/                 # Docker 部署配置
└── docs/                   # 详细设计文档
```

## 📚 详细文档

*   [产品设计总览 (PRODUCT_DESIGN.md)](docs/PRODUCT_DESIGN.md)
*   [技术架构设计 (ARCHITECTURE.md)](docs/ARCHITECTURE.md)
*   [首页设计 (HOME_PAGE_DESIGN.md)](docs/HOME_PAGE_DESIGN.md)
*   [详情页设计 (POST_DETAIL_DESIGN.md)](docs/POST_DETAIL_DESIGN.md)
*   [个人中心设计 (PERSONAL_CENTER_DESIGN.md)](docs/PERSONAL_CENTER_DESIGN.md)
*   [投稿页设计 (SUBMISSION_PAGE_DESIGN.md)](docs/SUBMISSION_PAGE_DESIGN.md)

## 🚀 快速开始 (本地开发)

### 前置条件
- Docker & Docker Compose
- Python 3.12+ (推荐使用 `uv`)
- Node.js 20+ (推荐使用 `pnpm`)

### 1. 启动基础设施
```bash
cd deploy
docker-compose up -d
```
这将启动 MySQL, Redis, MinIO 服务。

### 2. 后端启动
```bash
cd backend
# 安装依赖
uv sync
# 运行数据库迁移
uv run alembic upgrade head
# 启动服务
uv run python -m src.run
```
后端服务地址: `http://localhost:8000`
API 文档: `http://localhost:8000/docs`

### 3. 前端启动
```bash
cd frontend
# 安装依赖
pnpm install
# 启动开发服务器
pnpm dev
```
前端访问地址: `http://localhost:5173`

## 📄 License
MIT License. See [LICENSE](LICENSE) for details.
