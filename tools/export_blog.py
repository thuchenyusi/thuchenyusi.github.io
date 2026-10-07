#!/usr/bin/env python3
"""Create a self-contained Markdown ZIP using only Python's standard library."""

import argparse
import hashlib
import html
import json
import mimetypes
import re
import tempfile
import time
import unicodedata
import zipfile
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen


class ExportError(Exception):
    pass


def unescape_url(value):
    return html.unescape(re.sub(r"\\([\\`*{}\[\]()#+\-.!_>])", r"\1", value))


def mask_code(text):
    """Keep offsets intact while hiding comments, fenced and inline code."""
    chars = list(text)

    def hide(start, end):
        for index in range(start, end):
            if chars[index] not in "\r\n":
                chars[index] = " "

    fence = None
    indented = False
    previous_blank = True
    list_indent = None
    offset = 0
    for line in text.splitlines(keepends=True):
        effective = re.sub(r"^(?: {0,3}>[ \t]?)+", "", line)
        block_line = effective
        if list_indent and effective.startswith(" " * list_indent):
            block_line = effective[list_indent:]
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", block_line)
        if fence:
            hide(offset, offset + len(line))
            if match and match[1][0] == fence[0] and len(match[1]) >= fence[1]:
                if not block_line[match.end():].strip():
                    fence = None
        elif match:
            fence = (match[1][0], len(match[1]))
            hide(offset, offset + len(line))
        else:
            blank = not effective.strip()
            indentation = len(effective) - len(effective.lstrip(" "))
            code_indent = indentation >= 4 or effective.startswith("\t")
            if indented and (blank or code_indent):
                hide(offset, offset + len(line))
            else:
                indented = False
                if code_indent and previous_blank and list_indent is None:
                    hide(offset, offset + len(line))
                    indented = True
                else:
                    marker = re.match(r"^ {0,3}(?:[-+*]|\d+[.)])[ \t]+", effective)
                    if marker:
                        list_indent = marker.end()
                    elif not blank and list_indent is not None and indentation < list_indent:
                        list_indent = None
            previous_blank = blank
        offset += len(line)
    masked = "".join(chars)
    for match in re.finditer(r"<!--.*?-->|<(pre|code|script|style)\b[^>]*>.*?</\1\s*>",
                             masked, re.S | re.I):
        hide(*match.span())
    masked = "".join(chars)
    position = 0
    while match := re.search(r"`+", masked[position:]):
        start = position + match.start()
        token = match[0]
        closing = re.search(r"(?<!`)" + re.escape(token) + r"(?!`)",
                            masked[start + len(token):])
        if closing:
            end = start + len(token) + closing.end()
            hide(start, end)
            position = end
        else:
            position = start + len(token)
    return "".join(chars)


def destination(text, start):
    """Return the span of a Markdown destination, including balanced parentheses."""
    if start >= len(text):
        return None
    if text[start] == "<":
        end = start + 1
        while end < len(text) and text[end] not in ">\r\n":
            end += 2 if text[end] == "\\" else 1
        if end < len(text) and text[end] == ">":
            return start + 1, end, end + 1
        return None
    depth = 0
    end = start
    while end < len(text):
        char = text[end]
        if char == "\\":
            end += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                break
            depth -= 1
        elif char.isspace() and depth == 0:
            break
        end += 1
    return (start, end, end) if end > start and depth == 0 else None


def label(value):
    return " ".join(unescape_url(value).split()).casefold()


