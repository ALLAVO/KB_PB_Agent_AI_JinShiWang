from fastapi import APIRouter, Request
from app.master.intention import classify_and_extract

router = APIRouter()

@router.post("/intention")
async def get_intention(request: Request):
    data = await request.json()
    text = data.get("text", "")
    result = classify_and_extract(text)
    return result
