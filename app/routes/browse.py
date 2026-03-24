import hashlib
import os

from fastapi import APIRouter, HTTPException, Query

from app.config import CATEGORY_ALIASES, EXTERNAL_SOURCES, LOCKED_CATEGORIES, POSTS_DIR
from app.services import (
    UNARCHIVED_DISPLAY_NAME,
    VIRTUAL_UNARCHIVED_SEGMENT,
    build_unarchived_path,
    count_posts_recursive,
    get_grouped_source_members,
    get_lock_scope,
    get_path_display_name,
    get_virtual_source_groups,
    is_allowed_file,
    is_path_allowed,
    is_virtual_unarchived_path,
    join_virtual_path,
    parse_post_metadata,
    resolve_path,
    strip_virtual_unarchived,
)
from app.state import verified_sessions

router = APIRouter()

BROWSE_FILE_LIMIT = 50


def get_display_name(path: str) -> str:
    if not path:
        return ""
    if is_virtual_unarchived_path(path):
        return UNARCHIVED_DISPLAY_NAME
    return CATEGORY_ALIASES.get(path, get_path_display_name(path))


def _serialize_post_item(meta) -> dict:
    return {
        "slug": meta.slug,
        "title": meta.title,
        "date": meta.date,
        "summary": meta.summary,
    }


def _serialize_folder_item(
    name: str,
    display_name: str,
    path: str,
    count: int,
    *,
    locked: bool = False,
) -> dict:
    return {
        "name": name,
        "display_name": display_name,
        "count": count,
        "path": path,
        "locked": locked,
    }


def _ensure_browse_access(path: str) -> None:
    cleaned_path, _ = strip_virtual_unarchived(path)
    parts = [part for part in cleaned_path.split("/") if part]
    if not parts:
        return

    lock_scope = get_lock_scope(parts[0])
    if not lock_scope:
        return

    token = hashlib.md5(f"{lock_scope}:{LOCKED_CATEGORIES[lock_scope]}".encode()).hexdigest()
    if token not in verified_sessions:
        raise HTTPException(status_code=403, detail="该分类已加密，请先验证密码")


def _list_physical_directory(path: str, abs_path: str) -> tuple[list[dict], list[dict]]:
    is_virtual_unarchived = is_virtual_unarchived_path(path)
    folders: list[dict] = []
    files: list[dict] = []

    for item in sorted(os.listdir(abs_path)):
        if item.startswith("."):
            continue

        item_path = os.path.join(abs_path, item)
        rel_path = join_virtual_path(path, item)

        if os.path.isdir(item_path):
            if is_virtual_unarchived:
                continue

            folders.append(
                _serialize_folder_item(
                    item,
                    get_display_name(rel_path),
                    rel_path,
                    count_posts_recursive(item_path),
                    locked=bool(get_lock_scope(item)) if not path else False,
                )
            )
            continue

        if os.path.isfile(item_path) and is_allowed_file(item):
            meta = parse_post_metadata(item_path, item, path)
            if meta:
                files.append(_serialize_post_item(meta))

    return folders, files


def _list_grouped_directory(path: str, group_name: str) -> tuple[list[dict], list[dict]]:
    is_virtual_unarchived = is_virtual_unarchived_path(path)
    folders: list[dict] = []
    files: list[dict] = []

    for source_name in get_virtual_source_groups().get(group_name, []):
        source_dir = EXTERNAL_SOURCES.get(source_name)
        if not source_dir or not os.path.exists(source_dir):
            continue

        source_label = CATEGORY_ALIASES.get(source_name, source_name)
        source_path = join_virtual_path(group_name, source_name)

        for item in sorted(os.listdir(source_dir)):
            if item.startswith("."):
                continue

            item_path = os.path.join(source_dir, item)

            if os.path.isdir(item_path):
                if is_virtual_unarchived:
                    continue

                rel_path = join_virtual_path(source_path, item)
                folders.append(
                    _serialize_folder_item(
                        item,
                        f"{source_label} / {get_display_name(rel_path)}",
                        rel_path,
                        count_posts_recursive(item_path),
                    )
                )
                continue

            if os.path.isfile(item_path) and is_allowed_file(item):
                category_path = join_virtual_path(path, source_name) if is_virtual_unarchived else source_path
                meta = parse_post_metadata(item_path, item, category_path)
                if meta:
                    files.append(_serialize_post_item(meta))

    return folders, files


def _append_root_external_sources(folders: list[dict]) -> None:
    grouped_sources = get_virtual_source_groups()
    grouped_members = set(get_grouped_source_members())

    for group_name, source_names in sorted(grouped_sources.items()):
        existing_paths = [
            EXTERNAL_SOURCES[source_name]
            for source_name in source_names
            if source_name in EXTERNAL_SOURCES and os.path.exists(EXTERNAL_SOURCES[source_name])
        ]
        if not existing_paths:
            continue

        folders.append(
            _serialize_folder_item(
                group_name,
                CATEGORY_ALIASES.get(group_name, group_name),
                group_name,
                sum(count_posts_recursive(source_path) for source_path in existing_paths),
                locked=bool(get_lock_scope(group_name)),
            )
        )

    for cat_name, cat_path in sorted(EXTERNAL_SOURCES.items()):
        if cat_name in grouped_members or not os.path.exists(cat_path):
            continue

        folders.append(
            _serialize_folder_item(
                cat_name,
                CATEGORY_ALIASES.get(cat_name, cat_name),
                cat_name,
                count_posts_recursive(cat_path),
                locked=bool(get_lock_scope(cat_name)),
            )
        )


def _finalize_listing(path: str, folders: list[dict], files: list[dict]) -> dict:
    files.sort(key=lambda item: item.get("date", ""), reverse=True)

    if not is_virtual_unarchived_path(path) and folders and files:
        folders.append(
            _serialize_folder_item(
                VIRTUAL_UNARCHIVED_SEGMENT,
                UNARCHIVED_DISPLAY_NAME,
                build_unarchived_path(path),
                len(files),
            )
        )
        files = []

    total_files = len(files)
    return {
        "path": path,
        "display_name": get_display_name(path),
        "folders": folders,
        "files": files[:BROWSE_FILE_LIMIT],
        "total_files": total_files,
        "has_more": total_files > BROWSE_FILE_LIMIT,
    }


@router.get("/api/browse")
async def browse_directory(path: str = Query(default="", description="相对路径")):
    if ".." in path:
        raise HTTPException(status_code=400, detail="非法路径")

    if path:
        _ensure_browse_access(path)

    cleaned_path, _ = strip_virtual_unarchived(path)
    cleaned_parts = [part for part in cleaned_path.split("/") if part]
    grouped_root = len(cleaned_parts) == 1 and cleaned_path in get_virtual_source_groups()

    if grouped_root:
        folders, files = _list_grouped_directory(path, cleaned_path)
        return _finalize_listing(path, folders, files)

    abs_path = resolve_path(path) if path else POSTS_DIR
    if path and not is_path_allowed(abs_path):
        raise HTTPException(status_code=400, detail="非法路径")
    if not os.path.exists(abs_path) or not os.path.isdir(abs_path):
        raise HTTPException(status_code=404, detail="目录不存在")

    folders, files = _list_physical_directory(path, abs_path)

    if not path:
        _append_root_external_sources(folders)

    return _finalize_listing(path, folders, files)
