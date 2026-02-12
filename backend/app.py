from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from api.text_search import run_text_search
from api.image_search import run_image_search
import tempfile

app = FastAPI()

class TextSearchRequest(BaseModel):
    text: str

@app.post("/text-search")
async def text_search_endpoint(payload: TextSearchRequest):
    query = payload.text
    return run_text_search(query)



@app.post("/image-search")
async def image_search_endpoint(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        image_path = tmp.name

    return run_image_search(image_path)