def image_spans(text):
    """Locate image URLs without changing ordinary links, prose or code samples.

    Supports inline/reference Markdown images and HTML img/source attributes.
    URLs are rewritten by offset, never by a global string replacement.
    """
    masked = mask_code(text)
    definitions = {}
    for match in re.finditer(r"^ {0,3}\[([^\]\n]+)\]:[ \t]*", masked, re.M):
        span = destination(masked, match.end())
        if span:
            definitions.setdefault(label(match[1]), span[:2])
    spans = set()
    for match in re.finditer(r"(?<!\\)!\[", masked):
        start = match.end()
        end = start
        depth = 1
        while end < len(masked) and depth:
            if masked[end] == "\\":
                end += 2
                continue
            if masked[end] == "[":
                depth += 1
            elif masked[end] == "]":
                depth -= 1
            end += 1
        if depth:
            continue
        alt = masked[start:end - 1]
        position = end
        while position < len(masked) and masked[position].isspace():
            position += 1
        if position < len(masked) and masked[position] == "(":
            position += 1
            while position < len(masked) and masked[position].isspace():
                position += 1
            span = destination(masked, position)
            if not span:
                raise ExportError("Unsupported or empty Markdown image destination")
            tail = masked[span[2]:]
            if not re.match(r"\s*(?:\"(?:\\.|[^\"])*\"|'(?:\\.|[^'])*'|\([^)]*\))?\s*\)", tail):
                raise ExportError("Malformed Markdown image destination")
            spans.add(span[:2])
        else:
            reference = alt
            if position < len(masked) and masked[position] == "[":
                close = masked.find("]", position + 1)
                if close < 0:
                    raise ExportError("Unclosed Markdown image reference")
                reference = masked[position + 1:close] or alt
            if label(reference) in definitions:
                spans.add(definitions[label(reference)])
            else:
                # An unresolved ![label] is plain text, not a Markdown image.
                continue
    tag_pattern = r"<(?:img|source)\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*>"
    attr_pattern = r"\b(src|data-src|srcset)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))"
    for tag in re.finditer(tag_pattern, masked, re.I):
        for attr in re.finditer(attr_pattern, tag[0], re.I):
            group = next(index for index in (2, 3, 4) if attr[index] is not None)
            start = tag.start() + attr.start(group)
            value = attr[group]
            if attr[1].lower() == "srcset":
                if "data:" in value:
                    raise ExportError("Use src rather than a data URI in srcset")
                for item in re.finditer(r"(?:^|,)\s*([^\s,]+)", value):
                    spans.add((start + item.start(1), start + item.end(1)))
            elif value:
                spans.add((start, start + len(value)))
    return sorted(spans)


def split_front_matter(markdown):
    match = re.match(r"\A---[ \t]*\r?\n.*?\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|$)", markdown, re.S)
    return (markdown[:match.end()], match.end()) if match else ("", 0)


def work_card_spans(markdown):
    """Locate literal card includes, preserving code/raw examples and offsets."""
    _, body_start = split_front_matter(markdown)
    body = markdown[body_start:]
    masked = mask_code(body)
    masked = re.sub(
        r"\{%-?\s*(raw|comment)\s*-?%\}.*?\{%-?\s*end\1\s*-?%\}",
        lambda match: re.sub(r"[^\r\n]", " ", match[0]), masked, flags=re.S
    )
    for match in re.finditer(r"\{%-?\s*include\s+work-card\.html\b(.*?)\s*-?%\}", masked, re.S):
        args = re.fullmatch(r"\s+id\s*=\s*([\"'])([a-z0-9][a-z0-9-]*)\1\s*", match[1])
        if not args:
            raise ExportError('Exportable work cards must use include work-card.html id="literal-id"')
        yield body_start + match.start(), body_start + match.end(), args[2]


def markdown_text(value):
    """Escape one-line metadata used as Markdown text (not as HTML)."""
    text = html.escape(" ".join(str(value).split()), quote=False)
    return re.sub(r"([\\`*{}\[\]()#!_|])", r"\\\1", text)


