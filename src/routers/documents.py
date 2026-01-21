import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(tags=["Documents"])

OUTPUT_DIR = "generated_docs"

@router.get("/documents/download/{filename}")
async def download_document(filename: str):
    """
    Download a generated document.
    """
    file_path = os.path.join(OUTPUT_DIR, filename)
    
    # Security check: prevent directory traversal
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, media_type='application/pdf', filename=filename)
