from pydantic import BaseModel

class PostSummary(BaseModel):
    slug: str
    title: str
    date: str
    summary: str
    category: str

class PostDetail(PostSummary):
    content: str
    is_source: bool = False

class Category(BaseModel):
    name: str
    count: int
    slug: str
    locked: bool

class BlogStats(BaseModel):
    total_posts: int
    total_categories: int
    last_updated: str

class PasswordRequest(BaseModel):
    category: str
    password: str
