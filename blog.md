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

<h2>Latest Posts</h2>
<ul>
  {% for post in site.posts %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a> - <small>{{ post.date | date: "%B %d, %Y" }}</small>
    </li>
  {% endfor %}
</ul>
