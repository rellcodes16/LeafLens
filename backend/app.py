from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import traceback
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.app import app
from backend.api.text_search import run_text_search
from backend.api.image_search import run_image_search
import tempfile
import os
import imghdr

MAX_FILE_SIZE = 5 * 1024 * 1024  
ALLOWED_TYPES = ["jpeg", "png", "jpg"]


app = FastAPI()

origins = [
    "http://localhost:5173", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextSearchRequest(BaseModel):
    text: str

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("UNHANDLED ERROR:", str(exc))
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "type": "internal_server_error",
            "message": "Something went wrong on our server."
        },
    )

@app.post("/text-search")
async def text_search_endpoint(payload: TextSearchRequest):

    query = payload.text.strip()

    if len(query.split()) < 8:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "fail",
                "type": "text_too_short",
                "message": "Please enter more text."
            }
        )

    if len(query) > 50_000:
        raise HTTPException(
            status_code=413,
            detail={
                "status": "fail",
                "type": "text_too_large",
                "message": "Text is too large."
            }
        )

    result = run_text_search(query)
    
    if result["status"] == "fail":
        return {
            "status": "fail",
            "type": "no_match",
            "message": result.get("reason", "No match found.")
        }

    return result

@app.post("/image-search")
async def image_search_endpoint(file: UploadFile = File(...)):

    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "fail",
                "type": "invalid_file_type",
                "message": "Only JPG and PNG images are allowed."
            }
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail={
                "status": "fail",
                "type": "file_too_large",
                "message": "Image file too large."
            }
        )

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(contents)
        image_path = tmp.name

    result = run_image_search(image_path)

    if result["status"] == "fail":
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "type": "no_match",
                "message": result.get("reason", "No match found.")
            }
        )

    return result

