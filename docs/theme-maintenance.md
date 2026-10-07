# Theme maintenance

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

## Archive slugs

Tag and category archive links use the same `pretty` slug mode as
`jekyll-archives`. `_plugins/archive-slug-collision-check.rb` keeps the theme's
Liquid links aligned with the generated archive paths and fails the build when
two archive names produce the same slug. For example, `C` and `C++` generate
`/tags/c/` and `/tags/c++/`, while `C#` still collides with `C` in `pretty`
mode.

Before using a `C#` tag in a post, add an explicit `C#` to `csharp` slug mapping
and apply it to both Liquid link generation and `jekyll-archives` page
generation. The repository does not currently provide a mapping configuration,
so implement and test that support before publishing the tag. Do not disable
the collision check or change the visible tag name merely to make the build
pass.

## Sakana version maintenance

The metadata hook loads `html/sakana.min.js` from the `thuchenyusi/sakana`
fork through jsDelivr. `_config.yml` records the repository in
`sakana.repository` and pins its complete commit SHA in `sakana.revision`.
Updating the fork alone does not change the version used by the blog.

To upgrade, sync the fork and confirm that the selected commit contains the
updated `html/sakana.min.js` build, then replace `sakana.revision` with that
commit's complete SHA. Verify the exact CDN URL returns the expected script,
run the checks above, and deploy the blog. To roll back, restore the previous
SHA and deploy again. Keep published tags unchanged if using a tag instead.

`assets/js/sakana/sakana_init.js` and `_includes/sakana.html` remain local.
They provide the mobile breakpoint, scale, deferred initialization, expansion
state and collapse controls. Keep the deferred core script before the deferred
initialization script. After an upgrade, verify desktop dragging and character
switching, plus mobile expansion, dragging, switching, outside-click collapse,
saved expansion state and viewport changes. The site checker only checks local
resource references; CDN availability and widget behavior need separate checks.

## Markdown export

The footer's **导出全站** link downloads published Markdown posts, public work
records and their images as a ZIP with local relative image paths. The deployment
builds this archive automatically. See [blog-export.md](blog-export.md) for the
archive layout, image conventions and local export commands. Python 3.10+ is
required to generate the archive; reading it only needs a Markdown reader.
