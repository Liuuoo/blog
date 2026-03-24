import os
import re
import uuid
from datetime import date as date_cls
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import frontmatter
import markdown

from app.config import ALLOWED_EXTENSIONS, EXTERNAL_SOURCES, LOCKED_CATEGORIES, MEDIA_DIRS, POSTS_DIR
from app.models import PostSummary

VIRTUAL_UNARCHIVED_SEGMENT = "__virtual_unarchived__"
UNARCHIVED_DISPLAY_NAME = "未归档"
MARKDOWN_EXTENSIONS = [
    "fenced_code",
    "tables",
    "nl2br",
    "sane_lists",
    "pymdownx.tasklist",
    "pymdownx.tilde",
]
MARKDOWN_EXTENSION_CONFIGS = {
    "pymdownx.tasklist": {
        "clickable_checkbox": False,
        "custom_checkbox": False,
    }
}


def get_file_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    return ext.lower()


def is_allowed_file(filename: str) -> bool:
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


def _split_virtual_parts(path: str) -> List[str]:
    return [part for part in path.split("/") if part]


def join_virtual_path(*parts: str) -> str:
    cleaned_parts = []
    for part in parts:
        if not part:
            continue
        cleaned = part.strip("/")
        if cleaned:
            cleaned_parts.append(cleaned)
    return "/".join(cleaned_parts)


def strip_virtual_unarchived(path: str) -> Tuple[str, bool]:
    parts = _split_virtual_parts(path)
    has_virtual = VIRTUAL_UNARCHIVED_SEGMENT in parts
    cleaned_parts = [part for part in parts if part != VIRTUAL_UNARCHIVED_SEGMENT]
    return "/".join(cleaned_parts), has_virtual


def is_virtual_unarchived_path(path: str) -> bool:
    parts = _split_virtual_parts(path)
    return bool(parts) and parts[-1] == VIRTUAL_UNARCHIVED_SEGMENT


def build_unarchived_path(parent_path: str) -> str:
    return join_virtual_path(parent_path, VIRTUAL_UNARCHIVED_SEGMENT)


def get_path_display_name(path: str) -> str:
    if not path:
        return ""
    if is_virtual_unarchived_path(path):
        return UNARCHIVED_DISPLAY_NAME
    cleaned_path, _ = strip_virtual_unarchived(path)
    if not cleaned_path:
        return UNARCHIVED_DISPLAY_NAME
    return cleaned_path.split("/")[-1]


def get_post_category_label(category_path: str) -> str:
    cleaned_path, _ = strip_virtual_unarchived(category_path)
    if not cleaned_path:
        return UNARCHIVED_DISPLAY_NAME
    return cleaned_path.split("/")[0]


def get_virtual_source_groups() -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {}
    for locked_name in LOCKED_CATEGORIES:
        if locked_name in EXTERNAL_SOURCES:
            continue
        matches = sorted(
            source_name
            for source_name in EXTERNAL_SOURCES
            if source_name.endswith(locked_name)
        )
        if matches:
            groups[locked_name] = matches
    return groups


def get_grouped_source_members() -> Dict[str, str]:
    members: Dict[str, str] = {}
    for group_name, source_names in get_virtual_source_groups().items():
        for source_name in source_names:
            members[source_name] = group_name
    return members


def get_lock_scope(category: str) -> str:
    if category in LOCKED_CATEGORIES:
        return category
    return get_grouped_source_members().get(category, "")


def resolve_grouped_source_path(virtual_path: str) -> Optional[str]:
    cleaned_path, _ = strip_virtual_unarchived(virtual_path)
    parts = [part for part in cleaned_path.split("/") if part]
    if len(parts) < 2:
        return None

    group_name = parts[0]
    group_sources = get_virtual_source_groups().get(group_name, [])
    source_name = parts[1]
    if source_name not in group_sources:
        return None

    base = EXTERNAL_SOURCES[source_name]
    rest = parts[2:]
    return os.path.join(base, *rest) if rest else base


