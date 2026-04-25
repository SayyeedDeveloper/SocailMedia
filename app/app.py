from fastapi import FastAPI, HTTPException, File, Form, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import Post, create_db_and_tables, get_async_session
from app.schemas import CreatePost
from contextlib import asynccontextmanager
import os

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)




@app.get("/feed")
async def feed(
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]
    post_list = []
    for post in posts:
        post_list.append({
            "id": str(post.id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "origin_name": post.origin_name,
            "created_at": post.created_at
        })

    return {"posts": post_list}

@app.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        caption: str = Form(""),
        session: AsyncSession = Depends(get_async_session)
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save file to disk
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    post = Post(
        caption=caption,
        file_name=file.filename,
        url=f"/files/{file.filename}",
        file_type=file.content_type,
        origin_name=file.filename
    )

    session.add(post)
    await session.commit()
    await session.refresh(post)

    return post
