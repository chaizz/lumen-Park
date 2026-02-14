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

@router.post("/image", response_model=dict)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # Validate file size (e.g. 5MB limit handled roughly here, 
    # but actual stream read is needed for precise check or nginx/middleware)
    # Validate content type
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Supported formats: JPEG, PNG, WEBP")
    
    # Generate unique filename
    file_ext = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"
    
    try:
        # Read file content to upload
        # Warning: Reading entire file into memory. For large files, stream it.
        # But for 5MB limit, it's acceptable.
        contents = await file.read()
        if len(contents) > 20 * 1024 * 1024: # Increased to 20MB for raw photo uploads to preserve EXIF
             raise HTTPException(status_code=400, detail="File size exceeds 20MB limit")
             
        file_data = io.BytesIO(contents)
        
        # Extract EXIF and Dimensions before uploading
        # Use a separate stream for PIL to avoid cursor issues or just use the same bytes
        pil_stream = io.BytesIO(contents)
        width, height = 0, 0
        try:
            with Image.open(pil_stream) as img:
                width, height = img.size
        except Exception as e:
            print(f"Error getting image size: {e}")

        # Reset stream or use fresh one for EXIF
        exif_info = extract_exif(io.BytesIO(contents)) 
        
        # AI Tagging (Non-blocking attempt, or blocking if we want result immediately)
        # To provide immediate feedback in the UI, we must await it.
        # Save temp file for AI processing (CLIP expects path or PIL Image)
        # Our service expects path currently, let's modify it or save temp.
        # Service updated to accept path. Let's save a temp file.
        suggested_tags = []
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
                tmp.write(contents)
                tmp_path = tmp.name
            
            # Call AI service
            suggested_tags = await get_image_tags(tmp_path)
            
            # Clean up temp file
            os.remove(tmp_path)
        except Exception as e:
            print(f"AI Tagging failed: {e}")
            # Don't fail the upload if AI fails
        
        file_url = minio_client.upload_file(
            file_data, 
            file_name, 
            content_type=file.content_type
        )
        
        return {
            "url": file_url, 
            "exif": exif_info,
            "width": width,
            "height": height,
            "suggested_tags": suggested_tags
        }
    except Exception as e:
        # Check if it is the size limit exception we just raised
        if isinstance(e, HTTPException):
            raise e
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload image")