def resolve_path(virtual_path: str) -> str:
    """将虚拟路径解析为真实文件系统路径。"""
    grouped_path = resolve_grouped_source_path(virtual_path)
    if grouped_path:
        return grouped_path

    cleaned_path, _ = strip_virtual_unarchived(virtual_path)
    if not cleaned_path:
        return POSTS_DIR

    parts = cleaned_path.split("/", 1)
    category = parts[0]
    rest = parts[1] if len(parts) > 1 else ""
    if category in EXTERNAL_SOURCES:
        base = EXTERNAL_SOURCES[category]
        return os.path.join(base, rest) if rest else base
    return os.path.join(POSTS_DIR, cleaned_path)


def is_path_allowed(real_path: str) -> bool:
    """安全校验：确保路径在 POSTS_DIR 或外部源目录内。"""
    real_target = os.path.realpath(real_path)
    if real_target.startswith(os.path.realpath(POSTS_DIR)):
        return True
    for src_path in EXTERNAL_SOURCES.values():
        if os.path.exists(src_path) and real_target.startswith(os.path.realpath(src_path)):
            return True
    return False


def convert_obsidian_syntax(content: str) -> str:
    """将 Obsidian 特有语法转换为标准 Markdown + 博客媒体链接。"""

    def replace_image_embed(match: re.Match[str]) -> str:
        filename = match.group(1).strip()
        parts = filename.split("|")
        fname = parts[0].strip()
        ext = os.path.splitext(fname)[1].lower()
        if ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"):
            return f"![{fname}](/api/media/{fname})"
        if ext in (".mp4", ".webm"):
            return (
                f'<video src="/api/media/{fname}" controls '
                'style="max-width:100%;border-radius:6px;margin:1rem 0;"></video>'
            )
        return f"*[附件: {fname}]*"

    content = re.sub(r"!\[\[([^\]]+)\]\]", replace_image_embed, content)
    content = re.sub(
        r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]",
        lambda match: match.group(2) or match.group(1),
        content,
    )
    content = re.sub(r"==(.*?)==", r"<mark>\1</mark>", content)
    return content


def protect_latex(content: str) -> Tuple[str, Dict[str, str]]:
    """在 markdown 处理前保护 LaTeX 表达式，防止被 Markdown 解析器破坏。"""
    placeholders: Dict[str, str] = {}

    def make_placeholder(match_text: str) -> str:
        placeholder = f"LATEXPH{uuid.uuid4().hex[:12]}"
        placeholders[placeholder] = match_text
        return placeholder

    code_blocks: Dict[str, str] = {}

    def save_code_block(match: re.Match[str]) -> str:
        placeholder = f"CODEBLK{uuid.uuid4().hex[:12]}"
        code_blocks[placeholder] = match.group(0)
        return placeholder

    content = re.sub(r"```[\s\S]*?```", save_code_block, content)
    content = re.sub(r"`[^`\n]+`", save_code_block, content)
    content = re.sub(r"\$\$[\s\S]+?\$\$", lambda match: make_placeholder(match.group(0)), content)
    content = re.sub(r"(?<!\$)\$(?!\$)(.+?)\$(?!\$)", lambda match: make_placeholder(match.group(0)), content)

    for placeholder, code in code_blocks.items():
        content = content.replace(placeholder, code)

    return content, placeholders


def restore_latex(html: str, placeholders: Dict[str, str]) -> str:
    """将占位符替换回原始 LaTeX 表达式。"""
    for placeholder, original in placeholders.items():
        html = html.replace(placeholder, original)
    return html


def render_markdown(content: str) -> str:
    """统一 Markdown 渲染入口。"""
    content = convert_obsidian_syntax(content)
    content, latex_map = protect_latex(content)
    html = markdown.markdown(
        content,
        extensions=MARKDOWN_EXTENSIONS,
        extension_configs=MARKDOWN_EXTENSION_CONFIGS,
    )
    return restore_latex(html, latex_map)


def normalize_post_date(value: object, fallback_path: str) -> str:
    if value is None:
        mtime = os.path.getmtime(fallback_path)
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date_cls):
        return value.strftime("%Y-%m-%d")
    return str(value)


