# frozen_string_literal: true

require "jekyll"
require "tmpdir"
require "json"

# Exercise the real Jekyll collection, even with private content enabled locally.
Dir.mktmpdir("blog-export-input") do |root|
  FileUtils.mkdir_p(%w[_posts _drafts _works _plugins _includes _layouts].map { |directory| File.join(root, directory) })
  plugin = File.expand_path("../_plugins/blog-export-input.rb", __dir__)
  FileUtils.cp(plugin, File.join(root, "_plugins", "blog-export-input.rb"))
  File.write(File.join(root, "_layouts", "page.html"), '<main><article>{{ content }}</article></main>')
  File.write(File.join(root, "_includes", "illustration.html"),
             '<picture><source srcset="/assets/include-2x.png 2x, /assets/include-3x.png 3x"><img src="/assets/include-only.png" data-src="/assets/deferred.png"></picture>')
  File.write(File.join(root, "_includes", "work-card.html"),
             '<img class="work-card-cover" src="https://image.example.com/cover.webp">')
  File.write(File.join(root, "_posts", "2020-01-01-public.md"),
             "---\ntitle: Public\nlayout: page\n---\nPublic text\n{% include work-card.html id=\"little-prince\" %}\n")
  File.write(File.join(root, "_posts", "2020-01-02-hidden.md"),
             "---\ntitle: Hidden\npublished: false\n---\nPRIVATE_MARKER\n")
  File.write(File.join(root, "_posts", "2099-01-01-future.md"), "---\ntitle: Future\n---\nPRIVATE_MARKER\n")
  draft = File.join(root, "_drafts", "draft.md")
  File.write(draft, "---\ntitle: Draft\n---\nPRIVATE_MARKER\n")
  File.utime(Time.utc(2020), Time.utc(2020), draft)
  File.write(File.join(root, "_works", "little-prince.md"),
             "---\nid: little-prince\ntitle: 小王子\nlayout: page\nauthor: Author\nrating: 8.5\nimage: https://image.example.com/cover.webp\n---\n短评\n{% include illustration.html %}\n")
  File.write(File.join(root, "_works", "hidden-work.md"),
             "---\nid: hidden-work\ntitle: Hidden Work\npublished: false\n---\nPRIVATE_MARKER\n")

  configuration = Jekyll.configuration(
    "skip_config_files" => true,
    "source" => root,
    "destination" => File.join(root, "_site"),
    "theme" => nil,
    "plugins" => [],
    "plugins_dir" => "_plugins",
    "url" => "https://blog.example.com",
    "time" => Time.utc(2026, 10, 6),
    "future" => true,
    "unpublished" => true,
    "show_drafts" => true,
    "collections" => { "works" => { "output" => true } },
    "blog_export" => { "enabled" => true }
  )
  site = Jekyll::Site.new(configuration)
  site.process
  abort "Fixture did not load private posts" unless site.posts.docs.size == 4
  path = File.join(root, ".jekyll-cache", "blog-export.json")
  input = JSON.parse(File.read(path))
  abort "Export input version was not bumped" unless input.fetch("schema_version") == 3
  filenames = input.fetch("posts").map { |post| post.fetch("filename") }
  abort "Private posts leaked: #{filenames.inspect}" unless filenames == ["2020-01-01-public.md"]
  works = input.fetch("works")
  abort "Private works leaked: #{works.inspect}" unless works.map { |work| work.fetch("id") } == ["little-prince"]
  work = works.first
  abort "Work fields missing" unless work["front_image"] == "https://image.example.com/cover.webp" &&
    work["source"] == "_works/little-prince.md" && work["markdown"].include?("短评") &&
    work["creator"] == "Author" && work["rating"] == 8.5
  abort "Work include-only images were not checked" unless work["rendered_images"] ==
    ["/assets/include-2x.png", "/assets/include-3x.png", "/assets/include-only.png", "/assets/deferred.png"]
  abort "Post card cover bypassed image checks" unless input["posts"].first["rendered_images"] == ["https://image.example.com/cover.webp"]
  abort "Private text leaked" if File.read(path).include?("PRIVATE_MARKER")
  abort "Export input was published" if File.exist?(File.join(root, "_site", "blog-export.json"))

  site.config["blog_export"]["enabled"] = false
  Jekyll::Hooks.trigger(:site, :post_write, site)
  abort "Disabled state was not recorded" unless JSON.parse(File.read(path))["enabled"] == false
end

puts "Verified published-only export input with drafts, unpublished and future posts enabled."
