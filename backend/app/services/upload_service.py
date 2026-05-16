import os
import uuid
from fastapi import UploadFile
from pathlib import Path

class UploadService:
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file: UploadFile, subfolder: str = "") -> str:
        # Generate unique filename
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        
        target_dir = self.upload_dir / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = target_dir / filename
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
            
        # Return the URL path
        return f"/uploads/{subfolder}/{filename}" if subfolder else f"/uploads/{filename}"
