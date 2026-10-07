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

## 鉴赏栏目

`/reviews/` 按书籍、电影、动画、游戏展示封面墙，点击作品展开详情与评论。
作品也有独立页面 `/reviews/<id>/`。没有记录时显示「暂无记录」。

每件作品保存在 `_works/<id>.md`：YAML front matter 保存作品信息，Markdown
正文保存个人评论。下面仅为填写模板，封面需替换为已上传到 AWS S3 的公开地址：

~~~markdown
---
id: example-work
type: book
title: 作品名
author: 作者名
image: https://image.yurich.me/books/example-work/cover.webp
rating: 8.5
status: done
reviewed_at: "2026-01-01"
---

这里填写个人评论。
~~~

| 字段 | 约定 |
| --- | --- |
| `id` | 必填、唯一，与文件名一致；以小写字母或数字开头，只含小写字母、数字和连字符 |
| `type` | 必填：`book`、`movie`、`anime`、`game` |
| `title` | 必填，作品名 |
| `status` | 必填：`wish`、`doing`、`done`、`dropped`；按作品类型显示中文文案 |
| `rating` | 可选，0 到 10 的数字，步长 0.5；未评分可省略或填 `null`，页面统一显示如 `8.5 / 10` |
| `image` | 可选，显式公开图片 URL；沿用 `https://image.yurich.me/`，不使用临时签名地址 |
| `reviewed_at` | 可选，原评论日期，格式为 `YYYY-MM-DD`；封面墙按日期倒序，未填的排在最后 |
| `published` | 可选，`false` 表示不公开，不进入公开页面、搜索或导出包 |
| `links` | 可选映射，键为 `douban` / `bangumi`，值为对应作品的条目 URL |

可补充书籍的 `author`、`translator`、`publisher`、`isbn`，电影或动画的
`director`，游戏的 `developer`，以及通用的 `year`、`tags`。
`review_post` 可链接已发布的长评文章。缺少的元数据不展示。

封面沿用现有 S3 分类路径与原文件名；更换图片内容时使用新文件名。
记录目前手工维护，尚无平台导入或同步工具。

文章引用作品时，先在文章 front matter 中声明稳定 ID：

~~~yaml
works:
  - example-work
~~~

再在正文需要的位置插入卡片：

~~~liquid
{% include work-card.html id="example-work" %}
~~~

卡片读取作品文件中的标题、封面和当前个人评分，点击进入作品独立页面。
构建会校验作品字段与引用关系；引用的作品必须存在且已公开。
栏目框架不附带作品或文章样例，`_works/` 可以不存在或为空。

## Theme maintenance

The site uses the Chirpy 7.6 gem (locked to 7.6.0), including its layouts, scripts,
styles and translations. Keep theme files in the gem instead of copying them
into this repository: local copies override updates from the gem.

Site additions use the metadata hook, existing favicons, custom CSS,
Sakana/sakura widgets, additional locale tab labels and review collection
templates/scripts. The review layout extends the theme's page layout.
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
bundle exec ruby tools/test_works_validation.rb
bundle exec ruby tools/check_site.rb
~~~

For future theme updates, update Gemfile and Gemfile.lock, compare the upstream
_config.yml and static-assets revision, then repeat these checks. Pull requests
build and check the site; only the default branch deploys to GitHub Pages.

The footer's **导出全站** link downloads published Markdown posts, public work
records and their images as a ZIP with local relative image paths. The deployment
builds this archive automatically. See [docs/blog-export.md](docs/blog-export.md) for the
archive layout, image conventions and local export commands. Python 3.10+ is
required to generate the archive; reading it only needs a Markdown reader.

Known pre-existing content issue: the C and C++ tags both resolve to /tags/c/,
so Jekyll reports a duplicate archive destination.
