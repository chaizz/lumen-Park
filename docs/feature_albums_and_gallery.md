# 影集与沉浸式 3D 展厅设计文档 (Albums & Immersive 3D Gallery)

## 1. 概述 (Overview)

本模块旨在为 Lumen Park 提供全方位的作品集展示方案。

* **基础层**：提供标准的影集 (Album) 功能，允许用户将已发布的作品整理成主题合集（如“2023 富士街拍精选”）。
* **高级层**：基于 WebGL 技术构建沉浸式 3D 艺术展厅，让用户能以第一人称视角（FPS）漫游虚拟空间，获得如同亲临线下摄影展的体验。

---

## 2. 影集基础功能 (Album Core Features)

### 2.1 创建与管理 (Creation & Management)

* **创建入口**：
  * 个人主页 -> "影集" Tab -> "新建影集" 按钮。
  * 作品详情页 -> "添加到影集" -> "新建影集"。
* **创建向导 (Wizard)**：
  1. **第一步：选择作品**
     * 从用户已发布的帖子列表中选择（支持搜索/筛选）。
     * 支持多选、批量添加。
  2. **第二步：基本信息**
     * **标题** (Title)：必填，最大长度 50。
     * **描述** (Description)：选填，最大长度 500，支持 Markdown。
     * **封面图** (Cover)：默认使用第一张作品的封面，支持手动上传或从已选作品中指定。
     * **可见性** (Visibility)：公开 (Public) / 私密 (Private)。
     * **排序**：支持拖拽调整作品在影集中的顺序。
  3. **第三步：预览与发布**
     * 预览影集效果。
     * 保存为草稿 (Draft) 或直接发布 (Published)。
* **管理**：
  * 编辑影集信息。
  * 添加/移除作品。
  * 删除影集（不会删除其中的作品）。

### 2.2 展示与访问 (Display & Access)

* **影集详情页 (2D 模式)**：
  * **头部**：全宽封面图、标题、描述、作者信息、创建时间、总作品数。
  * **入口**：显著的 "进入 3D 展厅" 按钮。
  * **列表区**：瀑布流或网格展示影集内的作品。
  * **互动**：收藏影集（Bookmark Album）、分享。
* **短链接 (Short Link)**：
  * 发布时生成 7 位随机字符串 ID（如 `A7x9k2m`）。
  * 访问 URL：`http://localhost:5173/a/{short_id}`。

---

## 3. 沉浸式 3D 展厅 (Immersive 3D Gallery)

### 3.1 展厅结构规范 (Cylindrical Structure)
*   **几何形态**：标准圆柱体结构。
    *   **半径**：8-12 米（根据作品数量动态调整）。
    *   **高度**：6-8 米，营造开阔的空间感。
*   **展示区域**：
    *   圆柱内壁为主要展示面。
    *   沿圆周划分 12-16 个等距展示位（单层）。
    *   支持多层排列（如作品较多时）。
*   **材质环境**：
    *   **地面**：哑光材质（Matte），减少强反射干扰。
    *   **天花板**：设置环形漫射光源，提供均匀的基础照明。
    *   **墙面**：深色或中性色 PBR 材质，突出作品。

### 3.2 影集展示系统 (Exhibition System)
*   **作品分组**：
    *   将影集作品按类别或顺序分组，每组 8-12 张，环绕排列。
*   **专业画框**：
    *   采用专业级 3D 相框模型。
    *   包含玻璃反射效果（Glass Reflection）和纸张纹理。
*   **布局规范**：
    *   作品间距保持 1.5-2 米视觉距离（弧长）。
    *   默认悬挂高度：中心点离地 1.6 米。
*   **信息标签**：
    *   每幅作品下方或侧边添加 3D 信息标签。
    *   内容：标题、作者、创作年份。

### 3.3 交互控制系统 (Interaction System)
*   **视角控制**：
    *   **默认视角**：圆柱中心点，离地 1.6 米高度（第一人称视点）。
    *   **自由度限制**：
        *   **水平旋转 (Y轴)**：360° 无限制。
        *   **俯仰角 (X轴)**：±30° 限制，模拟人眼自然舒适区。
        *   **位移**：限制在中心圆盘区域，防止穿模或过分远离画作。
*   **输入方式**：
    *   **鼠标**：拖拽旋转视角，点击选中。
    *   **触摸**：单指滑动旋转，双指缩放（视野）。
    *   **键盘**：左右方向键旋转，上下键前后微调或切换作品。
*   **辅助功能**：
    *   **视角回正**：一键重置到水平视线。
    *   **自动旋转**：无人操作时缓慢自转展示（屏保模式）。

### 3.4 视觉渲染要求 (Visual & Rendering)
*   **PBR 材质系统**：全面使用 Physically Based Rendering 材质。
*   **光照方案**：
    *   **环境光**：低强度，填充暗部。
    *   **聚光灯 (Spotlights)**：6 个可调聚光灯组，重点照亮当前视野内的画作。
    *   **天顶光**：环形面光源。
*   **特殊效果**：
    *   作品表面添加防眩光涂层效果（Roughness map）。
    *   视角过渡动画：0.5 秒平滑插值（GSAP）。

### 3.5 性能优化标准 (Performance)
*   **模型面数**：场景总面数控制在 5 万面以内。
*   **纹理规范**：统一为 1024x1024（2K 可选），使用 WebP/KTX2 压缩。
*   **LOD (Level of Detail)**：
    *   远距离/快速旋转时使用低模/低贴图。
    *   静止/聚焦时加载高精贴图。
*   **目标帧率**：主流设备确保 60 FPS 流畅运行。

---

## 4. 数据模型设计 (Database Schema)

