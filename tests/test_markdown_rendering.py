import unittest

from app.services import render_markdown


class MarkdownRenderingTests(unittest.TestCase):
    def test_render_markdown_supports_planned_extensions(self):
        html = render_markdown(
            """```python
print(1)
```

line1
line2

- [ ] todo
- [x] done

~~gone~~
"""
        )

        self.assertIn('<code class="language-python">', html)
        self.assertIn('<br />', html)
        self.assertIn('type="checkbox"', html)
        self.assertIn('disabled', html)
        self.assertIn('checked', html)
        self.assertIn('<del>gone</del>', html)
        self.assertNotIn('codehilite', html)


if __name__ == "__main__":
    unittest.main()
