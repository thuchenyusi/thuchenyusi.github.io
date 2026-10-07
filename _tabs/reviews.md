---
title: reviews
icon: fas fa-star-half-stroke
order: 4
permalink: /reviews/
---

{% assign published = site.works | where_exp: "work", "work.published != false" %}
{% assign dated = published | where_exp: "work", "work.reviewed_at" | sort: "title" %}
{% assign undated = published | where_exp: "work", "work.reviewed_at == nil" | sort: "title" %}
{% assign groups = dated | group_by: "reviewed_at" | sort: "name" | reverse %}

<div class="reviews-filter" role="group" aria-label="按作品类型筛选">
  <button type="button" class="active" data-filter="all" aria-pressed="true">全部</button>
  <button type="button" data-filter="book" aria-pressed="false">书籍</button>
  <button type="button" data-filter="movie" aria-pressed="false">电影</button>
  <button type="button" data-filter="anime" aria-pressed="false">动画</button>
  <button type="button" data-filter="game" aria-pressed="false">游戏</button>
</div>

<div class="reviews-wall">
  {% for group in groups %}
    {% for work in group.items %}
      {% include work-card.html work=work mode="wall" %}
    {% endfor %}
  {% endfor %}
  {% for work in undated %}
    {% include work-card.html work=work mode="wall" %}
  {% endfor %}
</div>

<p class="reviews-empty"{% if published.size > 0 %} hidden{% endif %}>暂无记录</p>

<div class="work-details-source" hidden>
  {% for group in groups %}
    {% for work in group.items %}
      {% capture body %}{{ work.content | markdownify }}{% endcapture %}
      <template data-detail-for="{{ work.work_id }}">{% include work-detail.html work=work body=body collapse=true %}</template>
    {% endfor %}
  {% endfor %}
  {% for work in undated %}
    {% capture body %}{{ work.content | markdownify }}{% endcapture %}
    <template data-detail-for="{{ work.work_id }}">{% include work-detail.html work=work body=body collapse=true %}</template>
  {% endfor %}
</div>

<script defer src="{{ '/assets/js/reviews.js' | relative_url }}"></script>
