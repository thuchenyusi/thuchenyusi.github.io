# frozen_string_literal: true

require "jekyll"
require "tmpdir"
require "json"

# Exercise the real Jekyll collection, even with private content enabled locally.
Dir.mktmpdir("blog-export-input") do |root|
  FileUtils.mkdir_p(%w[_posts _drafts _plugins].map { |directory| File.join(root, directory) })
  plugin = File.expand_path("../_plugins/blog-export-input.rb", __dir__)
  FileUtils.cp(plugin, File.join(root, "_plugins", "blog-export-input.rb"))
  File.write(File.join(root, "_posts", "2020-01-01-public.md"), "---\ntitle: Public\n---\nPublic text\n")
  File.write(File.join(root, "_posts", "2020-01-02-hidden.md"),
             "---\ntitle: Hidden\npublished: false\n---\nPRIVATE_MARKER\n")
  File.write(File.join(root, "_posts", "2099-01-01-future.md"), "---\ntitle: Future\n---\nPRIVATE_MARKER\n")
  draft = File.join(root, "_drafts", "draft.md")
  File.write(draft, "---\ntitle: Draft\n---\nPRIVATE_MARKER\n")
  File.utime(Time.utc(2020), Time.utc(2020), draft)

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
    "blog_export" => { "enabled" => true }
  )
  site = Jekyll::Site.new(configuration)
  site.process
  abort "Fixture did not load private posts" unless site.posts.docs.size == 4
  path = File.join(root, ".jekyll-cache", "blog-export.json")
  input = JSON.parse(File.read(path))
  filenames = input.fetch("posts").map { |post| post.fetch("filename") }
  abort "Private posts leaked: #{filenames.inspect}" unless filenames == ["2020-01-01-public.md"]
  abort "Private text leaked" if File.read(path).include?("PRIVATE_MARKER")
  abort "Export input was published" if File.exist?(File.join(root, "_site", "blog-export.json"))

  site.config["blog_export"]["enabled"] = false
  Jekyll::Hooks.trigger(:site, :post_write, site)
  abort "Disabled state was not recorded" unless JSON.parse(File.read(path))["enabled"] == false
end

puts "Verified published-only export input with drafts, unpublished and future posts enabled."
