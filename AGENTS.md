# Repository guidance

- Keep Chirpy layouts and core assets in the theme gem; use the existing metadata
  hook and custom CSS for site additions.
- Before changing image URLs, site image configuration, Markdown processing,
  build/deploy steps or the export button, read [docs/blog-export.md](docs/blog-export.md).
  The Markdown export is a supported feature: published posts and their images
  must remain readable together after extracting the ZIP.
- Preserve the `posts/`, `images/<domain>/<original URL path>/`,
  `manifest.json`, `README.md` archive contract. Keep identical URLs deduplicated
  and preserve original filenames; add URL hashes only for queries or collisions.
  Update the export tests and documentation when changing the contract.
- Run the production build, `python tools/export_blog.py`, the export unit tests,
  and `bundle exec ruby tools/check_site.rb` for changes affecting this feature.
  Never publish an archive with silently omitted images or export drafts.
- Do not commit generated ZIPs, image downloads, `.jekyll-cache` or `_site`.
