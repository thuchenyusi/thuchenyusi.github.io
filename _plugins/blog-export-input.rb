# frozen_string_literal: true

require "json"
require "fileutils"
require "nokogiri"

# Use Jekyll's published collection, not a filesystem glob that can leak drafts.
# This private input stays outside _site; tools/export_blog.py creates the ZIP.
Jekyll::Hooks.register :site, :post_write do |site|
  rendered_images = lambda do |document|
    html = Nokogiri::HTML(document.output)
    article = html.at_css("main > article") || html
    article.css("img, source").flat_map do |node|
      [node["src"], node["data-src"]].compact +
        node["srcset"].to_s.scan(/(?:\A|,)\s*([^\s,]+)/).flatten
    end.uniq
  end
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
      # Include card covers too: the exporter expands each supported card into
      # portable Markdown before checking that every rendered image is saved.
      "rendered_images" => rendered_images.call(post),
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

  works_collection = site.collections["works"]
  works = works_collection ? works_collection.docs.select do |work|
    work.data["published"] != false
  end.sort_by { |work| work.data["id"].to_s }.map do |work|
    {
      "id" => work.data["id"].to_s,
      "source" => work.relative_path,
      "filename" => File.basename(work.path),
      "title" => work.data["title"].to_s,
      "creator" => work.data.values_at("author", "director", "developer").find { |value| !value.to_s.empty? },
      "rating" => work.data["rating"],
      "url" => work.url,
      "media_subpath" => work.data["media_subpath"].to_s,
      "front_image" => work.data["image"],
      "rendered_images" => rendered_images.call(work),
      "markdown" => File.read(work.path, encoding: "bom|utf-8")
    }
  end : []

  input = {
    "schema_version" => 3,
    "enabled" => site.config.dig("blog_export", "enabled") == true,
    "generated_at" => site.time.iso8601,
    "title" => site.config["title"],
    "site_url" => site.config["url"],
    "baseurl" => site.config["baseurl"].to_s,
    "cdn" => site.config["cdn"].to_s,
    "posts" => posts,
    "works" => works,
    "site_images" => images
  }
  path = File.join(site.source, ".jekyll-cache", "blog-export.json")
  FileUtils.mkdir_p(File.dirname(path))
  File.write(path, JSON.pretty_generate(input))
end