def build_post_summary(summary: str, content: str) -> str:
    if summary:
        return str(summary)

    clean = convert_obsidian_syntax(content.strip())
    lines = [
        line.strip()
        for line in clean.splitlines()
        if line.strip() and not line.startswith("#") and not line.startswith("!")
    ]
    text = lines[0] if lines else "暂无摘要"
    text = re.sub(r"\[(?: |x|X)\]\s*", "", text)
    text = re.sub(r"[*_`>$\\{}~]", "", text)
    return text[:100] + ("..." if len(text) > 100 else "")


_media_index: Dict[str, str] = {}
_media_indexed = False


def build_media_index() -> None:
    """构建 文件名 -> 真实路径 的媒体索引。"""
    global _media_index, _media_indexed
    if _media_indexed:
        return

    image_exts = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".mp4", ".webm"}
    for media_dir in MEDIA_DIRS:
        if not os.path.exists(media_dir):
            continue
        for root, dirs, files in os.walk(media_dir):
            dirs[:] = [directory for directory in dirs if not directory.startswith(".")]
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in image_exts and filename not in _media_index:
                    _media_index[filename] = os.path.join(root, filename)
    _media_indexed = True


def get_media_path(filename: str) -> Optional[str]:
    """根据文件名查找媒体文件真实路径。"""
    build_media_index()
    return _media_index.get(filename)


def scan_posts(category: str = "") -> List[PostSummary]:
    """扫描指定分类下的文章列表，仅包含直接子文件。"""
    posts: List[PostSummary] = []

    grouped_sources = get_virtual_source_groups().get(category)
    if grouped_sources:
        for source_name in grouped_sources:
            source_dir = EXTERNAL_SOURCES.get(source_name)
            if not source_dir or not os.path.exists(source_dir):
                continue
            for filename in os.listdir(source_dir):
                filepath = os.path.join(source_dir, filename)
                if os.path.isfile(filepath) and is_allowed_file(filename):
                    meta = parse_post_metadata(filepath, filename, join_virtual_path(category, source_name))
                    if meta:
                        posts.append(meta)
        posts.sort(key=lambda item: item.date, reverse=True)
        return posts

    target_dir = resolve_path(category)
    if not os.path.exists(target_dir):
        return posts

    for filename in os.listdir(target_dir):
        filepath = os.path.join(target_dir, filename)
        if os.path.isfile(filepath) and is_allowed_file(filename):
            meta = parse_post_metadata(filepath, filename, category)
            if meta:
                posts.append(meta)

    posts.sort(key=lambda item: item.date, reverse=True)
    return posts


def parse_post_metadata(filepath: str, filename: str, category: str = "") -> Optional[PostSummary]:
    ext = get_file_extension(filename)
    slug = join_virtual_path(category, filename) if category else filename
    category_label = get_post_category_label(category)

    try:
        if ext == ".md":
            post = frontmatter.load(filepath)
            title = post.get("title", filename.replace(".md", ""))
            date_str = normalize_post_date(post.get("date"), filepath)
            summary = build_post_summary(post.get("summary", ""), post.content)
            return PostSummary(
                slug=slug,
                title=str(title),
                date=date_str,
                summary=summary,
                category=category_label,
            )

        mtime = os.path.getmtime(filepath)
        date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        return PostSummary(
            slug=slug,
            title=filename,
            date=date_str,
            summary=f"{ext[1:].upper()} 源码",
            category=category_label,
        )
    except Exception as exc:
        print(f"解析出错 {filepath}: {exc}")
        return None


def count_all_posts() -> int:
    """递归统计所有文章数量，包含本地与外部源。"""
    total = 0
    if os.path.exists(POSTS_DIR):
        for root, dirs, files in os.walk(POSTS_DIR):
            dirs[:] = [directory for directory in dirs if not directory.startswith(".")]
            for filename in files:
                if is_allowed_file(filename):
                    total += 1
    for cat_path in EXTERNAL_SOURCES.values():
        total += count_posts_recursive(cat_path)
    return total


def count_posts_recursive(directory: str) -> int:
    """递归统计指定目录下所有可展示文件数量。"""
    total = 0
    if not os.path.exists(directory):
        return 0
    for root, dirs, files in os.walk(directory):
        dirs[:] = [subdir for subdir in dirs if not subdir.startswith(".")]
        for filename in files:
            if is_allowed_file(filename):
                total += 1
    return total
