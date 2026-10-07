# frozen_string_literal: true

require "date"
require "uri"

# 鉴赏栏目的构建期校验：作品记录不合法或文章引用悬空时让构建失败，
# 而不是生成残缺页面。评分不静默取整，导入适配器必须先清洗数据。
module WorksValidation
  TYPES = %w[book movie anime game].freeze unless defined?(TYPES)
  STATUSES = %w[wish doing done dropped].freeze unless defined?(STATUSES)
  LINK_KEYS = %w[douban bangumi].freeze unless defined?(LINK_KEYS)
  ID_PATTERN = /\A[a-z0-9][a-z0-9-]*\z/ unless defined?(ID_PATTERN)
  ISO_DATE = /\A\d{4}-\d{2}-\d{2}\z/ unless defined?(ISO_DATE)
  SIGNED_IMAGE_KEYS = %w[
    awsaccesskeyid signature expires key-pair-id policy
    x-amz-algorithm x-amz-credential x-amz-date x-amz-expires
    x-amz-signedheaders x-amz-signature x-amz-security-token
  ].freeze unless defined?(SIGNED_IMAGE_KEYS)

  class << self
    def validate(site)
      errors = []
      works = site.collections["works"] ? site.collections["works"].docs : []
      by_id = {}
      works.each { |doc| validate_work(doc, by_id, errors) }
      site.posts.docs.each { |post| validate_post(post, by_id, errors) }
      return if errors.empty?

      raise Jekyll::Errors::FatalException,
            "作品记录校验失败：\n" + errors.map { |error| "  - #{error}" }.join("\n")
    end

    def validate_work(doc, by_id, errors)
      path = doc.relative_path
      id = doc.data["id"].to_s
      if id.empty?
        errors << "#{path}: 缺少 id"
      else
        unless id.match?(ID_PATTERN)
          errors << "#{path}: id #{id.inspect} 只能包含小写字母、数字和连字符"
        end
        unless id == File.basename(doc.relative_path, ".*")
          errors << "#{path}: id #{id.inspect} 与文件名不一致"
        end
        if by_id.key?(id)
          errors << "#{path}: id #{id.inspect} 与 #{by_id[id][:path]} 重复"
        else
          by_id[id] = { path: path, published: doc.data["published"] != false }
        end
      end
      errors << "#{path}: 缺少 title" if doc.data["title"].to_s.empty?
      # Jekyll 文档内置的 id（集合路径）会在 Liquid 中遮蔽 front matter 的 id，
      # 另存 work_id 供模板使用。
      doc.data["work_id"] = id unless id.empty?
      unless TYPES.include?(doc.data["type"])
        errors << "#{path}: type 必须是 #{TYPES.join(' / ')}，当前为 #{doc.data['type'].inspect}"
      end
      unless STATUSES.include?(doc.data["status"])
        errors << "#{path}: status 必须是 #{STATUSES.join(' / ')}，当前为 #{doc.data['status'].inspect}"
      end
      rating = doc.data["rating"]
      unless rating.nil? || (rating.is_a?(Numeric) && rating >= 0 && rating <= 10 && (rating * 2) % 1 == 0)
        errors << "#{path}: rating 必须是 0 到 10、步长 0.5 的数字或 null，当前为 #{rating.inspect}"
      end
      validate_reviewed_at(doc, errors)
      image = doc.data["image"]
      if !image.nil? && !public_image_url?(image)
        errors << "#{path}: image 必须是显式的公开 http(s) URL，不使用 Liquid 表达式或签名地址"
      end
      validate_links(doc, errors)
    end

    def public_image_url?(image)
      return false unless image.is_a?(String) && !image.include?("{{") && !image.include?("{%")

      # Escape Unicode paths for URI parsing; query keys are decoded before
      # comparing so encoded/case-varied signing parameters cannot bypass it.
      uri = URI.parse(image.gsub(/[^\x00-\x7f]/) { |character| URI.encode_www_form_component(character) })
      return false unless %w[http https].include?(uri.scheme) && !uri.host.to_s.empty? && uri.userinfo.nil?

      URI.decode_www_form(uri.query.to_s).none? do |key, _|
        SIGNED_IMAGE_KEYS.include?(key.downcase)
      end
    rescue URI::InvalidURIError, ArgumentError
      false
    end

    def validate_reviewed_at(doc, errors)
      reviewed_at = doc.data["reviewed_at"]
      case reviewed_at
      when nil
        nil
      when Date, Time, DateTime
        # YAML 未加引号的日期会被解析成 Date，统一为 ISO 字符串供排序与分组。
        doc.data["reviewed_at"] = reviewed_at.strftime("%Y-%m-%d")
      when String
        valid = reviewed_at.match?(ISO_DATE) && begin
          Date.iso8601(reviewed_at)
          true
        rescue ArgumentError
          false
        end
        errors << "#{doc.relative_path}: reviewed_at 必须是 ISO 日期，当前为 #{reviewed_at.inspect}" unless valid
      else
        errors << "#{doc.relative_path}: reviewed_at 必须是 ISO 日期，当前为 #{reviewed_at.inspect}"
      end
    end

    def validate_links(doc, errors)
      links = doc.data["links"]
      return if links.nil?

      unless links.is_a?(Hash)
        errors << "#{doc.relative_path}: links 必须是 douban / bangumi 到条目 URL 的映射"
        return
      end
      links.each do |key, url|
        unless LINK_KEYS.include?(key.to_s)
          errors << "#{doc.relative_path}: links 只支持 #{LINK_KEYS.join(' / ')}，出现 #{key.inspect}"
          next
        end
        unless url.to_s.match?(%r{\Ahttps?://})
          errors << "#{doc.relative_path}: links.#{key} 必须是 http(s) 条目 URL"
        end
      end
    end

    def validate_post(post, by_id, errors)
      ids = post.data["works"]
      path = post.relative_path
      unless ids.nil? || ids.is_a?(Array)
        errors << "#{path}: works 必须是作品 id 列表"
        return
      end
      seen = {}
      Array(ids).each do |raw|
        id = raw.to_s
        if seen.key?(id)
          errors << "#{path}: works 重复引用 #{id.inspect}"
          next
        end
        seen[id] = true
        work = by_id[id]
        if work.nil? || !work[:published]
          errors << "#{path}: works 引用了不存在或未公开的作品 #{id.inspect}"
        end
      end
      post.content.to_s.scan(/\{%-?\s*include\s+work-card\.html\s+id\s*=\s*["']([^"']+)["']/).each do |(id)|
        unless seen.key?(id)
          errors << "#{path}: include work-card.html 引用了未在 works 中声明的作品 #{id.inspect}"
        end
      end
    end
  end
end

Jekyll::Hooks.register :site, :post_read do |site|
  WorksValidation.validate(site)
end
