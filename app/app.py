import uuid
from fastapi import FastAPI, HTTPException, File, Form, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import Post, create_db_and_tables, get_async_session, User
from contextlib import asynccontextmanager
import os

from app.schemas import UserRead, UserCreate, UserUpdate
from app.users import auth_backend, current_active_user, fastapi_users

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_TYPES = {"image/jpeg", "image/png"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(fastapi_users.get_auth_router(auth_backend), prefix='/auth/jwt', tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=['auth'])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=['users'])
@app.get("/feed")
async def feed(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
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
            "created_at": post.created_at,
            "is_owner": post.user_id == user.id
        })

    return {"posts": post_list}

@app.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        caption: str = Form(""),
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type")

    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Save file to disk
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    post = Post(
        caption=caption,
        user_id=user.id,
        file_name=unique_name,
        url=f"/files/{unique_name}",
        file_type=file.content_type,
        origin_name=file.filename
    )

    session.add(post)
    await session.commit()
    await session.refresh(post)

    return post


@app.delete("/post/{id}")
async def delete(
        id: str,
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_active_user)
):
    post = await session.get(Post, id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    file_path = os.path.join(UPLOAD_DIR, post.file_name)

    if os.path.exists(file_path):
        os.remove(file_path)

    await session.delete(post)
    await session.commit()

    return {"message": "Post deleted"}