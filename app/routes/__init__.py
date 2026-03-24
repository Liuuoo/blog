from fastapi import FastAPI

from app.routes import blog, posts, auth, browse, admin, media


def register_routes(app: FastAPI):
    app.include_router(blog.router)
    app.include_router(posts.router)
    app.include_router(auth.router)
    app.include_router(browse.router)
    app.include_router(admin.router)
    app.include_router(media.router)