def front_image_span(front, expected):
    if not expected:
        return None
    image = re.search(r"^image:[ \t]*([^\r\n]*)", front, re.M)
    if not image:
        raise ExportError("Post image must be written explicitly in front matter")
    value_start, value_end = image.span(1)
    if not image[1].strip() or image[1].lstrip().startswith("#"):
        block = re.match(r"(?:[ \t]*\r?\n|[ \t]+[^\r\n]*\r?\n)*", front[image.end():])
        path = re.search(r"^[ \t]+path:[ \t]*([^\r\n]*)", block[0], re.M)
        if not path:
            raise ExportError("Post image must use a scalar URL or image.path")
        value_start = image.end() + path.start(1)
        value_end = image.end() + path.end(1)
    value = front[value_start:value_end].strip()
    value_start += len(front[value_start:value_end]) - len(front[value_start:value_end].lstrip())
    if value.startswith(('"', "'")):
        close = value.rfind(value[0])
        span = value_start + 1, value_start + close
    else:
        value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
        span = value_start, value_start + len(value)
    if unescape_url(front[slice(*span)]) != str(expected):
        raise ExportError("Unsupported YAML image value; use a plain quoted image URL")
    return span


def canonical_url(raw, config, media_subpath=""):
    raw = unescape_url(raw).strip()
    if "{{" in raw or "{%" in raw:
        raise ExportError("Image URLs must be explicit, without Liquid expressions")
    if raw.startswith("data:image/"):
        return raw
    if raw.startswith("//"):
        raw = "https:" + raw
    elif not urlsplit(raw).scheme:
        path = "/".join(part.strip("/") for part in (media_subpath, raw) if part)
        if config.get("cdn"):
            raw = config["cdn"].rstrip("/") + "/" + path
        else:
            raw = config["site_url"].rstrip("/") + config.get("baseurl", "").rstrip("/") + "/" + path
    parts = urlsplit(raw)
    if parts.scheme not in ("https", "http") or not parts.hostname or parts.username:
        raise ExportError(f"Unsupported image URL: {raw}")
    path = quote(parts.path, safe="/%:@!$&'()*+,;=-._~")
    query = quote(parts.query, safe="=&%/:?@!$'()*+,;~-._")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, parts.fragment))


def is_image(data, content_type):
    # Some S3 objects have application/octet-stream metadata: accept signatures.
    if content_type.startswith("image/"):
        return True
    return (data.startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"GIF87a", b"GIF89a", b"\x00\x00\x01\x00"))
            or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")
            or (data[4:8] == b"ftyp" and data[8:12] in (b"avif", b"avis"))
            or re.search(br"<svg\b", data[:1024]) is not None)


def archive_component(value):
    """Decode one URL segment, escaping names unsafe on Windows or in ZIPs."""
    value = unquote(value)
    escaped = "".join(
        quote(char, safe="") if char in '%<>:"/\\|?*' or ord(char) < 32 else char
        for char in value
    )
    # quote always leaves dots unescaped; handle trailing dots/spaces explicitly.
    escaped = re.sub(r"[ .]+$", lambda match: "".join(
        "%20" if char == " " else "%2E" for char in match[0]), escaped)
    if re.fullmatch(r"(?:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\..*)?", escaped, re.I):
        escaped = f"%{ord(escaped[0]):02X}" + escaped[1:]
    return escaped or "%00"


def with_url_hash(path, url, attempt=0):
    directory, _, filename = path.rpartition("/")
    suffix = Path(filename).suffix
    stem = filename[:-len(suffix)] if suffix else filename
    digest = hashlib.sha256(url.encode()).hexdigest()[:16]
    extra = f"-{attempt}" if attempt else ""
    return f"{directory}/{stem}-{digest}{extra}{suffix}"


def archive_image_path(url, content_type):
    parts = urlsplit(url)
    segments = parts.path.removeprefix("/").split("/")
    if not segments[-1]:
        segments[-1] = "image" + (mimetypes.guess_extension(content_type) or ".img")
    path = "images/" + archive_component(parts.netloc) + "/" + "/".join(
        archive_component(segment) for segment in segments
    )
    return with_url_hash(path, url) if parts.query else path


