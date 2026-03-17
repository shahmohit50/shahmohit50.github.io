---
layout: default
title: Blog
---

<div class="hero">
  <h1>AI Experiments Lab</h1>
  <p>Simple guides, experiments, and breakdowns of trending AI tools.</p>
</div>

<div class="post-list">
  {% for post in site.posts %}
    <div class="post-card">
      <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>

      <p class="meta">
        {{ post.date | date: "%B %d, %Y" }}
      </p>

      <p>
        {{ post.excerpt | strip_html | truncate: 160 }}
      </p>

      <a href="{{ post.url }}" class="read-more">Read more →</a>
    </div>
  {% endfor %}
</div>

