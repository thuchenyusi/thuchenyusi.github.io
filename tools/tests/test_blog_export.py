import base64
import copy
import hashlib
import io
import json
import re
import sys
import tempfile
import unittest
import zipfile
from email.message import Message
from pathlib import Path
from urllib.parse import unquote
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from export_blog import ExportError, Exporter, canonical_url, image_spans


PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aL1sAAAAASUVORK5CYII="
)


class BlogExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.site = self.root / "site"
        self.site.mkdir()
        for filename in ("avatar.png", "background.png", "cover.png", "中文.png", "photo(1).png"):
            path = self.site / "assets" / filename
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(PNG)
        self.config = {
            "schema_version": 3,
            "title": "测试博客",
            "generated_at": "2026-10-06T19:00:00+08:00",
            "site_url": "https://blog.example.com",
            "baseurl": "",
            "cdn": "",
            "site_images": [{"role": "avatar", "url": "/assets/avatar.png"},
                            {"role": "sidebar_background", "url": "/assets/background.png"}],
            "posts": [],
            "works": []
        }
        self.output = self.root / "blog.zip"

    def post(self, markdown, filename="2026-10-06-book.md", **extra):
        return {"source": "_posts/" + filename, "filename": filename,
                "title": "书籍", "url": "/posts/book/", "markdown": markdown, **extra}

    def work(self, markdown, filename="little-prince.md", work_id="little-prince", **extra):
        return {"id": work_id, "source": "_works/" + filename, "filename": filename,
                "title": "小王子", "url": "/reviews/little-prince/", "markdown": markdown, **extra}

    def export(self, posts, works=None):
        self.config["posts"] = posts
        if works is not None:
            self.config["works"] = works
        counts = Exporter(self.config, self.site).write(self.output)
        with zipfile.ZipFile(self.output) as archive:
            self.assertIsNone(archive.testzip())
            contents = {name: archive.read(name) for name in archive.namelist()}
        return counts, contents, json.loads(contents["manifest.json"])

    def test_extracted_markdown_resolves_images_and_shared_images_are_deduplicated(self):
        posts = [self.post("![封面](/assets/cover.png)\n"),
                 self.post("![同一封面](/assets/cover.png)\n", "2026-10-07-second.md")]
        counts, contents, manifest = self.export(posts)
        self.assertEqual(counts, (2, 0, 3))
        with zipfile.ZipFile(self.output) as archive:
            archive.extractall(self.root / "extracted")
        for post in posts:
            path = self.root / "extracted/posts" / post["filename"]
            text = path.read_text(encoding="utf-8")
            for start, end in image_spans(text):
                self.assertEqual((path.parent / text[start:end]).read_bytes(), PNG)
        cover = next(image for image in manifest["images"] if image["url"].endswith("cover.png"))
        self.assertEqual(len(cover["uses"]), 2)
        self.assertEqual(cover["path"], "images/blog.example.com/assets/cover.png")
        self.assertEqual(cover["sha256"], hashlib.sha256(contents[cover["path"]]).hexdigest())
        self.assertEqual({image["role"] for image in manifest["site_images"]}, {"avatar", "sidebar_background"})
        self.assertTrue(all(image["path"].startswith("images/blog.example.com/assets/") for image in manifest["site_images"]))

    def test_original_url_directories_and_unicode_names_are_preserved(self):
        _, contents, manifest = self.export([
            self.post("![封面](/assets/cover.png)"),
            self.post("![截图](/assets/中文.png)", "2026-10-07-game.md")
        ])
        paths = {image["url"]: image["path"] for image in manifest["images"]}
        self.assertEqual(paths["https://blog.example.com/assets/cover.png"], "images/blog.example.com/assets/cover.png")
        self.assertEqual(paths["https://blog.example.com/assets/%E4%B8%AD%E6%96%87.png"], "images/blog.example.com/assets/中文.png")
        self.assertIn("../images/blog.example.com/assets/cover.png", contents["posts/2026-10-06-book.md"].decode())
        markdown = contents["posts/2026-10-07-game.md"].decode()
        for start, end in image_spans(markdown):
            self.assertEqual(contents[unquote(markdown[start:end]).removeprefix("../")], PNG)

    def test_usage_changes_do_not_move_images(self):
        _, _, original = self.export([self.post("![封面](/assets/cover.png)")])
        _, _, shared = self.export([self.post("![封面](/assets/cover.png)"),
                                    self.post("![封面](/assets/cover.png)", "2026-10-07-second.md")])
        self.assertEqual({item["url"]: item["path"] for item in original["images"]},
                         {item["url"]: item["path"] for item in shared["images"]})

    def test_site_image_used_by_post_stays_at_original_url_path(self):
        _, contents, manifest = self.export([self.post("![头像](/assets/avatar.png)")])
        avatar = next(image for image in manifest["images"] if image["url"].endswith("avatar.png"))
        self.assertEqual(avatar["path"], "images/blog.example.com/assets/avatar.png")
        site_avatar = next(image for image in manifest["site_images"] if image["role"] == "avatar")
        self.assertEqual(site_avatar["path"], avatar["path"])
        self.assertIn("../" + avatar["path"], contents["posts/2026-10-06-book.md"].decode())

    def test_manifest_keeps_only_distinct_source_references(self):
        _, _, manifest = self.export([self.post("![相对地址](/assets/cover.png)")])
        self.assertEqual(manifest["schema_version"], 4)
        avatar = next(image for image in manifest["images"] if image["url"].endswith("avatar.png"))
        # Site config may use a relative spelling, so preserve it once.
        self.assertEqual(avatar["uses"], [{"role": "avatar", "reference": "/assets/avatar.png"}])
        self.config["site_images"][0]["url"] = "https://blog.example.com/assets/avatar.png"
        _, _, manifest = self.export([self.post("![绝对地址](https://blog.example.com/assets/cover.png)")])
        avatar = next(image for image in manifest["images"] if image["url"].endswith("avatar.png"))
        self.assertEqual(avatar["uses"], [{"role": "avatar"}])
        cover = next(image for image in manifest["images"] if image["url"].endswith("cover.png"))
        self.assertNotIn("reference", cover["uses"][0])
        self.assertNotIn("url", cover["uses"][0])

    def test_unicode_post_folder_uses_readable_local_image(self):
        filename = "2026-10-06-书评.md"
        _, contents, _ = self.export([self.post("![封面](/assets/cover.png)", filename)])
        markdown = contents["posts/" + filename].decode()
        for start, end in image_spans(markdown):
            path = unquote(markdown[start:end]).removeprefix("../")
            self.assertEqual(contents[path], PNG)

    def test_code_examples_comments_and_ordinary_links_are_preserved(self):
        markdown = (
            "[购买](/assets/cover.png)\n"
            "`![示例](/assets/missing.png)`\n"
            "```markdown\n![示例](/assets/missing.png)\n```\n"
            "<!-- ![示例](/assets/missing.png) -->\n"
            "![真实图片](/assets/cover.png)\n"
        )
        _, contents, _ = self.export([self.post(markdown)])
        exported = contents["posts/2026-10-06-book.md"].decode()
        self.assertTrue(exported.startswith(markdown.rsplit("![真实图片]", 1)[0]))
        self.assertIn("![真实图片](../images/", exported)

    def test_indented_code_is_preserved_but_list_images_are_exported(self):
        markdown = ("正文\n\n    ![代码](/assets/missing.png)\n\n"
                    "- 列表\n\n    ![图片](/assets/cover.png)\n")
        _, contents, _ = self.export([self.post(markdown)])
        exported = contents["posts/2026-10-06-book.md"].decode()
        self.assertIn("    ![代码](/assets/missing.png)", exported)
        self.assertIn("    ![图片](../images/", exported)

    def test_quoted_and_list_nested_code_fences_are_preserved(self):
        markdown = ("> ```markdown\n> ![代码](/assets/missing.png)\n> ```\n\n"
                    "- 列表\n\n  ```markdown\n  ![代码](/assets/missing.png)\n  ```\n\n"
                    "![图片](/assets/cover.png)\n")
        _, contents, _ = self.export([self.post(markdown)])
        exported = contents["posts/2026-10-06-book.md"].decode()
        self.assertIn("> ![代码](/assets/missing.png)", exported)
        self.assertIn("  ![代码](/assets/missing.png)", exported)

    def test_inline_nested_parentheses_and_angle_destinations(self):
        markdown = '![嵌套 [说明]](/assets/photo(1).png "标题")\n![中文](</assets/中文.png>)'
        counts, contents, _ = self.export([self.post(markdown)])
        self.assertEqual(counts[2], 4)
        exported = contents["posts/2026-10-06-book.md"].decode()
        self.assertIn(' "标题")', exported)
        self.assertIn("](<../images/", exported)

    def test_reference_images_rewrite_only_used_definitions(self):
        markdown = (
            "![封面][BOOK]\n![book][]\n![Book]\n"
            '[book]: /assets/cover.png "保留标题"\n'
            "[购买][shop]\n[shop]: https://book.douban.com/subject/1807516/\n"
        )
        _, contents, _ = self.export([self.post(markdown)])
        exported = contents["posts/2026-10-06-book.md"].decode()
        self.assertIn("[book]: ../images/", exported)
        self.assertIn('[shop]: https://book.douban.com/subject/1807516/', exported)
        self.assertIn('"保留标题"', exported)

    def test_html_images_and_srcset_are_local(self):
        markdown = ('<picture><source srcset="/assets/cover.png 1x, /assets/中文.png 2x">'
                    '<img src="/assets/cover.png" data-src="/assets/background.png"></picture>')
        _, contents, _ = self.export([self.post(markdown)])
        exported = contents["posts/2026-10-06-book.md"].decode()
        self.assertEqual(len(image_spans(exported)), 4)
        self.assertNotIn('="/assets/', exported)
        self.assertIn(" 1x, ../images/", exported)

    def test_front_matter_image_and_image_path_are_rewritten(self):
        for value in ('image: "/assets/cover.png" # 注释', 'image:\n  path: /assets/cover.png\n  alt: 封面'):
            with self.subTest(value=value):
                markdown = "---\ntitle: 书籍\n" + value + "\n---\n正文\n"
                _, contents, _ = self.export([self.post(markdown, front_image="/assets/cover.png")])
                exported = contents["posts/2026-10-06-book.md"].decode()
                self.assertIn("../images/blog.example.com/assets/cover.png", exported)
                self.assertTrue(exported.endswith("---\n正文\n"))

    def test_same_filename_different_queries_do_not_collide(self):
        _, _, manifest = self.export([self.post("![A](/assets/cover.png?v=1)\n![B](/assets/cover.png?v=2)")])
        covers = [image for image in manifest["images"] if "cover.png" in image["url"]]
        self.assertEqual(len(covers), 2)
        self.assertNotEqual(covers[0]["path"], covers[1]["path"])
        self.assertTrue(all(re.fullmatch(r"images/blog.example.com/assets/cover-[a-f0-9]{16}\.png", image["path"])
                            for image in covers))

    def test_different_domains_and_original_directories_remain_separate(self):
        urls = ["https://image.example.com/books/cover.png", "https://other.example.com/books/cover.png",
                "https://image.example.com/games/cover.png"]
        with patch.object(Exporter, "fetch", return_value=(PNG, "image/png")):
            _, _, manifest = self.export([self.post("\n".join(f"![图]({url})" for url in urls))])
        paths = {image["url"]: image["path"] for image in manifest["images"]}
        for url in urls:
            self.assertEqual(paths[url], "images/" + url.removeprefix("https://"))

    def test_unsafe_segments_are_portable_and_references_resolve_after_extraction(self):
        urls = ["https://image.example.com/CON/a%2Fb.png", "https://image.example.com/../NUL.png",
                "https://image.example.com/a%5Cb/name%3F.png", "https://image.example.com/trailing./file%20",
                "https://image.example.com/percent%252F.png"]
        with patch.object(Exporter, "fetch", return_value=(PNG, "image/png")):
            _, _, manifest = self.export([self.post("\n".join(f"![图]({url})" for url in urls))])
        paths = {image["url"]: image["path"] for image in manifest["images"]}
        self.assertEqual(paths[urls[0]], "images/image.example.com/%43ON/a%2Fb.png")
        self.assertEqual(paths[urls[1]], "images/image.example.com/%2E%2E/%4EUL.png")
        self.assertEqual(paths[urls[2]], "images/image.example.com/a%5Cb/name%3F.png")
        self.assertEqual(paths[urls[3]], "images/image.example.com/trailing%2E/file%20")
        self.assertEqual(paths[urls[4]], "images/image.example.com/percent%252F.png")
        with zipfile.ZipFile(self.output) as archive:
            archive.extractall(self.root / "extracted")
        post = self.root / "extracted/posts/2026-10-06-book.md"
        markdown = post.read_text(encoding="utf-8")
        for start, end in image_spans(markdown):
            resolved = (post.parent / unquote(markdown[start:end])).resolve()
            self.assertTrue(resolved.is_relative_to((self.root / "extracted").resolve()), str(resolved))
            self.assertEqual(resolved.read_bytes(), PNG)

    def test_case_scheme_and_file_directory_collisions_do_not_overwrite(self):
        urls = ["https://image.example.com/a.png", "https://image.example.com/A.png",
                "http://image.example.com/a.png", "https://image.example.com/icon",
                "https://image.example.com/icon/part.png"]
        with patch.object(Exporter, "fetch", return_value=(PNG, "image/png")):
            _, _, manifest = self.export([self.post("\n".join(f"![图]({url})" for url in urls))])
        paths = [image["path"] for image in manifest["images"]]
        self.assertEqual(len(paths), len(set(path.casefold() for path in paths)))
        self.assertFalse(any(other.casefold().startswith(path.casefold() + "/")
                             for path in paths for other in paths))
        with zipfile.ZipFile(self.output) as archive:
            archive.extractall(self.root / "extracted")

    def test_baseurl_local_images_and_cdn_media_subpath(self):
        self.config["baseurl"] = "/blog"
        counts, _, _ = self.export([self.post("![封面](assets/cover.png)")])
        self.assertEqual(counts, (1, 0, 3))
        config = copy.deepcopy(self.config)
        config["cdn"] = "https://image.example.com"
        self.assertEqual(canonical_url("cover.png", config, "books/book"),
                         "https://image.example.com/books/book/cover.png")
        self.assertEqual(canonical_url("https://image.example.com/中文.png?q=中文", config),
                         "https://image.example.com/%E4%B8%AD%E6%96%87.png?q=%E4%B8%AD%E6%96%87")

    def test_missing_image_does_not_overwrite_previous_archive(self):
        self.export([self.post("![封面](/assets/cover.png)")])
        previous = self.output.read_bytes()
        self.config["posts"] = [self.post("![丢失](/assets/missing.png)")]
        with self.assertRaisesRegex(ExportError, "Missing local image"):
            Exporter(self.config, self.site).write(self.output)
        self.assertEqual(self.output.read_bytes(), previous)

    def test_remote_download_failure_is_reported(self):
        exporter = Exporter(self.config, self.site)
        with patch("export_blog.urlopen", side_effect=OSError("offline")), patch("export_blog.time.sleep"):
            with self.assertRaisesRegex(ExportError, "Unable to download"):
                exporter.fetch("https://image.example.com/missing.png")

    def test_remote_html_error_page_is_rejected(self):
        response = io.BytesIO(b"<html>Access denied</html>")
        response.headers = Message()
        response.headers["Content-Type"] = "text/html"
        with patch("export_blog.urlopen", return_value=response):
            with self.assertRaisesRegex(ExportError, "non-image"):
                Exporter(self.config, self.site).fetch("https://image.example.com/cover.png")

    def test_embedded_image_and_svg_fragments_remain_usable(self):
        (self.site / "assets/icon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        embedded = "data:image/png;base64," + base64.b64encode(PNG).decode()
        _, contents, manifest = self.export([self.post(
            f"![内嵌]({embedded})\n![图标](/assets/icon.svg#one)\n![图标](/assets/icon.svg#two)"
        )])
        exported = contents["posts/2026-10-06-book.md"].decode()
        self.assertIn(embedded, exported)
        icons = [image for image in manifest["images"] if image["url"].endswith("icon.svg")]
        self.assertEqual(len(icons), 1)
        self.assertIn(".svg#one)", exported)
        self.assertIn(".svg#two)", exported)

    def test_liquid_image_expression_fails_with_actionable_error(self):
        with self.assertRaisesRegex(ExportError, "Liquid"):
            self.export([self.post('![封面]({{site.image_url}}/cover.png)')])

    def test_local_path_cannot_escape_site_directory(self):
        with self.assertRaisesRegex(ExportError, "Missing local image"):
            self.export([self.post('![图片](/../outside.png)')])

    def test_image_from_liquid_include_cannot_be_silently_omitted(self):
        with self.assertRaisesRegex(ExportError, "no exportable Markdown reference"):
            self.export([self.post('{% include cover.html %}',
                                   rendered_images=["/assets/cover.png"])])

    def test_works_are_exported_to_reviews_with_rewritten_images(self):
        markdown = ("---\nid: little-prince\nimage: \"/assets/cover.png\"\n---\n"
                    "短评。\n\n![插图](/assets/中文.png)\n")
        counts, contents, manifest = self.export(
            [self.post("正文\n")], [self.work(markdown, front_image="/assets/cover.png")])
        self.assertEqual(counts, (1, 1, 4))
        exported = contents["reviews/little-prince.md"].decode()
        self.assertIn("../images/blog.example.com/assets/cover.png", exported)
        self.assertIn("id: little-prince", exported)
        for start, end in image_spans(exported):
            path = unquote(exported[start:end]).removeprefix("../")
            self.assertEqual(contents[path], PNG)
        self.assertEqual(manifest["works"], [{
            "id": "little-prince", "source": "_works/little-prince.md",
            "filename": "little-prince.md", "title": "小王子", "url": "/reviews/little-prince/"
        }])
        readme = contents["README.md"].decode()
        self.assertIn("## 作品", readme)
        self.assertIn("(reviews/little-prince.md)", readme)

    def test_cover_shared_by_post_and_work_is_deduplicated(self):
        work = self.work("---\nid: little-prince\nimage: \"/assets/cover.png\"\n---\n短评。\n",
                         front_image="/assets/cover.png")
        counts, _, manifest = self.export([self.post("![同一封面](/assets/cover.png)\n")], [work])
        self.assertEqual(counts, (1, 1, 3))
        cover = next(image for image in manifest["images"] if image["url"].endswith("cover.png"))
        self.assertEqual({use["markdown"] for use in cover["uses"]},
                         {"posts/2026-10-06-book.md", "reviews/little-prince.md"})

    def test_post_works_yaml_is_preserved_without_expansion(self):
        front = "---\ntitle: 书籍\nworks:\n  - little-prince\n---\n"
        _, contents, _ = self.export([self.post(front + "正文\n")], [self.work("短评\n")])
        self.assertTrue(contents["posts/2026-10-06-book.md"].decode().startswith(front))

    def test_work_cards_expand_in_place_and_resolve_after_extraction(self):
        front = "---\ntitle: Reading\nworks: [little-prince]\n---\n"
        tag = '{% include work-card.html id="little-prince" %}'
        post = self.post(front + "Before\n\n" + tag + "\n\nAfter\n", rendered_images=["/assets/cover.png"])
        work = self.work("---\nimage: /assets/cover.png\n---\nReview\n",
                         front_image="/assets/cover.png", creator="Author", rating=8.5,
                         rendered_images=["/assets/cover.png"])
        counts, contents, manifest = self.export([post], [work])
        text = contents["posts/2026-10-06-book.md"].decode()
        self.assertTrue(text.startswith(front))
        self.assertNotIn(tag, text)
        self.assertLess(text.index("Before"), text.index("我的评分：8.5 / 10"))
        self.assertLess(text.index("我的评分：8.5 / 10"), text.index("After"))
        self.assertIn("Author", text)
        self.assertIn("[小王子](../reviews/little-prince.md)", text)
        self.assertEqual(counts, (1, 1, 3))
        cover = next(image for image in manifest["images"] if image["url"].endswith("cover.png"))
        self.assertEqual({use["markdown"] for use in cover["uses"]},
                         {"posts/2026-10-06-book.md", "reviews/little-prince.md"})
        self.assertEqual(next(use["line"] for use in cover["uses"] if use["source"] == post["source"]), 7)
        with zipfile.ZipFile(self.output) as archive:
            archive.extractall(self.root / "expanded")
        exported = self.root / "expanded/posts" / post["filename"]
        for start, end in image_spans(text):
            self.assertEqual((exported.parent / unquote(text[start:end])).read_bytes(), PNG)
        self.assertTrue((exported.parent / "../reviews/little-prince.md").is_file())

    def test_work_card_code_comments_and_raw_examples_are_not_expanded(self):
        tag = '{% include work-card.html id="ghost" %}'
        examples = [f'`{tag}`', f'```liquid\n{tag}\n```', f'    {tag}\n',
                    f'<!-- {tag} -->', f'{{% raw %}}{tag}{{% endraw %}}',
                    f'{{%- comment -%}}{tag}{{%- endcomment -%}}']
        source = "\n\n".join(examples)
        _, contents, _ = self.export([self.post(source)])
        self.assertEqual(contents["posts/2026-10-06-book.md"].decode(), source)

    def test_work_card_whitespace_control_metadata_escaping_and_no_rating(self):
        tag = "{%- include work-card.html id = 'little-prince' -%}"
        work = self.work("Review", title="A [title] & <b>", rating=None)
        _, contents, _ = self.export([self.post(tag)], [work])
        text = contents["posts/2026-10-06-book.md"].decode()
        self.assertIn(r"A \[title\] &amp; &lt;b&gt;", text)
        self.assertNotIn("我的评分", text)
        self.assertNotIn("include", text)

    def test_work_card_zero_score_and_multiple_references(self):
        tags = '{% include work-card.html id="little-prince" %}\n{% include work-card.html id="second" %}'
        _, contents, _ = self.export([self.post(tags)], [
            self.work("Review", rating=0), self.work("Review", filename="second.md", work_id="second", rating=10)
        ])
        text = contents["posts/2026-10-06-book.md"].decode()
        self.assertIn("我的评分：0.0 / 10", text)
        self.assertIn("我的评分：10.0 / 10", text)
        self.assertIn("../reviews/second.md", text)

    def test_missing_and_dynamic_work_cards_fail_without_replacing_archive(self):
        self.export([self.post("Original")])
        previous = self.output.read_bytes()
        for tag, error in [('{% include work-card.html id="ghost" %}', "missing or unpublished"),
                           ('{% include work-card.html id=page.work %}', "literal-id")]:
            with self.subTest(tag=tag), self.assertRaisesRegex(ExportError, error):
                self.export([self.post(tag)])
            self.assertEqual(self.output.read_bytes(), previous)

    def test_work_include_images_cannot_be_silently_omitted(self):
        self.export([self.post("Original")])
        previous = self.output.read_bytes()
        work = self.work("{% include illustration.html %}", rendered_images=["/assets/cover.png"])
        with self.assertRaisesRegex(ExportError, "_works/little-prince.md.*no exportable Markdown reference"):
            self.export([], [work])
        self.assertEqual(self.output.read_bytes(), previous)

    def test_invalid_work_filename_is_rejected(self):
        with self.assertRaisesRegex(ExportError, "Invalid exported filename"):
            self.export([], [self.work("短评\n", filename="../evil.md")])


if __name__ == "__main__":
    unittest.main()
