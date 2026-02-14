# AI Agent 开发指南 (AGENTS.md)

本文档是 **Lumen Park** 项目的 AI 助手（即您）的专用指南。请在进行开发任务时参考以下规范、约定和架构细节。

## 1. 项目概况

**Lumen Park** 是一个全栈摄影社交平台，核心在于分享“富士胶片配方”。

- **后端**: FastAPI + SQLAlchemy (Async) + Pydantic v2 + MySQL + Redis + MinIO。
- **前端**: Vue 3 + Vite + TailwindCSS + Element Plus + Pinia。
- **部署**: Docker Compose。

## 2. 编码规范 (Coding Standards)

### 2.1 后端 (Python)

- **类型提示**: 必须对所有函数参数和返回值进行 Type Hinting。
  ```python
  async def get_user(user_id: str) -> User | None: ...
  ```
- **异步优先**: 数据库操作、I/O 操作必须使用 `async/await`。
- **风格**: 遵循 `ruff` 的默认配置。
- **模型**: 使用 Pydantic v2 进行数据验证（Schema），SQLAlchemy 2.0 进行 ORM 映射（Model）。
- **导入顺序**: 标准库 -> 第三方库 -> 本地模块 (`from src.xxx import ...`)。
- **外键**: 映射到数据库中（使用 `ForeignKey`），并正确配置 `relationship`（使用 `selectinload` 进行预加载）。
- 一定要遵循事务。

### 2.2 前端 (Vue/TS)

- **Composition API**: 必须使用 `<script setup lang="ts">` 风格。
- **样式**: 优先使用 TailwindCSS 类名，仅在必要时使用 `<style scoped>`。
- **组件**: 使用 Element Plus 组件库，保持 UI 风格统一。
- **状态**: 全局状态使用 Pinia，组件局部状态使用 `ref`/`reactive`。
- **图标**: 使用 `@element-plus/icons-vue` 或 SVG。

## 3. 项目结构导航

### 后端 (`backend/src`)

- `apps/`: 业务逻辑入口。每个模块（如 `users`, `posts`, `interactions`）应包含 `router.py`, `service.py`, `models.py`, `schemas.py`。
- `core/`: 全局配置、安全认证、异常处理。
- `database/`: 数据库连接 (`session.py`) 和基类 (`base.py`)。
- `common/`: 跨模块共享的枚举、常量。

### 前端 (`frontend/src`)

- `api/`: 封装 Axios 请求，与后端接口一一对应。
- `stores/`: Pinia Store 定义。
- `views/`: 页面级组件。
- `components/`: 通用/原子级组件。
- `router/`: 路由配置。

## 4. 开发工作流 (Workflow)

1. **数据库变更**:
   - 修改/创建 SQLAlchemy Model。
   - 运行 `cd backend && uv run alembic revision --autogenerate -m "message"`。
   - 运行 `uv run alembic upgrade head` 应用变更。
2. **新增 API**:
   - 定义 Pydantic Schema (Request/Response)。
   - 在 `apps/{module}/router.py` 实现端点。
   - 在 `main.py` 注册路由。
3. **前端对接**:
   - 在 `api/` 下定义请求函数。
   - 在组件中调用，处理 loading 和 error 状态。

## 5. 核心业务逻辑备忘

- **配方数据**: 富士配方包含大量字段（如 `wb_shift_r`, `dynamic_range`），在处理时需注意字段的完整性和类型转换。
- **EXIF 解析**: 上传图片时，后端应尝试自动提取 EXIF。
- **互动逻辑**:
  - **点赞/收藏**: 均为原子操作，需同时更新关联表和主表计数。
  - **评论**: 支持无限层级（树形结构），删除权限仅限作品作者和评论发布者。
- **权限**: 区分 `Guest` (只读), `Photographer` (读写), `Admin` (管理)。

## 6. 自我检查清单 (Self-Check)

- [ ] 新增的 Python 包是否添加到了 `pyproject.toml`？
- [ ] 每个功能开发完毕是否都更新了设计文档？
- [ ] 数据库模型修改是否生成了迁移文件？
- [ ] 所有的 API 是否都有对应的 Pydantic Schema？
- [ ] 前端组件是否适配了移动端（Tailwind 响应式类）？
- [ ] 所有的单测，都不需要我确认删除，都保留, 测试都放在 tests 目录中。
- [ ] 每个功能完成都需要执行单测来验证。

## 7. 其他规范

使用中文回答问题。
