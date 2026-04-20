from fastapi import FastAPI, HTTPException

from app.schemas import CreatePost

app = FastAPI()


text_posts = {1: {"title": "New Post", "content": "This new post content"}}


@app.get("/posts")
def get_all_posts(limit: int = None):
    return text_posts

@app.get("/posts/{id}")
def get_post(id: int):
    if id not in text_posts:
        raise HTTPException(status_code=404, detail="Post not found")

    return text_posts.get(id)


@app.post("/posts")
def create_post(post: CreatePost):
    new_post = {"title": post.title, "content": post.content}
    text_posts[max(text_posts.keys()) + 1 ] = new_post

    return new_post

@app.delete("/delete/{id}")
def delete_post(id: int):
    text_posts.pop(id)
    return text_posts
