# 消息推送方案选型与设计 (Message Push Strategy)

## 1. 方案对比 (Comparison)

在不使用轮询 (Polling) 的前提下，实时推送主要有以下三种主流方案：

### 方案 A：WebSocket (全双工)
*   **原理**：建立持久化的 TCP 连接，服务器和客户端可以随时互相发送数据。
*   **✅ 优势**：
    *   **实时性极高**：毫秒级延迟。
    *   **双向通信**：客户端也可以给服务器发消息（适合聊天室、在线游戏）。
    *   **成熟**：库支持广泛（如 Socket.IO, FastAPI WebSockets）。
*   **❌ 劣势**：
    *   **连接开销**：每个在线用户都需要维持一个长连接，对服务器资源（内存/文件句柄）有一定压力。
    *   **复杂性**：需要处理心跳检测、断线重连、鉴权握手等逻辑。
    *   **防火墙**：某些企业网络可能会拦截非标准 HTTP 端口或协议。

### 方案 B：SSE (Server-Sent Events, 单向流)
*   **原理**：基于 HTTP 长连接，服务器向客户端单向推送文本流 (`text/event-stream`)。
*   **✅ 优势**：
    *   **轻量级**：基于标准 HTTP，无需额外协议升级，防火墙友好。
    *   **断线重连**：浏览器原生支持自动重连 (EventSource API)。
    *   **简单**：后端实现比 WebSocket 简单得多，适合“通知”这种单向场景。
*   **❌ 劣势**：
    *   **单向**：客户端不能通过这个连接发消息（需另开 HTTP 请求）。
    *   **连接限制**：HTTP/1.1 下浏览器对同一域名的并发连接数有限制（通常 6 个），HTTP/2 可以解决此问题。

### 方案 C：HTTP/2 Server Push (或 Long Polling)
*   **长轮询 (Long Polling)**：客户端发请求 -> 服务器挂起直到有数据 -> 返回 -> 客户端立即再请求。
    *   **劣势**：仍然有 header 开销，不算真正的“推送”，实时性略逊。
*   **HTTP/2 Push**：主要用于推送静态资源，不适合应用层数据推送。

---

## 2. 选型决策 (Decision)

**推荐方案：SSE (Server-Sent Events)**

**理由**：
1.  **场景匹配**：Lumen Park 的消息中心主要是“服务器通知用户（有人点赞/评论）”，这是典型的**单向推送**场景，不需要双向通信（不需要像聊天室那样高频交互）。
2.  **开发成本**：FastAPI 对 SSE 支持极好（`StreamingResponse`），前端使用 `EventSource` 也非常简单。
3.  **资源友好**：相比 WebSocket，SSE 在处理大量空闲连接时通常更轻量，且协议开销更小。
4.  **兼容性**：现代浏览器均支持，配合 HTTP/2 性能优异。

---

## 3. SSE 详细设计方案

### 3.1 架构设计
*   **连接管理**：后端维护一个全局的 `ConnectionManager`，记录每个在线用户的 SSE 连接（Queue 或 Stream）。
*   **消息分发**：
    1.  业务层（如 `LikeService`）触发事件。
    2.  调用 `NotificationService.create_notification` 写入数据库。
    3.  **同步** 调用 `ConnectionManager.send_to_user(user_id, data)`。
    4.  如果用户在线，通过 SSE 连接推送 JSON 数据；如果不在线，忽略推送（用户下次上线拉取列表即可）。
*   **Redis Pub/Sub (可选/进阶)**：如果后端是多实例部署，必须引入 Redis Pub/Sub 来跨进程广播消息。但目前单实例部署，可以直接使用内存 Queue。

### 3.2 接口设计

#### 3.2.1 SSE 连接端点
*   **Endpoint**: `GET /api/v1/notifications/stream`
*   **Auth**: Query Param `?token=...` (EventSource 不支持自定义 Header，需通过 URL 传 Token)
*   **Response Header**: `Content-Type: text/event-stream`
*   **Event Types**:
    *   `message`: 通用通知（包含红点计数、新消息摘要）。
    *   `ping`: 心跳保活。

#### 3.2.2 消息格式 (Payload)
```json
// Event: "notification"
{
  "type": "like", // or 'comment', 'follow', 'system'
  "unread_count": 5, // 当前总未读数，方便前端直接更新红点
  "data": {
    "id": "uuid...",
    "sender": { "username": "alice", "avatar": "..." },
    "content": "点赞了你的作品"
  }
}
```

### 3.3 后端实现逻辑 (FastAPI)

```python
# 伪代码
class ConnectionManager:
    def __init__(self):
        # user_id -> List[Queue] (支持多端登录)
        self.active_connections: Dict[str, List[asyncio.Queue]] = {}

    async def connect(self, user_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(queue)
        return queue

    def disconnect(self, user_id: str, queue: asyncio.Queue):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(queue)

    async def send_personal_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for queue in self.active_connections[user_id]:
                await queue.put(message)

manager = ConnectionManager()

@router.get("/stream")
async def stream_notifications(token: str):
    user = await get_current_user(token)
    queue = await manager.connect(user.id)
    
    async def event_generator():
        try:
            while True:
                # 等待新消息，设置超时用于发送心跳
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            manager.disconnect(user.id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 3.4 前端实现逻辑 (Vue)

```javascript
// store/notification.ts
let eventSource: EventSource | null = null;

function connectSSE() {
  const token = authStore.token;
  if (!token) return;

  eventSource = new EventSource(`/api/v1/notifications/stream?token=${token}`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // 更新未读数
    notificationStore.unreadCount = data.unread_count;
    // 弹出 Toast 提示 (可选)
    ElNotification({
      title: '新消息',
      message: `${data.sender.username} ${data.content}`,
      type: 'info'
    });
  };

  eventSource.onerror = () => {
    eventSource?.close();
    // 简单的重连逻辑交给浏览器，或者手动延迟重连
  };
}
```

## 4. 开发计划调整

1.  **Phase 1 (Database & API)**:
    *   建立 `Notification` 模型。
    *   实现 CRUD Service。
    *   **新增**: 实现 `ConnectionManager` (单机版内存队列)。
2.  **Phase 2 (Integration)**:
    *   在 `Like/Comment/Follow` 业务逻辑中，插入 `manager.send_personal_message` 调用。
    *   实现 SSE 路由端点。
3.  **Phase 3 (Frontend)**:
    *   前端集成 `EventSource`。
    *   全局 Store 管理连接状态。
