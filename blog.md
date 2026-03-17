---
layout: default
title: Blog
---
{% for post in site.posts %}
  <div class="post-card">
    <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
    <p class="meta">{{ post.date | date: "%B %d, %Y" }}</p>

    <p>
      {{ post.excerpt | strip_html | truncate: 160 }}
    </p>

    <a href="{{ post.url }}" class="read-more">Read more →</a>
  </div>
{% endfor %}

