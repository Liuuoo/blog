import os
from datetime import datetime
from typing import List

import frontmatter
from fastapi import APIRouter

from app.config import BLOG_CONFIG, CATEGORY_ALIASES, EXTERNAL_SOURCES, LOCKED_CATEGORIES, POSTS_DIR
from app.models import BlogStats, Category
from app.services import (
    UNARCHIVED_DISPLAY_NAME,
    count_all_posts,
    count_posts_recursive,
    get_grouped_source_members,
    get_virtual_source_groups,
    is_allowed_file,
)

router = APIRouter()


@router.get("/api/config")
async def get_blog_config():
    return BLOG_CONFIG


def _collect_date(filepath: str, filename: str, all_dates: list) -> None:
    if filename.endswith(".md"):
        try:
            post = frontmatter.load(filepath)
            value = post.get("date")
            if isinstance(value, datetime):
                all_dates.append(value.strftime("%Y-%m-%d"))
            elif value:
                all_dates.append(str(value))
            else:
                mtime = os.path.getmtime(filepath)
                all_dates.append(datetime.fromtimestamp(mtime).strftime("%Y-%m-%d"))
        except Exception:
            pass
    elif is_allowed_file(filename):
        mtime = os.path.getmtime(filepath)
        all_dates.append(datetime.fromtimestamp(mtime).strftime("%Y-%m-%d"))


def _count_visible_external_categories() -> int:
    count = 0
    grouped_sources = get_virtual_source_groups()
    grouped_members = set(get_grouped_source_members())

    for source_names in grouped_sources.values():
        if any(
            source_name in EXTERNAL_SOURCES and os.path.exists(EXTERNAL_SOURCES[source_name])
            for source_name in source_names
        ):
            count += 1

    for cat_name, cat_path in EXTERNAL_SOURCES.items():
        if cat_name in grouped_members or not os.path.exists(cat_path):
            continue
        count += 1

    return count


@router.get("/api/stats", response_model=BlogStats)
async def get_stats():
    cat_count = 0
    all_dates = []

    if os.path.exists(POSTS_DIR):
        root_posts = [
            filename
            for filename in os.listdir(POSTS_DIR)
            if os.path.isfile(os.path.join(POSTS_DIR, filename)) and is_allowed_file(filename)
        ]
        if root_posts:
            cat_count += 1

        for item in os.listdir(POSTS_DIR):
            if os.path.isdir(os.path.join(POSTS_DIR, item)):
                cat_count += 1

        for root, dirs, files in os.walk(POSTS_DIR):
            dirs[:] = [directory for directory in dirs if not directory.startswith(".")]
            for filename in files:
                if is_allowed_file(filename):
                    _collect_date(os.path.join(root, filename), filename, all_dates)

    cat_count += _count_visible_external_categories()

    for cat_path in EXTERNAL_SOURCES.values():
        if os.path.exists(cat_path):
            for root, dirs, files in os.walk(cat_path):
                dirs[:] = [directory for directory in dirs if not directory.startswith(".")]
                for filename in files:
                    if is_allowed_file(filename):
                        _collect_date(os.path.join(root, filename), filename, all_dates)

    latest_date = "未知"
    if all_dates:
        all_dates.sort(reverse=True)
        latest_date = all_dates[0]

    return BlogStats(
        total_posts=count_all_posts(),
        total_categories=cat_count,
        last_updated=latest_date,
    )


@router.get("/api/categories", response_model=List[Category])
async def list_categories():
    categories = []

    if os.path.exists(POSTS_DIR):
        for name in sorted(os.listdir(POSTS_DIR)):
            if os.path.isdir(os.path.join(POSTS_DIR, name)):
                categories.append(
                    Category(
                        name=CATEGORY_ALIASES.get(name, name),
                        count=count_posts_recursive(os.path.join(POSTS_DIR, name)),
                        slug=name,
                        locked=name in LOCKED_CATEGORIES,
                    )
                )

        root_posts = [
            filename
            for filename in os.listdir(POSTS_DIR)
            if os.path.isfile(os.path.join(POSTS_DIR, filename)) and is_allowed_file(filename)
        ]
        if root_posts:
            categories.append(
                Category(
                    name=UNARCHIVED_DISPLAY_NAME,
                    count=len(root_posts),
                    slug="_uncategorized",
                    locked=False,
                )
            )

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

        categories.append(
            Category(
                name=CATEGORY_ALIASES.get(group_name, group_name),
                count=sum(count_posts_recursive(source_path) for source_path in existing_paths),
                slug=group_name,
                locked=True,
            )
        )

    for cat_name, cat_path in sorted(EXTERNAL_SOURCES.items()):
        if cat_name in grouped_members or not os.path.exists(cat_path):
            continue

        categories.append(
            Category(
                name=CATEGORY_ALIASES.get(cat_name, cat_name),
                count=count_posts_recursive(cat_path),
                slug=cat_name,
                locked=cat_name in LOCKED_CATEGORIES,
            )
        )

    return categories