### 4.1 Albums 表

| 字段名          | 类型        | 描述                                   |
| :-------------- | :---------- | :------------------------------------- |
| `id`          | UUID        | 主键                                   |
| `short_id`    | String(8)   | 唯一短标识符，索引，用于 URL           |
| `user_id`     | UUID        | 创建者 ID (FK -> users.id)             |
| `title`       | String(100) | 标题                                   |
| `description` | Text        | 描述                                   |
| `cover_url`   | String      | 封面图片 URL                           |
| `status`      | Enum        | `draft` (草稿), `published` (发布) |
| `is_public`   | Boolean     | 是否公开                               |
| `created_at`  | DateTime    | 创建时间                               |
| `updated_at`  | DateTime    | 更新时间                               |

### 4.2 AlbumPosts 表 (关联表)

| 字段名       | 类型     | 描述                         |
| :----------- | :------- | :--------------------------- |
| `album_id` | UUID     | FK -> albums.id              |
| `post_id`  | UUID     | FK -> posts.id               |
| `order`    | Integer  | 排序权重 (0, 1, 2...)        |
| `added_at` | DateTime | 添加时间                     |
| **PK** |          | (album_id, post_id) 联合主键 |

### 4.3 GalleryConfig 表 (3D 配置)

| 字段名             | 类型   | 描述                                   |
| :----------------- | :----- | :------------------------------------- |
| `id`             | UUID   | 主键                                   |
| `album_id`       | UUID   | FK -> albums.id (One-to-One)           |
| `theme`          | String | 主题模板 (modern, classic, minimalist) |
| `wall_color`     | String | 墙面颜色 Hex                           |
| `floor_material` | String | 地面材质 ID                            |
| `frame_style`    | String | 默认画框样式                           |
| `bgm_id`         | String | 背景音乐 ID                            |
| `layout_data`    | JSON   | 自定义布局数据 (预留)                  |

---

## 5. API 接口设计 (API Design)

### 5.1 影集管理

* `POST /api/v1/albums/` - 创建影集 (支持同时传入 `post_ids`)。
* `PUT /api/v1/albums/{id}` - 更新影集信息 (标题、描述、封面、可见性)。
* `DELETE /api/v1/albums/{id}` - 删除影集。
* `GET /api/v1/albums/my` - 获取当前用户的影集列表（包含草稿）。

### 5.2 影集内容

* `POST /api/v1/albums/{id}/posts` - 向影集添加作品（批量）。
* `DELETE /api/v1/albums/{id}/posts` - 从影集移除作品。
* `PUT /api/v1/albums/{id}/reorder` - 更新作品顺序。

### 5.3 3D 配置

* `GET /api/v1/albums/{id}/gallery-config` - 获取 3D 展厅配置。
* `PUT /api/v1/albums/{id}/gallery-config` - 更新配置。

### 5.4 公开访问

* `GET /api/v1/albums/{short_id}` - 获取影集详情（含作品列表）。
  * 权限逻辑：如果是私密影集，仅作者可访问；如果是公开，所有人可访问。
* `GET /api/v1/users/{user_id}/albums` - 获取某用户的公开影集列表。

---

## 6. 技术架构 (Technical Architecture)

### 6.1 技术选型

* **后端**：FastAPI + SQLAlchemy (Async)。
* **前端 (2D)**：Vue 3 + Element Plus + Pinia。
* **前端 (3D)**：
  * **渲染引擎**：**Three.js** (基石)。
  * **框架集成**：**TresJS** (推荐) - 以 Vue 组件方式编写 3D 场景。
  * **物理引擎**：Cannon-es (碰撞检测)。
  * **动画库**：GSAP (相机运镜)。

### 6.2 性能优化策略 (3D)

* **LOD (Level of Detail)**：
  * 远处的画框使用低分辨率纹理。
  * 近处（点击查看时）动态加载 4K 高清纹理。
* **纹理压缩**：使用 KTX2 / WebP 格式压缩贴图。
* **几何体实例化 (InstancedMesh)**：画框、射灯模型复用，减少 Draw Call。
* **资源预加载**：进入展厅前显示进度条，预加载核心模型和前 5 张图片。

---

## 7. 前端组件设计 (Frontend Components)

### 7.1 目录结构

```
src/
├── views/
│   ├── AlbumList.vue         # 影集列表
│   ├── AlbumDetail.vue       # 2D 详情页
│   └── AlbumCreate.vue       # 创建向导
└── components/
    ├── album/
    │   ├── AlbumCard.vue     # 影集卡片
    │   └── PostSelector.vue  # 作品选择器
    └── 3d/
        ├── GalleryScene.vue      # 3D 场景入口 (Canvas)
        ├── VirtualCamera.vue     # 相机控制器
        ├── ExhibitionRoom.vue    # 展厅几何体
        ├── ArtFrame.vue          # 画框组件
        └── UI/
            ├── LoadingScreen.vue # 3D 加载页
            └── DetailPanel.vue   # 作品详情弹窗
```

---

## 8. 开发计划

1. **Phase 1: 影集基础 (Backend & Frontend)**
   * 创建 `Album`, `AlbumPost` 模型。
   * 实现影集 CRUD 接口。
   * 开发创建向导和 2D 详情页。
2. **Phase 2: 3D 核心 (Frontend)**
   * 搭建 TresJS 基础场景。
   * 实现动态画廊生成算法（根据作品数量）。
   * 实现漫游控制 (WASD)。
3. **Phase 3: 3D 交互与优化**
   * 实现画框点击交互与详情弹窗。
   * 添加光照、材质和阴影。
   * 性能优化 (LOD, 纹理压缩)。
