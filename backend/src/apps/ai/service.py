import asyncio
import os

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

# Define our labels based on centralized config
# We need to map English keywords (for CLIP) to Chinese tags (for our app)
# Since TAG_CATEGORIES only has Chinese, we might need to enhance the constants or keep a mapping here.
# For now, let's keep the mapping here but validate against TAG_CATEGORIES if needed, 
# or better yet, let's move the English mapping to constants.py as well?
# To avoid over-complicating constants.py with AI-specific stuff, let's keep the AI mapping here,
# but ensure the output Chinese tags exist in our system.

LABELS_MAP = {
    # Lighting
    "sunny": "晴天",
    "overcast": "阴天",
    "indoor": "室内",
    "night": "夜景",
    "sunset": "日落",
    "golden hour": "黄金时刻",
    
    # Location
    "street": "街拍",
    "cafe": "咖啡厅",
    "sea": "海边",
    "park": "公园",
    "home": "居家",
    "mountain": "山",
    "city": "城市",
    
    # Subject
    "portrait": "人像",
    "person": "人像",
    "cat": "猫",
    "dog": "狗",
    "food": "美食",
    "flower": "花",
    "architecture": "建筑",
    "car": "汽车"
}

ENGLISH_LABELS = list(LABELS_MAP.keys())

class ImageTagger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ImageTagger, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.processor = None
            cls._instance.device = "cuda" if torch.cuda.is_available() else "cpu"
        return cls._instance

    def load_model(self):
        if self.model is None:
            # Define local path: backend/src/core/model/clip-vit-base-patch32
            # __file__ is backend/src/apps/ai/service.py
            # dirname(abspath(__file__)) -> backend/src/apps/ai
            # dirname(...) -> backend/src/apps
            # dirname(...) -> backend/src
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            model_dir = os.path.join(base_dir, "core", "model", "clip-vit-base-patch32")
            model_id = "openai/clip-vit-base-patch32"
            
            print(f"Loading CLIP model on {self.device}...")
            
            # Check if local model exists
            if os.path.exists(model_dir) and os.path.exists(os.path.join(model_dir, "config.json")):
                print(f"Loading from local directory: {model_dir}")
                self.model = CLIPModel.from_pretrained(model_dir).to(self.device)
                self.processor = CLIPProcessor.from_pretrained(model_dir)
            else:
                print(f"Local model not found. Downloading {model_id}...")
                self.model = CLIPModel.from_pretrained(model_id).to(self.device)
                self.processor = CLIPProcessor.from_pretrained(model_id)
                
                # Save to local directory for future use
                print(f"Saving model to {model_dir}...")
                self.model.save_pretrained(model_dir)
                self.processor.save_pretrained(model_dir)
                
            print("CLIP model loaded.")

    def predict(self, image_path: str, top_k=3, threshold=0.2) -> list[str]:
        if self.model is None:
            self.load_model()
            
        try:
            image = Image.open(image_path)
            
            # Prepare inputs
            inputs = self.processor(
                text=ENGLISH_LABELS, 
                images=image, 
                return_tensors="pt", 
                padding=True
            ).to(self.device)

            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Calculate probabilities
            logits_per_image = outputs.logits_per_image  # image-text similarity score
            probs = logits_per_image.softmax(dim=1)  # softmax to get probabilities
            
            # Get top k
            values, indices = probs[0].topk(len(ENGLISH_LABELS))
            
            results = []
            for i in range(len(indices)):
                score = values[i].item()
                idx = indices[i].item()
                label_en = ENGLISH_LABELS[idx]
                
                # Filter by threshold and top_k limit
                if score > threshold:
                    label_cn = LABELS_MAP[label_en]
                    if label_cn not in results:
                        results.append(label_cn)
                
                if len(results) >= top_k:
                    break
                    
            return results
        except Exception as e:
            print(f"Error in AI tagging: {e}")
            return []

# Singleton instance
tagger = ImageTagger()

async def get_image_tags(image_path: str) -> list[str]:
    # Run in thread pool to avoid blocking async loop
    # Since loading model might be slow, the first call will block the thread, but not the loop.
    return await asyncio.to_thread(tagger.predict, image_path)
