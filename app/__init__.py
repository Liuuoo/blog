from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import register_routes

app = FastAPI(title="个人博客 API")
register_routes(app)
app.mount("/", StaticFiles(directory="web", html=True), name="web")
