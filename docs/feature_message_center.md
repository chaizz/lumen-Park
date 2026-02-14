# 消息中心详细设计文档 (Message Center Design)

## 1. 概述
消息中心是 Lumen Park 的核心互动枢纽，负责聚合点赞、评论、关注及系统通知，通过红点提示和列表展示，增强用户的留存与互动频率。

## 2. 数据模型设计 (Database Schema)

我们需要一张 `notifications` 表来存储所有类型的通知。

### 2.1 Notifications Table
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | 主键 |
| `recipient_id` | UUID | **接收者** ID (User 外键) |
| `sender_id` | UUID | **发送者** ID (User 外键，可为空，如系统消息) |
| `type` | Enum | 通知类型: `like`, `comment`, `follow`, `system` |
| `post_id` | UUID | 关联帖子 ID (可为空，如关注通知) |
| `comment_id` | UUID | 关联评论 ID (可为空) |
| `content` | Text | 通知的补充文本 (如评论内容摘要、系统公告) |
| `is_read` | Boolean | 是否已读 (默认 False) |
| `created_at` | DateTime | 创建时间 |

### 2.2 索引策略
*   `recipient_id` + `is_read`: 用于快速查询未读数量。
*   `recipient_id` + `created_at`: 用于列表分页排序。

## 3. 接口设计 (API Design)

### 3.1 获取未读数量
*   **Endpoint**: `GET /api/v1/notifications/unread-count`
*   **Auth**: Required
*   **Response**: `{ "count": 12 }`

### 3.2 获取通知列表
*   **Endpoint**: `GET /api/v1/notifications/`
*   **Query Params**:
    *   `skip`: int
    *   `limit`: int
    *   `type`: string (optional, e.g., 'like')
*   **Response**: `List[NotificationResponse]`
    *   包含发送者头像、用户名、关联帖子缩略图等聚合信息。

### 3.3 标记已读
*   **Endpoint**: `POST /api/v1/notifications/{id}/read`
*   **Description**: 标记单条为已读。

### 3.4 全部已读
*   **Endpoint**: `POST /api/v1/notifications/read-all`
*   **Description**: 将当前用户所有未读消息标记为已读。

## 4. 业务逻辑 (Business Logic)

### 4.1 通知触发机制
采用 **Service 层调用** 或 **Event 钩子** 的方式。在执行业务操作成功后，同步创建通知。

*   **点赞 (Like)**:
    *   当 `User A` 点赞 `User B` 的 `Post P`。
    *   检查 `A != B` (自己点赞自己不发通知)。
    *   检查是否已存在同类型的未读通知 (防止重复刷屏)，如果存在则更新时间，或忽略。
    *   Insert `Notification(recipient=B, sender=A, type='like', post=P)`.
*   **评论 (Comment)**:
    *   当 `User A` 评论 `Post P` (作者 `User B`)。
    *   Insert `Notification(recipient=B, sender=A, type='comment', post=P, content=comment_preview)`.
    *   如果是回复评论，则接收者是原评论的作者。
*   **关注 (Follow)**:
    *   当 `User A` 关注 `User B`.
    *   Insert `Notification(recipient=B, sender=A, type='follow')`.

### 4.2 实时性
*   MVP 阶段：前端轮询 (Polling)，每 30-60 秒请求一次 `unread-count`。
*   进阶阶段：引入 WebSocket 实现实时推送。

## 5. 前端 UI 组件 (Frontend Components)

### 5.1 导航栏入口
*   在 Navbar 右侧添加铃铛图标。
*   使用 `ElBadge` 显示未读红点。

### 5.2 通知列表页 (`/notifications`)
*   **Tabs**: 全部 | 点赞 | 评论 | 关注。
*   **列表项样式**:
    *   左侧：发送者头像 (Avatar)。
    *   中间：
        *   第一行：`User A` 点赞了你的作品 / `User A` 评论了: "..."
        *   第二行：时间 (如 "2小时前")。
    *   右侧：
        *   点赞/评论：帖子缩略图 (点击跳转详情)。
        *   关注：显示“关注”或“回关”按钮。
    *   状态：未读项背景为淡蓝色，已读为白色。

## 6. 开发计划
1.  **Backend**:
    *   创建 `Notification` Model 和 Migration。
    *   实现 CRUD Service。
    *   在 `LikeService`, `CommentService`, `UserService` 中埋点触发通知。
    *   实现 API Router。
2.  **Frontend**:
    *   封装 Notification API。
    *   实现 Navbar 轮询逻辑。
    *   开发 Notification List 页面。
