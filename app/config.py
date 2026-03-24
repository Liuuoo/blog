import os
import yaml
from typing import Dict, List

CONFIG_PATH = "config.yaml"
FALLBACK_CONFIG_PATH = "config.example.yaml"


def _read_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        return _read_yaml(CONFIG_PATH)
    if os.path.exists(FALLBACK_CONFIG_PATH):
        return _read_yaml(FALLBACK_CONFIG_PATH)
    return {}

def save_config():
    """将当前运行时配置写回 config.yaml"""
    cfg = load_config()
    cfg["category_aliases"] = CATEGORY_ALIASES
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

CONFIG = load_config()
BLOG_CONFIG = CONFIG.get("blog", {})
LOCKED_CATEGORIES: Dict[str, str] = CONFIG.get("locked_categories", {})

# 文章根目录，支持绝对/相对路径
_posts_dir_raw = CONFIG.get("posts_dir", "posts")
POSTS_DIR = _posts_dir_raw if os.path.isabs(_posts_dir_raw) else _posts_dir_raw

# 管理员密码
ADMIN_PASSWORD: str = CONFIG.get("admin_password", "admin123")

# 分类显示别名
CATEGORY_ALIASES: Dict[str, str] = CONFIG.get("category_aliases", {}) or {}

# 支持直接按行展示的源码后缀
ALLOWED_EXTENSIONS = {
    ".md", ".py", ".cpp", ".c", ".h", ".hpp", ".js", ".ts",
    ".go", ".java", ".html", ".css", ".json", ".yaml", ".yml", ".sh"
}

# 外部笔记源：虚拟分类名 → 真实文件系统路径
EXTERNAL_SOURCES: Dict[str, str] = {}
# root_only 源：仅扫描直接子文件，不递归子目录（用于归档散落文件）
ROOT_ONLY_SOURCES: set = set()
for _src in CONFIG.get("external_sources", []):
    _cat = _src.get("category", "")
    _path = _src.get("path", "")
    if _cat and _path:
        EXTERNAL_SOURCES[_cat] = _path
        if _src.get("root_only", False):
            ROOT_ONLY_SOURCES.add(_cat)

# 媒体文件搜索目录
MEDIA_DIRS: List[str] = CONFIG.get("media_dirs", [])
