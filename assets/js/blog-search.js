(function () {
  const dataNode = document.getElementById("blog-posts-data");
  const grid = document.getElementById("blog-results-grid");
  const emptyState = document.getElementById("blog-empty-state");
  const status = document.getElementById("blog-results-status");
  const input = document.getElementById("blog-search-input");
  const clearBtn = document.getElementById("blog-search-clear");
  const sort = document.getElementById("blog-sort");
  const template = document.getElementById("blog-card-template");
  const filterRow = document.getElementById("blog-filter-row");
  const resultsWrap = document.querySelector(".blog-results");

  if (!dataNode || !grid || !status || !input || !sort || !template || !filterRow) {
    return;
  }

  let parsed = [];
  try {
    parsed = JSON.parse(dataNode.textContent);
  } catch (error) {
    status.textContent = "Could not load posts data for search.";
    return;
  }

  if (!Array.isArray(parsed) || parsed.length === 0) {
    status.textContent = "No posts published yet.";
    return;
  }

  const posts = parsed.map((item, index) => {
    const tags = Array.isArray(item.tags)
      ? item.tags.filter(Boolean).map((tag) => String(tag))
      : [];
    return {
      title: String(item.title || ""),
      url: String(item.url || "#"),
      excerpt: String(item.excerpt || ""),
      description: String(item.description || ""),
      dateIso: String(item.date_iso || "1970-01-01"),
      datePretty: String(item.date_pretty || ""),
      readingMinutes: Number(item.reading_minutes) || 1,
      tags,
      tagsLower: tags.map((tag) => tag.toLowerCase()),
      position: index
    };
  });

  const featuredUrl = resultsWrap ? String(resultsWrap.dataset.featuredUrl || "") : "";
  const state = {
    query: "",
    filter: "all",
    sort: "newest"
  };

  function slugify(value) {
    return String(value)
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "");
  }

  function scorePost(post, terms) {
    if (!terms.length) {
      return 0;
    }

    const title = post.title.toLowerCase();
    const body = (post.description + " " + post.excerpt).toLowerCase();
    const tags = post.tagsLower.join(" ");
    const allText = title + " " + body + " " + tags;

    const everyTermExists = terms.every((term) => allText.includes(term));
    if (!everyTermExists) {
      return 0;
    }

    let score = 0;
    terms.forEach((term) => {
      if (title.includes(term)) {
        score += 8;
      }
      if (body.includes(term)) {
        score += 4;
      }
      if (tags.includes(term)) {
        score += 5;
      }
    });

    return score;
  }

  function getFilteredPosts() {
    const terms = state.query
      .toLowerCase()
      .split(/\s+/)
      .filter(Boolean);

    let scoped = posts.filter((post) => {
      if (state.filter === "all") {
        return true;
      }
      return post.tagsLower.includes(state.filter);
    });

    const mapped = scoped.map((post) => ({
      ...post,
      score: scorePost(post, terms),
      time: Date.parse(post.dateIso) || 0
    }));

    let filtered = mapped;
    if (terms.length > 0) {
      filtered = mapped.filter((post) => post.score > 0);
    } else if (state.filter === "all" && featuredUrl) {
      filtered = mapped.filter((post) => post.url !== featuredUrl);
    }

    const sortMode = terms.length > 0 && state.sort === "newest" ? "relevance" : state.sort;

    filtered.sort((a, b) => {
      if (sortMode === "oldest") {
        return a.time - b.time || a.position - b.position;
      }
      if (sortMode === "title") {
        return a.title.localeCompare(b.title);
      }
      if (sortMode === "relevance") {
        return b.score - a.score || b.time - a.time;
      }
      return b.time - a.time || a.position - b.position;
    });

    return filtered;
  }

  function createTagPill(tag) {
    const pill = document.createElement("span");
    pill.className = "tag-pill";
    pill.textContent = tag;
    return pill;
  }

  function renderCards(list) {
    grid.innerHTML = "";
    emptyState.hidden = list.length > 0;

    if (!list.length) {
      return;
    }

    const fragment = document.createDocumentFragment();

    list.forEach((post, index) => {
      const clone = template.content.cloneNode(true);
      const card = clone.querySelector(".blog-card");
      const link = clone.querySelector(".blog-card-link");
      const dateNode = clone.querySelector(".blog-card-date");
      const titleNode = clone.querySelector(".blog-card-title");
      const excerptNode = clone.querySelector(".blog-card-excerpt");
      const tagsNode = clone.querySelector(".blog-card-tags");
      const readNode = clone.querySelector(".blog-card-read");

      card.style.setProperty("--stagger", String(Math.min(index, 14)));
      link.setAttribute("href", post.url);
      dateNode.textContent = post.datePretty;
      titleNode.textContent = post.title;
      excerptNode.textContent = post.description || post.excerpt;
      readNode.textContent = post.readingMinutes + " min read";

      tagsNode.innerHTML = "";
      post.tags.slice(0, 3).forEach((tag) => {
        tagsNode.appendChild(createTagPill(tag));
      });

      fragment.appendChild(clone);
    });

    grid.appendChild(fragment);
  }

  function updateStatus(total, shown) {
    const hasQuery = state.query.trim().length > 0;
    let message = "Showing " + shown + " of " + total + " stories";

    if (state.filter !== "all") {
      message += " in #" + state.filter;
    }
    if (hasQuery) {
      message += ' for "' + state.query.trim() + '"';
    }

    status.textContent = message;
  }

  function applyFilterButtons() {
    const buttons = filterRow.querySelectorAll(".filter-chip");
    buttons.forEach((button) => {
      const key = String(button.dataset.filter || "all");
      if (key === state.filter) {
        button.classList.add("is-active");
      } else {
        button.classList.remove("is-active");
      }
    });
  }

  function render() {
    const result = getFilteredPosts();
    renderCards(result);
    updateStatus(posts.length, result.length);
    applyFilterButtons();

    const hasValue = input.value.trim().length > 0;
    clearBtn.hidden = !hasValue;
  }

  function applyHashFilter() {
    const hash = window.location.hash.replace(/^#/, "");
    if (!hash) {
      return;
    }
    const chip = document.getElementById(hash);
    if (!(chip instanceof HTMLElement) || !chip.classList.contains("filter-chip")) {
      return;
    }
    state.filter = String(chip.dataset.filter || "all");
  }

  function buildTagFilters() {
    const counts = new Map();
    posts.forEach((post) => {
      post.tags.forEach((tag) => {
        const key = tag.trim();
        if (!key) {
          return;
        }
        counts.set(key, (counts.get(key) || 0) + 1);
      });
    });

    const topTags = Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, 8);

    topTags.forEach(([tag, count]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "filter-chip";
      button.dataset.filter = tag.toLowerCase();
      button.id = "tag-" + slugify(tag);
      button.textContent = tag + " (" + count + ")";
      filterRow.appendChild(button);
    });
  }

  let debounceTimer = null;
  input.addEventListener("input", function (event) {
    const value = String(event.target.value || "");
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function () {
      state.query = value;
      render();
    }, 100);
  });

  clearBtn.addEventListener("click", function () {
    state.query = "";
    input.value = "";
    input.focus();
    render();
  });

  sort.addEventListener("change", function (event) {
    state.sort = String(event.target.value || "newest");
    render();
  });

  filterRow.addEventListener("click", function (event) {
    const target = event.target;
    if (!(target instanceof HTMLElement) || !target.classList.contains("filter-chip")) {
      return;
    }
    state.filter = String(target.dataset.filter || "all");
    if (state.filter === "all") {
      history.replaceState(null, "", window.location.pathname + window.location.search);
    } else if (target.id) {
      history.replaceState(null, "", "#" + target.id);
    }
    render();
  });

  document.addEventListener("keydown", function (event) {
    const active = document.activeElement;
    const isTyping =
      active instanceof HTMLInputElement ||
      active instanceof HTMLTextAreaElement ||
      active instanceof HTMLSelectElement;
    if (event.key === "/" && !isTyping && !event.ctrlKey && !event.metaKey) {
      event.preventDefault();
      input.focus();
    }
  });

  buildTagFilters();
  applyHashFilter();
  render();
  window.addEventListener("hashchange", function () {
    applyHashFilter();
    render();
  });
})();
