# frozen_string_literal: true

require "json"
require "fileutils"
require "nokogiri"

# Use Jekyll's published collection, not a filesystem glob that can leak drafts.
# This private input stays outside _site; tools/export_blog.py creates the ZIP.
Jekyll::Hooks.register :site, :post_write do |site|
  posts = site.posts.docs.select do |post|
    post.relative_path.start_with?("_posts/") &&
      post.data["published"] != false && post.date <= site.time
  end.sort_by(&:relative_path).map do |post|
    image = post.data["image"]
    image = image["path"] if image.is_a?(Hash)
    {
      "source" => post.relative_path,
      "filename" => File.basename(post.path),
      "title" => post.data["title"].to_s,
      "url" => post.url,
      "media_subpath" => post.data["media_subpath"].to_s,
      "front_image" => image,
      # Detect unsupported image-producing Liquid/includes instead of silently
      # generating a ZIP whose Markdown has missing pictures.
      "rendered_images" => Nokogiri::HTML(post.output).css("main > article img").flat_map do |node|
        [node["src"], node["data-src"]].compact
      end.uniq,
      "markdown" => File.read(post.path, encoding: "bom|utf-8")
    }
  end

  images = %w[avatar sidebar_background].filter_map do |role|
    url = site.config[role]
    { "role" => role, "url" => url } unless url.to_s.empty?
  end
  Array(site.config.dig("blog_export", "extra_images")).each_with_index do |url, index|
    images << { "role" => "extra_#{index + 1}", "url" => url }
  end

  input = {
    "schema_version" => 1,
    "enabled" => site.config.dig("blog_export", "enabled") == true,
    "generated_at" => site.time.iso8601,
    "title" => site.config["title"],
    "site_url" => site.config["url"],
    "baseurl" => site.config["baseurl"].to_s,
    "cdn" => site.config["cdn"].to_s,
    "posts" => posts,
    "site_images" => images
  }
  path = File.join(site.source, ".jekyll-cache", "blog-export.json")
  FileUtils.mkdir_p(File.dirname(path))
  File.write(path, JSON.pretty_generate(input))
end
