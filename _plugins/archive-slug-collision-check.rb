# frozen_string_literal: true

# jekyll-archives silently lets one archive overwrite another when two names
# produce the same slug. Fail the build instead, so a future tag such as C#
# cannot make the C archive disappear unnoticed.
module Jekyll
  # The theme calls `slugify` without a mode. Use the same configured mode as
  # jekyll-archives while preserving any mode explicitly passed by a template.
  module Filters
    def slugify(input, mode = nil)
      mode ||= @context.registers[:site].config["archive_slug_mode"]
      Utils.slugify(input, :mode => mode)
    end
  end

  class ArchiveSlugCollisionCheck < Generator
    safe true
    priority :highest

    def generate(site)
      config = site.config.fetch("jekyll-archives", {})
      slug_mode = config.fetch("slug_mode", "default")

      verify_slug_mode!(site, slug_mode)

      enabled_archives = Array(config["enabled"])
      verify_collection!("category", site.categories, slug_mode) if enabled_archives.include?("categories")
      verify_collection!("tag", site.tags, slug_mode) if enabled_archives.include?("tags")
    end

    private

    def verify_slug_mode!(site, archive_slug_mode)
      link_slug_mode = site.config.fetch("archive_slug_mode", "default")
      return if archive_slug_mode == link_slug_mode

      raise Errors::FatalException,
            "archive_slug_mode (#{link_slug_mode}) must match " \
            "jekyll-archives.slug_mode (#{archive_slug_mode})"
    end

    def verify_collection!(type, collection, slug_mode)
      collisions = collection.keys.group_by do |name|
        Utils.slugify(name.to_s, mode: slug_mode)
      end.select { |_slug, names| names.size > 1 }

      return if collisions.empty?

      details = collisions.map do |slug, names|
        "#{names.map(&:inspect).join(', ')} -> #{slug.inspect}"
      end.join("; ")

      raise Errors::FatalException, "Conflicting #{type} archive slugs: #{details}"
    end
  end
end
