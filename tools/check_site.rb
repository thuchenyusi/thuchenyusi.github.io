# frozen_string_literal: true

require "nokogiri"
require "json"
require "uri"
require "pathname"

root = Pathname.new(ARGV.fetch(0, "_site")).expand_path
pages = Dir[root.join("**/*.html").to_s]
abort "No generated pages found in #{root}" if pages.empty?
errors = []
checked = 0

# Check local page/resource references without requiring external network access.
pages.each do |file|
  doc = Nokogiri::HTML(File.read(file))
  doc.css("[href], [src]").each do |element|
    %w[href src].each do |attribute|
      url = element[attribute]
      next if url.nil? || url.empty? || url.start_with?("#", "//")
      next if url.match?(/\A[a-z][a-z0-9+.-]*:/i)

      path = URI::DEFAULT_PARSER.unescape(url.split(/[?#]/).first.to_s)
      target = path.start_with?("/") ? root.join(path.delete_prefix("/")) : Pathname.new(file).dirname.join(path)
      candidates = [target, target.join("index.html"), Pathname.new("#{target}.html")]
      errors << "#{Pathname.new(file).relative_path_from(root)}: missing #{url}" unless candidates.any?(&:file?)
      checked += 1
    end
  end
end

# These endpoints are consumed by JavaScript and the browser, not HTML links.
%w[assets/js/data/search.json assets/js/data/swconf.js app.min.js sw.min.js sw.js feed.xml].each do |path|
  errors << "Missing theme endpoint: #{path}" unless root.join(path).file?
end
search = JSON.parse(root.join("assets/js/data/search.json").read)
errors << "Search index is empty" if search.empty?
manifest = JSON.parse(root.join("assets/img/favicons/site.webmanifest").read)
manifest.fetch("icons").each do |icon|
  errors << "Missing PWA icon: #{icon['src']}" unless root.join(icon.fetch("src").delete_prefix("/")).file?
end

abort errors.uniq.join("\n") unless errors.empty?
puts "Checked #{pages.size} pages, #{checked} local references, #{search.size} search entries and PWA assets."