class Exporter:
    def __init__(self, config, site_dir, timeout=20, max_image_mb=32):
        self.config = config
        self.site_dir = Path(site_dir).resolve()
        self.timeout = timeout
        self.limit = max_image_mb * 1024 * 1024
        self.resources = {}
        self.works = {}
        for work in config.get("works", []):
            if work["id"] in self.works:
                raise ExportError(f"Duplicate exported work id: {work['id']}")
            self.works[work["id"]] = work

    def referenced_work(self, work_id):
        if work_id not in self.works:
            raise ExportError(f"Work card references a missing or unpublished work: {work_id}")
        return self.works[work_id]

    def work_card(self, entry, directory, start, work_id):
        work = self.referenced_work(work_id)
        title = markdown_text(work["title"])
        lines = [f"**[{title}](../reviews/{quote(work['filename'], safe='')})**"]
        if work.get("creator"):
            lines += ["", markdown_text(work["creator"])]
        if work.get("rating") is not None:
            lines += ["", f"我的评分：{work['rating']:.1f} / 10"]
        image = work.get("front_image")
        if image:
            path = self.add_image(image, self.entry_use(entry, directory, start), work.get("media_subpath", ""))
            if not path.startswith("data:image/"):
                path = "../" + quote(path, safe="/#")
            lines += ["", f"![{title}](<{path}>)"]
        return "\n\n" + "\n".join(lines) + "\n\n"

    def fetch(self, url):
        parts = urlsplit(url)
        origin = urlsplit(self.config["site_url"])
        baseurl = self.config.get("baseurl", "").rstrip("/")
        if parts.netloc == origin.netloc and (not baseurl or parts.path.startswith(baseurl + "/")):
            relative = unquote(parts.path[len(baseurl):]).lstrip("/")
            path = (self.site_dir / relative).resolve()
            if not path.is_relative_to(self.site_dir) or not path.is_file():
                raise ExportError(f"Missing local image: {relative}")
            if path.stat().st_size > self.limit:
                raise ExportError(f"Image exceeds size limit: {url}")
            data = path.read_bytes()
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        else:
            error = None
            for attempt in range(3):
                try:
                    request = Request(url, headers={"User-Agent": "Yiyouge-Markdown-Export/1.0"})
                    with urlopen(request, timeout=self.timeout) as response:
                        content_type = response.headers.get_content_type()
                        data = response.read(self.limit + 1)
                    break
                except (OSError, ValueError) as exc:
                    error = exc
                    if attempt < 2:
                        time.sleep(0.5 * (attempt + 1))
            else:
                raise ExportError(f"Unable to download {url}: {error}") from error
        if not data or len(data) > self.limit or not is_image(data, content_type):
            raise ExportError(f"Empty, oversized or non-image response: {url}")
        return data, content_type

    def add_image(self, raw, use, media_subpath=""):
        url = canonical_url(raw, self.config, media_subpath)
        if url.startswith("data:image/"):
            return url  # Already embedded and usable offline.
        parts = urlsplit(url)
        resource_url = urlunsplit(parts._replace(fragment=""))
        if resource_url not in self.resources:
            data, content_type = self.fetch(resource_url)
            self.resources[resource_url] = {
                "path": archive_image_path(resource_url, content_type),
                "data": data,
                "content_type": content_type,
                "sha256": hashlib.sha256(data).hexdigest(),
                "uses": []
            }
        resource = self.resources[resource_url]
        entry = dict(use)
        # The parent record already identifies the downloaded URL. Preserve a
        # source spelling only when it differs (relative paths, entities, etc.).
        if raw != resource_url:
            entry["reference"] = raw
        if entry not in resource["uses"]:
            resource["uses"].append(entry)
        return resource["path"] + ("#" + parts.fragment if parts.fragment else "")

    def assign_image_paths(self):
        """Preserve URL paths, resolving file and directory collisions portably."""
        originals = {url: archive_image_path(url, resource["content_type"])
                     for url, resource in self.resources.items()}
        paths = dict(originals)
        attempt = 0
        while True:
            groups = {}
            directories = set()
            for url, path in paths.items():
                key = unicodedata.normalize("NFC", path).casefold()
                groups.setdefault(key, []).append(url)
                components = key.split("/")
                directories.update("/".join(components[:index]) for index in range(1, len(components)))
            conflicts = {url for key, urls in groups.items()
                         if len(urls) > 1 or key in directories for url in urls}
            if not conflicts:
                break
            for url in conflicts:
                paths[url] = with_url_hash(originals[url], url, attempt)
            attempt += 1
        for url, path in paths.items():
            self.resources[url]["path"] = path

    @staticmethod
    def entry_spans(entry):
        markdown = entry["markdown"]
        front, body_start = split_front_matter(markdown)
        spans = [(a + body_start, b + body_start) for a, b in image_spans(markdown[body_start:])]
        front_span = front_image_span(front, entry.get("front_image"))
        if front_span:
            spans.append(front_span)
        return sorted(set(spans))

    @staticmethod
    def entry_use(entry, directory, start):
        return {
            "source": entry["source"],
            "markdown": directory + "/" + entry["filename"],
            "line": entry["markdown"].count("\n", 0, start) + 1
        }

    def rewrite_entry(self, entry, directory):
        markdown = entry["markdown"]
        replacements = []
        entry_images = set()
        for start, end in self.entry_spans(entry):
            raw = markdown[start:end]
            local = self.add_image(raw, self.entry_use(entry, directory, start), entry.get("media_subpath", ""))
            if not local.startswith("data:image/"):
                resolved = canonical_url(raw, self.config, entry.get("media_subpath", ""))
                entry_images.add(urlunsplit(urlsplit(resolved)._replace(fragment="")))
                replacements.append((start, end, "../" + quote(local, safe="/#")))
        for start, end, work_id in work_card_spans(markdown):
            replacements.append((start, end, self.work_card(entry, directory, start, work_id)))
            work = self.referenced_work(work_id)
            if work.get("front_image"):
                resolved = canonical_url(work["front_image"], self.config, work.get("media_subpath", ""))
                entry_images.add(urlunsplit(urlsplit(resolved)._replace(fragment="")))
        for start, end, replacement in sorted(replacements, reverse=True):
            markdown = markdown[:start] + replacement + markdown[end:]
        for rendered in entry.get("rendered_images", []):
            if rendered.startswith("data:image/"):
                continue
            absolute = urljoin(self.config["site_url"].rstrip("/") + "/", html.unescape(rendered))
            required = urlsplit(canonical_url(absolute, self.config))._replace(fragment="")
            if urlunsplit(required) not in entry_images:
                raise ExportError(f"Image in {entry['source']} has no exportable Markdown reference: {rendered}")
        return markdown

    def write(self, output):
        collections = (("posts", self.config["posts"]), ("reviews", self.config.get("works", [])))
        entries = {}
        for directory, records in collections:
            for record in records:
                filename = record["filename"]
                if Path(filename).name != filename or not filename.endswith((".md", ".markdown")):
                    raise ExportError(f"Invalid exported filename: {filename}")
                path = directory + "/" + filename
                if path in entries:
                    raise ExportError(f"Duplicate exported filename: {filename}")
                entries[path] = None
                for start, end in self.entry_spans(record):
                    self.add_image(record["markdown"][start:end], self.entry_use(record, directory, start),
                                   record.get("media_subpath", ""))
                for start, _, work_id in work_card_spans(record["markdown"]):
                    work = self.referenced_work(work_id)
                    if work.get("front_image"):
                        self.add_image(work["front_image"], self.entry_use(record, directory, start),
                                       work.get("media_subpath", ""))
        for image in self.config["site_images"]:
            self.add_image(image["url"], {"role": image["role"]})
        self.assign_image_paths()
        for directory, records in collections:
            for record in records:
                entries[directory + "/" + record["filename"]] = self.rewrite_entry(record, directory)
        site_images = []
        for image in self.config["site_images"]:
            path = self.add_image(image["url"], {"role": image["role"]})
            site_images.append({"role": image["role"], "path": path})
        manifest = {
            "schema_version": 4,
            "generated_at": self.config["generated_at"],
            "site_url": self.config["site_url"],
            "posts": [{key: post[key] for key in ("source", "filename", "title", "url")}
                      for post in self.config["posts"]],
            "works": [{key: work[key] for key in ("id", "source", "filename", "title", "url")}
                      for work in self.config.get("works", [])],
            "site_images": site_images,
            "images": [{"url": url, **{key: value for key, value in resource.items() if key != "data"}}
                       for url, resource in sorted(self.resources.items())]
        }
        readme = [f"# {self.config['title']}：Markdown 导出", "",
                  f"导出时间：{self.config['generated_at']}", "",
                  "解压整个 ZIP，保留 posts、reviews 与 images 的相对位置。用支持 Markdown 的阅读器打开 posts 中的文章、reviews 中的作品记录即可。",
                  "所有图片按原 URL 保存到 images/<域名>/<原始路径>，同一 URL 只保存一份，不按文章或用途分类。",
                  "Markdown 已使用相对路径引用图片；普通外部链接仍需联网访问。",
                  "此包包含已发布文章、公开作品记录和引用到的图片，不包含草稿、未公开作品、网站运行依赖或未引用的原始图片。",
                  "manifest.json 记录原图片地址、使用位置与 SHA-256，可用于校验和恢复云端对象。", "",
                  "## 网站图片", ""]
        for image in site_images:
            role = {"avatar": "头像", "sidebar_background": "侧栏背景"}.get(image["role"], image["role"])
            readme.append(f"![{role}]({quote(image['path'], safe='/')})")
        readme += ["", "## 文章", ""]
        for post in self.config["posts"]:
            title = re.sub(r"([\[\]\\])", r"\\\1", post["title"]).replace("\n", " ")
            readme.append(f"- [{title}](posts/{quote(post['filename'])})")
        works = self.config.get("works", [])
        if works:
            readme += ["", "## 作品", ""]
            for work in works:
                title = re.sub(r"([\[\]\\])", r"\\\1", work["title"]).replace("\n", " ")
                readme.append(f"- [{title}](reviews/{quote(work['filename'])})")
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        # Atomically replace only after all downloads and ZIP integrity checks pass.
        with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".zip", delete=False) as handle:
            temporary = Path(handle.name)
        try:
            with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
                for path, content in entries.items():
                    archive.writestr(path, content)
                for resource in self.resources.values():
                    archive.writestr(resource["path"], resource["data"])
                archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
                archive.writestr("README.md", "\n".join(readme) + "\n")
            with zipfile.ZipFile(temporary) as archive:
                if archive.testzip():
                    raise ExportError("ZIP integrity check failed")
            temporary.replace(output)
        finally:
            temporary.unlink(missing_ok=True)
        return len(self.config["posts"]), len(works), len(self.resources)


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=root / ".jekyll-cache/blog-export.json")
    parser.add_argument("--site-dir", type=Path, default=root / "_site")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--max-image-mb", type=int, default=32)
    args = parser.parse_args()
    try:
        config = json.loads(args.input.read_text(encoding="utf-8"))
        if config.get("schema_version") != 3:
            raise ExportError("Unsupported export input version")
        if config.get("enabled") is False:
            print("Markdown export is disabled in _config.yml")
            return
        if args.timeout < 1 or args.max_image_mb < 1:
            raise ExportError("Timeout and image size limit must be positive")
        output = args.output or args.site_dir / "downloads/blog-markdown.zip"
        posts, works, images = Exporter(config, args.site_dir, args.timeout, args.max_image_mb).write(output)
    except (ExportError, OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Markdown export failed: {exc}\n")
    print(f"Exported {posts} posts, {works} works and {images} images to {output}")


if __name__ == "__main__":
    main()
