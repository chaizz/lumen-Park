# 基于 AI 图像识别的智能标签推荐方案

## 1. 核心理念 (Core Concept)

为了进一步降低用户在投稿时的输入成本并提高标签的准确性，我们将引入 **AI 图像识别** 能力。当用户上传图片后，系统自动分析图片内容，识别出场景（Scene）、物体（Object）和光线（Lighting）特征，并**预选中**或**推荐**相应的标签。

## 2. 技术选型 (Tech Stack)

考虑到项目目前的技术栈（Python/FastAPI）和部署成本，推荐以下两种路径：

### 方案 A：本地轻量级模型 (推荐)
使用 `CLIP` (OpenAI) 或 `MobileNet` 等预训练模型。
*   **优点**：零 API 成本，数据隐私好，响应快。
*   **实现**：使用 `transformers` 库加载 `clip-vit-base-patch32`，将图片和预设的标签文本（"sunny", "indoor", "portrait"）进行匹配，取置信度最高的 Top-K。
*   **适用**：Lumen Park 这种已有明确分类维度的场景（Zero-shot Classification）。

### 方案 B：在线大模型 API
调用 GPT-4o-mini 或 Google Gemini Flash 等视觉 API。
*   **优点**：识别能力极强，能理解复杂语境（如“胶片感”、“忧郁氛围”）。
*   **缺点**：有 API 成本，受网络影响。

**决策**：考虑到我们只需要识别“阴天”、“咖啡厅”等基础特征，**CLIP (Zero-shot)** 是性价比最高的选择。它不需要训练，直接能把图片和我们现有的标签库匹配起来。

## 3. 业务流程 (Workflow)

1.  **上传阶段**：
    *   用户在前端选择图片 -> 上传到后端。
    *   后端保存图片的同时，触发**异步任务**（使用 `BackgroundTasks`）。
2.  **识别阶段 (Backend)**：
    *   后端加载 CLIP 模型（单例模式，避免重复加载）。
    *   输入：用户图片 + 我们的预设标签库（光线/地点/主题列表）。
    *   输出：计算图片与每个标签的相似度分数。
    *   筛选：选取分数超过阈值（如 0.2）且排名前 5 的标签。
3.  **反馈阶段 (Frontend)**：
    *   上传接口返回响应时，带上 `suggested_tags` 字段。
    *   前端界面上，将这些标签**自动高亮选中**，或者在推荐区带有“✨ AI 推荐”的特殊标记。
    *   用户可以保留这些推荐，也可以手动取消或补充。

## 4. 后端实现细节 (Implementation Details)

### 4.1 新增依赖
```bash
uv add transformers torch pillow
```

### 4.2 AI Service (`src/apps/ai/service.py`)
创建一个单例的 AI 服务类：
```python
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

class ImageTagger:
    def __init__(self):
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.candidate_labels = [
            "sunny", "overcast", "indoor", "night", # Lighting
            "street", "cafe", "sea", "park", # Location
            "portrait", "cat", "dog", "food" # Subject
        ]
        # Mapping to Chinese tags
        self.label_map = {
            "sunny": "晴天", "overcast": "阴天", ...
        }

    def predict(self, image_path: str, top_k=3):
        image = Image.open(image_path)
        inputs = self.processor(
            text=self.candidate_labels, 
            images=image, 
            return_tensors="pt", 
            padding=True
        )
        outputs = self.model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)
        # Get Top-K...
        return [self.label_map[label] for label in top_labels]
```

### 4.3 API 调整
`POST /upload/image` 接口：
*   原有逻辑：保存文件 -> 返回 URL。
*   新增逻辑：调用 `ImageTagger.predict` -> 返回 `{ "url": "...", "suggested_tags": ["阴天", "海边"] }`。

## 5. 前端交互 (Frontend Interaction)

在 `Submit.vue` 中：
1.  当图片上传成功后，接收 `suggested_tags`。
2.  **自动填充**：如果当前标签栏为空，直接将推荐标签填入，并显示一个 Toast 提示：“已根据图片内容自动生成标签”。
3.  **视觉区分**：在标签选择区，将 AI 推荐的标签打上特殊的边框或角标（如 ✨），提示用户这是智能识别的结果。

## 6. 开发计划

1.  **Phase 1: 环境搭建**
    *   安装 PyTorch 和 Transformers。
    *   下载并缓存 CLIP 模型。
2.  **Phase 2: 后端逻辑**
    *   封装 `ImageTagger` 服务。
    *   改造上传接口。
3.  **Phase 3: 前端对接**
    *   解析推荐标签并自动选中。
