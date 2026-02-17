from typing import Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from PIL import Image
from src.utils.minio_client import minio_client
from src.utils.exif_helper import extract_exif
from src.core import deps
from src.apps.users.models import User
from src.apps.ai.service import get_image_tags
import uuid
import os
import io
import tempfile

router = APIRouter()

import asyncio

@router.post("/image", response_model=dict)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # ... existing validation ...
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Supported formats: JPEG, PNG, WEBP")
    
    file_ext = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"
    
    tmp_path = None
    try:
        # Read content (still in memory for now, but acceptable for <20MB)
        contents = await file.read()
        if len(contents) > 20 * 1024 * 1024:
             raise HTTPException(status_code=400, detail="File size exceeds 20MB limit")
             
        file_data = io.BytesIO(contents)
        
        # ... EXIF extraction ...
        exif_info = extract_exif(io.BytesIO(contents))
        
        # ... Dimensions ...
        width, height = 0, 0
        try:
            with Image.open(io.BytesIO(contents)) as img:
                width, height = img.size
        except Exception as e:
            print(f"Error getting image size: {e}")

        # AI Tagging
        suggested_tags = []
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
                tmp.write(contents)
                tmp_path = tmp.name
            
            suggested_tags = await get_image_tags(tmp_path)
        except Exception as e:
            print(f"AI Tagging failed: {e}")
        
        # Upload to MinIO (Offload blocking I/O to thread pool)
        # Using asyncio.to_thread to prevent blocking event loop
        file_url = await asyncio.to_thread(
            minio_client.upload_file,
            file_data, 
            file_name, 
            file.content_type
        )
        
        return {
            "url": file_url, 
            "exif": exif_info,
            "width": width,
            "height": height,
            "suggested_tags": suggested_tags
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload image")
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as e:
                print(f"Error removing temp file: {e}")
