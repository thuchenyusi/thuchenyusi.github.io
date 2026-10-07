# frozen_string_literal: true

require "jekyll"
require "tmpdir"
require "fileutils"

# The validation plugin must fail the build on invalid works records or dangling
# post references, and normalize unquoted YAML dates for the wall's grouping.
def build_site(root)
  configuration = Jekyll.configuration(
    "skip_config_files" => true,
    "source" => root,
    "destination" => File.join(root, "_site"),
    "theme" => nil,
    "plugins" => [],
    "plugins_dir" => "_plugins",
    "url" => "https://blog.example.com",
    "collections" => { "works" => { "output" => true } }
  )
  site = Jekyll::Site.new(configuration)
  site.process
  site
end

def fixture_root
  root = Dir.mktmpdir("works-validation")
  FileUtils.mkdir_p(%w[_posts _works _plugins _includes].map { |directory| File.join(root, directory) })
  plugin = File.expand_path("../_plugins/works-validation.rb", __dir__)
  FileUtils.cp(plugin, File.join(root, "_plugins", "works-validation.rb"))
  include_file = File.expand_path("../_includes/work-card.html", __dir__)
  FileUtils.cp(include_file, File.join(root, "_includes", "work-card.html"))
  root
end

def write_work(root, name, front_matter)
  File.write(File.join(root, "_works", name), front_matter + "---\n短评\n")
end

valid_work = <<~YAML
  ---
  id: little-prince
  type: book
  title: 小王子
  image: https://image.example.com/cover.webp
  rating: 8.5
  status: done
  reviewed_at: 2026-09-18
  links:
    douban: https://book.douban.com/subject/1084336/
  ---
YAML

failures = {
  "invalid rating" => valid_work.sub("rating: 8.5", "rating: 8.4"),
  "rating out of range" => valid_work.sub("rating: 8.5", "rating: 11"),
  "unknown type" => valid_work.sub("type: book", "type: podcast"),
  "unknown status" => valid_work.sub("status: done", "status: finished"),
  "mismatched id" => valid_work.sub("id: little-prince", "id: other"),
  "bad reviewed_at" => valid_work.sub("reviewed_at: 2026-09-18", "reviewed_at: last week"),
  "local image url" => valid_work.sub("image: https://image.example.com/cover.webp", "image: /local/cover.webp"),
  "signed image url" => valid_work.sub("cover.webp", "cover.webp?X-Amz-Signature=example&X-Amz-Expires=60"),
  "encoded signed image url" => valid_work.sub("cover.webp", "cover.webp?%58-Amz-SiGnAtUrE=example"),
  "legacy signed image url" => valid_work.sub("cover.webp", "cover.webp?AWSAccessKeyId=example&Signature=example"),
  "malformed image url" => valid_work.sub("https://image.example.com/cover.webp", "https://"),
  "image credentials" => valid_work.sub("https://image.example.com/cover.webp", "https://user:password@image.example.com/cover.webp"),
  "unknown link key" => valid_work.sub("douban:", "weibo:")
}

failures.each do |name, front_matter|
  root = fixture_root
  write_work(root, "little-prince.md", front_matter)
  begin
    build_site(root)
    abort "#{name}: build should have failed"
  rescue Jekyll::Errors::FatalException
    nil
  ensure
    FileUtils.remove_entry(root)
  end
end

# Duplicate ids across files.
root = fixture_root
write_work(root, "little-prince.md", valid_work)
write_work(root, "copy.md", valid_work.sub("id: little-prince", "id: copy"))
# Renamed file keeps its own id; create the real duplicate by hand.
File.write(File.join(root, "_works", "copy.md"), valid_work)
begin
  build_site(root)
  abort "duplicate ids: build should have failed"
rescue Jekyll::Errors::FatalException
  nil
ensure
  FileUtils.remove_entry(root)
end

# Post references: missing, unpublished and undeclared includes must fail.
{
  "missing reference" => "---\ntitle: P\nworks:\n  - ghost\n---\n",
  "duplicate reference" => "---\ntitle: P\nworks:\n  - little-prince\n  - little-prince\n---\n",
  "undeclared include" => "---\ntitle: P\n---\n{% include work-card.html id=\"little-prince\" %}\n"
}.each do |name, front_matter|
  root = fixture_root
  write_work(root, "little-prince.md", valid_work)
  File.write(File.join(root, "_posts", "2020-01-01-p.md"), front_matter + "正文\n")
  begin
    build_site(root)
    abort "#{name}: build should have failed"
  rescue Jekyll::Errors::FatalException
    nil
  ensure
    FileUtils.remove_entry(root)
  end
end

# Unpublished works cannot be referenced and stay out of the wall data.
root = fixture_root
write_work(root, "little-prince.md", valid_work)
write_work(root, "hidden.md", valid_work.sub("id: little-prince", "id: hidden")
                                        .sub("rating: 8.5", "published: false\nrating: 8.5"))
File.write(File.join(root, "_posts", "2020-01-01-p.md"),
           "---\ntitle: P\nworks:\n  - hidden\n---\n正文\n")
begin
  build_site(root)
  abort "unpublished reference: build should have failed"
rescue Jekyll::Errors::FatalException
  nil
ensure
  FileUtils.remove_entry(root)
end

# Valid records pass, and unquoted YAML dates normalize to ISO strings.
root = fixture_root
write_work(root, "little-prince.md", valid_work)
File.write(File.join(root, "_posts", "2020-01-01-p.md"),
           "---\ntitle: P\nworks:\n  - little-prince\n---\n{% include work-card.html id=\"little-prince\" %}\n")
site = build_site(root)
work = site.collections["works"].docs.first
abort "reviewed_at was not normalized" unless work.data["reviewed_at"] == "2026-09-18"
abort "Public S3 Unicode URL was rejected" unless WorksValidation.public_image_url?("https://image.yurich.me/books/小王子/cover.webp?versionId=public-version")
abort "Non-URL image data was accepted" if WorksValidation.public_image_url?({ "path" => "/cover.webp" })
FileUtils.remove_entry(root)

puts "Verified works validation: invalid records fail the build, valid records pass."
