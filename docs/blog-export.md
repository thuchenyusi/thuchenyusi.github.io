# 博客 Markdown 与图片导出

## 范围与入口

正文底部页脚中，主题说明下方的「导出全站」文字链接下载一个 ZIP，包含所有已发布文章的 Markdown、文章
引用的图片、头像、侧栏背景和显式配置的附加图片。它保存的是部署时的
快照，不是点击时重新抓取 S3。不会导出草稿、未来文章、未引用的原图、
HTML、JS 或字体。普通豆瓣等外部链接保持原样。桌面端链接与主题说明右对齐，
移动端跟随页脚居中显示，不占用侧栏导航。链接说明标明 Markdown 和图片范围。

GitHub Pages 是静态托管。构建时下载图片并生成 ZIP，按钮下载同源文件，
因此不需要浏览器跨域请求图片、S3 密钥或新增后端。每次部署更新导出包；
仅浏览博客不会创建本地备份，需要点击下载并保留文件。

## 图片链接的维护约定

- 推荐普通 Markdown：`![封面](https://image.yurich.me/books/文章标识/cover.webp)`。
  游戏截图使用 `games/文章标识/截图文件名.webp`。更换图片内容使用新文件名。
- 文章图片以正文链接及 front matter 的 `image` / `image.path` 为准，不另设
  一份手工维护的图片列表。支持行内图片、引用式图片及 HTML `img` 的
  `src` / `data-src`、`img` / `source` 的 `srcset`。
- 推荐显式 URL，不要把图片链接藏在 Liquid include、JavaScript 或 CSS 中。
  URL 内的 Liquid 表达式会导致导出失败；网页可显示并不代表 Markdown
  本身能离线显示。需要新增图片语法时，应先扩展导出器与测试。
- 本地图片和 `media_subpath`、`site.cdn` 的组合按 Chirpy 7.6 的媒体地址规则
  解析；配置非空 baseurl 时也必须保证导出测试覆盖。
- 头像统一放在 `_config.yml` 的 `avatar`；背景统一放在 `sidebar_background`，
  SCSS 读取这个配置。不要在 CSS 中另写第二份背景 URL。
- 其他共享图片可放到 `blog_export.extra_images`。只允许公开图片地址，
  不要使用临时签名 URL 或把访问密钥写进图片链接。

## ZIP 布局与引用关系

```text
blog-markdown-YYYY-MM-DD.zip
├─ README.md
├─ manifest.json
├─ posts/
│  └─ 2022-09-07-detective-fiction-list.md
└─ images/
   └─ image.yurich.me/
      ├─ anime/
      │  ├─ avatar/mayuri.jpg
      │  └─ sidebar/明石さん_しち.png
      └─ books/原URL中的目录/cover.webp
```

保留文章原文件名，避免不同文章重名。所有图片统一按
`images/<域名>/<原始URL路径>` 保存，不根据所属文章或头像、背景等用途重新
分类。上述目录仅是例子：实际结构以原 URL 为准。同一 URL 在同一 ZIP 中
只保存一次，新增引用文章不会改变其目录。不同 SVG fragment 共用文件但
保留 fragment。

普通图片保留原文件名与大小写，中文路径解码一次，Markdown 引用按 URI 编码。
有查询参数的图片在文件名中追加完整 URL 的稳定短哈希；大小写、协议等导致
文件冲突时也追加哈希，避免解压到 Windows 时覆盖。文件与目录同名冲突同样
处理。Windows 禁用字符、保留名称、尾部空格或点和路径中的 `.` / `..` 用
百分号编码保存；编码的斜杠不会变成目录分隔符。无文件名的地址使用
`image` 加 MIME 类型推导的扩展名。实际映射始终记录在清单中。

`posts/` 中的 Markdown 图片 URL 替换为
`../images/image.yurich.me/books/原URL中的目录/cover.webp`。按源文本位置
替换，不能全局替换字符串，避免改动普通链接和代码示例。引用式图片只
重写其定义；如果普通链接共用同一定义，它也指向同一张本地图片。

`manifest.json` 的输出版本为 3，包含导出时间、文章源路径、线上文章地址、原图片 URL、本地
图片路径、引用文章与行号、网站图片角色、Content-Type 和 SHA-256。行号
仅用于定位当次快照，恢复时应以原 URL 和对象路径为准。查询参数保留在
原 URL 中，恢复 S3 时不能把它误当成对象名。URI 路径应解码一次。

每个图片记录只在顶层保存一次 `url`。`uses` 只描述角色或文章位置；源文本
使用相对路径、不同编码或 fragment 等不同写法时，额外保存 `reference`。
源文本与顶层 URL 相同则省略，不重复保存相同地址。

下载后解压整个 ZIP，用 Markdown 阅读器打开文章；不要只移动 `posts/`。
`README.md` 提供文章目录，并展示已导出的头像、背景等共享图片。
ZIP 不依赖 Jekyll、Python 或本地 HTTP 服务器来阅读。

## 实现与构建

1. `_plugins/blog-export-input.rb` 根据 Jekyll 发布文章集合生成私有输入
   `.jekyll-cache/blog-export.json`，不使用 `_posts` 文件遍历，也不发布该输入。
2. `tools/export_blog.py` 使用 Python 标准库解析并替换图片引用、读取本地
   图片或下载远程图片、生成清单与 ZIP。
3. `_includes/metadata-hook.html` 和 `assets/js/blog-export.js` 将下载链接
   插入页脚主题说明下方，避免复制和覆盖整个主题布局。
4. 部署工作流先构建、生成 ZIP、运行测试，再检查本地引用并上传网站。

```sh
JEKYLL_ENV=production bundle exec jekyll build
python tools/export_blog.py
python -B -m unittest discover -s tools/tests -p 'test_*.py'
bundle exec ruby tools/test_blog_export_input.rb
bundle exec ruby tools/check_site.rb
```

输出为 `_site/downloads/blog-markdown.zip`。本地备份放到自行选择的仓库外
目录，不新增仓库内备份目录或相应的 `.gitignore` 规则。例如：

```sh
python tools/export_blog.py --output D:/backup/blog/blog-markdown-2026-10-06.zip
```

Windows PowerShell 用 `$env:JEKYLL_ENV = 'production'` 设置构建环境。
Python 需要 3.10 或以上。Jekyll 开发服务器不会自动运行 Python 导出步骤；
测试按钮前需执行该步骤，部署工作流则会自动执行。

## 失败处理与验证

远程下载使用超时和重试；默认单张图片上限 32 MB，可通过
`--max-image-mb` 调整。空文件、非图片响应、缺失文件或下载失败都会让导出
失败。不会静默跳过图片，也不会用残缺 ZIP 覆盖上一份成功导出。
还会核对文章实际渲染的图片；如果 Liquid include 等产生了无法在 Markdown
中定位的图片，导出会报错，要求先采用可导出的图片写法。
构建失败会阻止本次部署，线上上一份成功的部署继续保留。

测试必须覆盖：相对路径在解压后能找到文件、共享图片去重、同名 URL 冲突、
引用式图片与 HTML 图片、代码示例和普通链接不被误改、封面元数据、中文
URL、CDN/baseurl/media_subpath、下载失败不覆盖旧包及发布集合不泄露草稿。
增加新图片用法时同步补充样例。手动验证应解压包并在断网后打开 Markdown。

这是公开下载包，只包含可公开发布的内容。导出包能恢复已发布图片，但不
包含 Git 历史、站点完整源代码或没有上传过的高清原图。保留这些内容仍依靠
现有代码仓库及原图保存方式。
