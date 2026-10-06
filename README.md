# thuchenyusi.github.io

![Automatic build](https://github.com/thuchenyusi/thuchenyusi.github.io/actions/workflows/pages-deploy.yml/badge.svg)
[![LICENSE](https://img.shields.io/github/license/thuchenyusi/thuchenyusi.github.io.svg)](https://github.com/thuchenyusi/thuchenyusi.github.io/blob/main/LICENSE)

My Personal blog | Made With Jekyll

## Address

- https://blog.yurich.me

## Acknowledgements

- Thanks [Jekyll](https://jekyllrb.com/) for its blog generator.
- Thanks [chirpy](https://github.com/cotes2020/jekyll-theme-chirpy) for its blog theme.
- Thanks [しち](https://www.pixiv.net/users/4313649) for hir [illustration](https://www.pixiv.net/artworks/43254374).
- Thanks [トトロ](https://github.com/itorr) and [大伏アオ](https://twitter.com/blue00f4) for the [「Sakana!」](https://github.com/itorr/sakana).

## License

Except where otherwise noted, the files in project are licensed under MIT.
## Theme maintenance

The site uses the Chirpy 7.6 gem (locked to 7.6.0), including its layouts, scripts,
styles and translations. Keep theme files in the gem instead of copying them
into this repository: local copies override updates from the gem.

Site overrides are limited to the metadata hook, the existing favicons,
custom CSS, the Sakana/sakura widgets and additional locale tab labels.
The assets/lib submodule matches Chirpy v7.6.0
(5cde3f0076b62e45fc68291893cf7d93e122adb7).
The small /sw.js bridge upgrades visitors with a Chirpy 5 service worker.

Use Ruby 3.4, initialize submodules, and run:

~~~sh
git submodule update --init
bundle install
JEKYLL_ENV=production bundle exec jekyll build
python tools/export_blog.py
python -B -m unittest discover -s tools/tests -p 'test_*.py'
bundle exec ruby tools/test_blog_export_input.rb
bundle exec ruby tools/check_site.rb
~~~

For future theme updates, update Gemfile and Gemfile.lock, compare the upstream
_config.yml and static-assets revision, then repeat these checks. Pull requests
build and check the site; only the default branch deploys to GitHub Pages.

The footer's **导出全站** link downloads published Markdown posts and their
images as a ZIP with local relative image paths. The deployment builds this
archive automatically. See [docs/blog-export.md](docs/blog-export.md) for the
archive layout, image conventions and local export commands. Python 3.10+ is
required to generate the archive; reading it only needs a Markdown reader.

Known pre-existing content issue: the C and C++ tags both resolve to /tags/c/,
so Jekyll reports a duplicate archive destination.
