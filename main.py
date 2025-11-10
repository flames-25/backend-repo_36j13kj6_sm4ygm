import os
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User as UserSchema, Photo as PhotoSchema

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "HoloFrame Backend Running"}


@app.get("/test")
def test_database():
    status = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "collections": []
    }
    try:
        collections = db.list_collection_names()
        status["database"] = "✅ Connected"
        status["collections"] = collections
    except Exception as e:
        status["database"] = f"❌ Error: {str(e)[:80]}"
    return status


@app.get("/api/bootstrap")
async def bootstrap(link: Optional[str] = None):
    # Public view by link
    if link:
        users = list(db["user"].find({"link": link}).limit(1))
        if not users:
            return JSONResponse({"user": None, "photos": []})
        user = users[0]
        photos = list(db["photo"].find({"user_id": str(user.get("_id")), "is_public": True}).sort("date", -1))
        for p in photos:
            p["_id"] = str(p["_id"])  # serialize
        return {"user": None, "photos": photos}

    # Private bootstrap: ensure a demo user exists for this sandbox session
    # In a real app you'd have auth — here we seed one demo user
    demo = db["user"].find_one({"username": "demo"})
    if not demo:
        demo_id = create_document("user", UserSchema(
            name="Demo User",
            username="demo",
            email="demo@example.com",
            bio="Holographic curator",
            profile_pic=None,
            link="demo"
        ))
        demo = db["user"].find_one({"_id": ObjectId(demo_id)})

    photos = list(db["photo"].find({"user_id": str(demo.get("_id"))}).sort("date", -1))
    for p in photos:
        p["_id"] = str(p["_id"])  # serialize
    user = {
        "_id": str(demo.get("_id")),
        "name": demo.get("name"),
        "username": demo.get("username"),
        "email": demo.get("email"),
        "bio": demo.get("bio"),
        "profile_pic": demo.get("profile_pic"),
        "link": demo.get("link"),
    }
    return {"user": user, "photos": photos}


@app.post("/api/photos/upload")
async def upload_photo(
    file: UploadFile = File(...),
    caption: str = Form("") ,
    is_public: bool = Form(True)
):
    # Save the file to a local folder and serve via static path in this sandbox
    # For simplicity we store to /tmp and return a pseudo-public path via backend
    content = await file.read()
    fname = f"{datetime.utcnow().timestamp()}-{file.filename}"
    folder = "/tmp/uploads"
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, fname)
    with open(path, "wb") as f:
        f.write(content)

    # Ensure demo user exists and get id
    demo = db["user"].find_one({"username": "demo"})
    if not demo:
        raise HTTPException(400, "User not initialized")

    # Use a simple static serving proxy endpoint
    image_url = f"/api/static/{fname}"

    photo = PhotoSchema(
        image_url=image_url,
        caption=caption or None,
        user_id=str(demo.get("_id")),
        is_public=bool(is_public),
    )
    pid = create_document("photo", photo)
    doc = db["photo"].find_one({"_id": ObjectId(pid)})
    doc["_id"] = str(doc["_id"])  # serialize
    return {"photo": doc}


@app.get("/api/static/{fname}")
async def static_file(fname: str):
    file_path = os.path.join("/tmp/uploads", fname)
    if not os.path.exists(file_path):
        raise HTTPException(404, "Not found")
    from fastapi.responses import FileResponse
    return FileResponse(file_path)
