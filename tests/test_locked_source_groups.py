import asyncio
import os
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from fastapi import HTTPException

import app.routes.auth as auth_route
import app.routes.blog as blog_route
import app.routes.browse as browse_route
import app.routes.posts as posts_route
import app.services as services
from app.models import PasswordRequest
from app.state import verified_sessions


def write_markdown(path: str, body: str = "content") -> None:
    with open(path, "w", encoding="utf-8") as file:
        file.write(f"---\ntitle: {os.path.basename(path)}\n---\n\n{body}\n")


class LockedSourceGroupTests(unittest.TestCase):
    def patched_sources(self, posts_dir: str, external_sources: dict, locked_categories: dict):
        stack = ExitStack()
        verified_sessions.clear()
        stack.callback(verified_sessions.clear)

        stack.enter_context(patch.object(services, "POSTS_DIR", posts_dir))
        stack.enter_context(patch.object(services, "EXTERNAL_SOURCES", external_sources))
        stack.enter_context(patch.object(services, "LOCKED_CATEGORIES", locked_categories))

        stack.enter_context(patch.object(auth_route, "LOCKED_CATEGORIES", locked_categories))

        stack.enter_context(patch.object(blog_route, "POSTS_DIR", posts_dir))
        stack.enter_context(patch.object(blog_route, "EXTERNAL_SOURCES", external_sources))
        stack.enter_context(patch.object(blog_route, "LOCKED_CATEGORIES", locked_categories))
        stack.enter_context(patch.object(blog_route, "CATEGORY_ALIASES", {}))

        stack.enter_context(patch.object(browse_route, "POSTS_DIR", posts_dir))
        stack.enter_context(patch.object(browse_route, "EXTERNAL_SOURCES", external_sources))
        stack.enter_context(patch.object(browse_route, "LOCKED_CATEGORIES", locked_categories))
        stack.enter_context(patch.object(browse_route, "CATEGORY_ALIASES", {}))

        stack.enter_context(patch.object(posts_route, "POSTS_DIR", posts_dir))
        stack.enter_context(patch.object(posts_route, "EXTERNAL_SOURCES", external_sources))
        stack.enter_context(patch.object(posts_route, "LOCKED_CATEGORIES", locked_categories))

        return stack

    def test_grouped_locked_sources_support_virtual_root_and_new_subfolders(self):
        with tempfile.TemporaryDirectory() as tempdir:
            posts_dir = os.path.join(tempdir, "posts")
            os.mkdir(posts_dir)

            source_2025 = os.path.join(tempdir, "2025-journal")
            source_2026 = os.path.join(tempdir, "2026-journal")
            os.mkdir(source_2025)
            os.mkdir(source_2026)
            os.mkdir(os.path.join(source_2026, "week1"))

            write_markdown(os.path.join(source_2025, "entry-a.md"))
            write_markdown(os.path.join(source_2026, "entry-b.md"))
            write_markdown(os.path.join(source_2026, "week1", "nested.md"))

            external_sources = {
                "2025-journal": source_2025,
                "2026-journal": source_2026,
            }
            locked_categories = {"journal": "pw"}

            with self.patched_sources(posts_dir, external_sources, locked_categories):
                with self.assertRaises(HTTPException) as error:
                    asyncio.run(browse_route.browse_directory("journal"))
                self.assertEqual(error.exception.status_code, 403)

                verified = asyncio.run(
                    auth_route.verify_password(PasswordRequest(category="2025-journal", password="pw"))
                )
                self.assertTrue(verified["success"])

                categories = asyncio.run(blog_route.list_categories())
                category_slugs = {category.slug for category in categories}
                self.assertIn("journal", category_slugs)
                self.assertNotIn("2025-journal", category_slugs)
                self.assertNotIn("2026-journal", category_slugs)

                grouped_listing = asyncio.run(browse_route.browse_directory("journal"))
                folder_paths = {folder["path"] for folder in grouped_listing["folders"]}
                self.assertIn("journal/2026-journal/week1", folder_paths)
                self.assertIn("journal/__virtual_unarchived__", folder_paths)
                self.assertEqual(grouped_listing["files"], [])

                grouped_unarchived = asyncio.run(
                    browse_route.browse_directory("journal/__virtual_unarchived__")
                )
                grouped_slugs = {item["slug"] for item in grouped_unarchived["files"]}
                self.assertIn("journal/__virtual_unarchived__/2025-journal/entry-a.md", grouped_slugs)
                self.assertIn("journal/__virtual_unarchived__/2026-journal/entry-b.md", grouped_slugs)

                nested_listing = asyncio.run(browse_route.browse_directory("journal/2026-journal/week1"))
                self.assertEqual(len(nested_listing["files"]), 1)
                self.assertEqual(
                    nested_listing["files"][0]["slug"],
                    "journal/2026-journal/week1/nested.md",
                )

                grouped_posts = asyncio.run(posts_route.list_posts("journal"))
                grouped_post_slugs = {post.slug for post in grouped_posts}
                self.assertIn("journal/2025-journal/entry-a.md", grouped_post_slugs)
                self.assertIn("journal/2026-journal/entry-b.md", grouped_post_slugs)

                public_posts = asyncio.run(posts_route.list_posts(""))
                self.assertFalse(any("journal" in post.slug for post in public_posts))

                post = asyncio.run(
                    posts_route.get_post("journal/__virtual_unarchived__/2025-journal/entry-a.md")
                )
                self.assertEqual(
                    post.slug,
                    "journal/__virtual_unarchived__/2025-journal/entry-a.md",
                )
                self.assertEqual(post.title, "entry-a.md")


if __name__ == "__main__":
    unittest.main()
