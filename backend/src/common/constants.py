# Tag Categories Configuration

TAG_CATEGORIES = {
    "lighting": {
        "label": "光线",
        "icon": "✨",
        "tags": ["阴天", "晴天", "室内", "夜景", "日落", "黄金时刻", "自然光", "闪光灯"]
    },
    "location": {
        "label": "地点",
        "icon": "📍",
        "tags": ["咖啡厅", "街道", "海边", "公园", "居家", "山", "城市", "废墟", "商场"]
    },
    "subject": {
        "label": "主题",
        "icon": "📷",
        "tags": ["人像", "静物", "扫街", "建筑", "猫", "狗", "美食", "花", "汽车", "胶片感"]
    }
}

# Reverse mapping for quick lookup (tag_name -> category_key)
TAG_TO_CATEGORY = {}
for category_key, data in TAG_CATEGORIES.items():
    for tag in data["tags"]:
        TAG_TO_CATEGORY[tag] = category_key
