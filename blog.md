---
layout: default
title: Blog
---

# AI Story Experiments

{% for post in site.posts %}
  ## [{{ post.title }}]({{ post.url }})
  <small>{{ post.date | date: "%B %d, %Y" }}</small>
  <p>{{ post.excerpt }}</p>
{% endfor %}
