import asyncio
import os
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import patch

import app.routes.browse as browse_route
import app.services as services


def write_markdown(path: str, body: str = "content") -> None:
    with open(path, "w", encoding="utf-8") as file:
        file.write(f"---\ntitle: {os.path.basename(path)}\n---\n\n{body}\n")


class BrowseUnarchivedTests(unittest.TestCase):
    def patched_sources(self, posts_dir: str, external_sources=None):
        external_sources = external_sources or {}
        stack = ExitStack()
        stack.enter_context(patch.object(services, "POSTS_DIR", posts_dir))
        stack.enter_context(patch.object(services, "EXTERNAL_SOURCES", external_sources))
        stack.enter_context(patch.object(services, "LOCKED_CATEGORIES", {}))
        stack.enter_context(patch.object(browse_route, "POSTS_DIR", posts_dir))
        stack.enter_context(patch.object(browse_route, "EXTERNAL_SOURCES", external_sources))
        stack.enter_context(patch.object(browse_route, "LOCKED_CATEGORIES", {}))
        stack.enter_context(patch.object(browse_route, "CATEGORY_ALIASES", {}))
        return stack

    def test_mixed_directory_uses_virtual_unarchived(self):
        with tempfile.TemporaryDirectory() as tempdir:
            os.mkdir(os.path.join(tempdir, "folder"))
            write_markdown(os.path.join(tempdir, "root.md"))
            write_markdown(os.path.join(tempdir, "folder", "child.md"))

            with self.patched_sources(tempdir):
                data = asyncio.run(browse_route.browse_directory(""))

                folder_paths = {item["path"]: item for item in data["folders"]}
                self.assertIn(services.VIRTUAL_UNARCHIVED_SEGMENT, folder_paths)
                self.assertEqual(folder_paths[services.VIRTUAL_UNARCHIVED_SEGMENT]["count"], 1)
                self.assertEqual(data["files"], [])

                unarchived = asyncio.run(browse_route.browse_directory(services.VIRTUAL_UNARCHIVED_SEGMENT))
                self.assertEqual(unarchived["folders"], [])
                self.assertEqual(len(unarchived["files"]), 1)
                self.assertEqual(
                    unarchived["files"][0]["slug"],
                    f"{services.VIRTUAL_UNARCHIVED_SEGMENT}/root.md",
                )

    def test_pure_directories_and_files_do_not_create_virtual_unarchived(self):
        with tempfile.TemporaryDirectory() as tempdir:
            os.mkdir(os.path.join(tempdir, "files-only"))
            os.mkdir(os.path.join(tempdir, "dirs-only"))
            os.mkdir(os.path.join(tempdir, "dirs-only", "nested"))
            write_markdown(os.path.join(tempdir, "files-only", "a.md"))
            write_markdown(os.path.join(tempdir, "files-only", "b.md"))

            with self.patched_sources(tempdir):
                files_only = asyncio.run(browse_route.browse_directory("files-only"))
                self.assertEqual(len(files_only["files"]), 2)
                self.assertFalse(any(
                    folder["path"].endswith(services.VIRTUAL_UNARCHIVED_SEGMENT)
                    for folder in files_only["folders"]
                ))

                dirs_only = asyncio.run(browse_route.browse_directory("dirs-only"))
                self.assertEqual(len(dirs_only["folders"]), 1)
                self.assertEqual(dirs_only["files"], [])
                self.assertFalse(any(
                    folder["path"].endswith(services.VIRTUAL_UNARCHIVED_SEGMENT)
                    for folder in dirs_only["folders"]
                ))

    def test_external_mixed_directory_uses_virtual_unarchived(self):
        with tempfile.TemporaryDirectory() as tempdir:
            external_dir = os.path.join(tempdir, "external")
            os.mkdir(external_dir)
            os.mkdir(os.path.join(external_dir, "topic"))
            write_markdown(os.path.join(external_dir, "note.md"))
            write_markdown(os.path.join(external_dir, "topic", "child.md"))

            with self.patched_sources(tempdir, {"外部": external_dir}):
                data = asyncio.run(browse_route.browse_directory("外部"))
                folder_paths = {item["path"]: item for item in data["folders"]}
                self.assertIn(f"外部/{services.VIRTUAL_UNARCHIVED_SEGMENT}", folder_paths)
                self.assertEqual(data["files"], [])

                unarchived = asyncio.run(
                    browse_route.browse_directory(f"外部/{services.VIRTUAL_UNARCHIVED_SEGMENT}")
                )
                self.assertEqual(unarchived["folders"], [])
                self.assertEqual(
                    unarchived["files"][0]["slug"],
                    f"外部/{services.VIRTUAL_UNARCHIVED_SEGMENT}/note.md",
                )


if __name__ == "__main__":
    unittest.main()
