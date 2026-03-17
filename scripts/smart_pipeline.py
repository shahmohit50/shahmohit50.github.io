import requests
import feedparser
import json
from datetime import datetime
import os

# ------------------------------
# CONFIG
# ------------------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
POSTS_DIR = "_posts"
USED_TOPICS_FILE = "used_topics.json"

# Hybrid model assignment
FAST_MODEL = "qwen/qwen3-32b"                 # Trend extraction & ranking
BLOG_MODEL = "llama-3.3-70b-versatile"        # Main blog generation
TUTORIAL_MODEL = "moonshotai/kimi-k2-instruct-0905"  # Optional tutorial sections

MAX_BLOGS_PER_DAY = 4

# Reddit config
REDDIT_SUBREDDITS = ["MachineLearning", "ArtificialIntelligence"]
REDDIT_LIMIT = 20

# Product Hunt API
PRODUCT_HUNT_API_KEY = os.environ.get("PRODUCT_HUNT_API_KEY")
PRODUCT_HUNT_LIMIT = 20

# GitHub Trending
GITHUB_TRENDING_URL = "https://ghapi.huchen.dev/repositories"  # unofficial API
GITHUB_TRENDING_LIMIT = 20

# ------------------------------
# UTILS
# ------------------------------
def load_used_topics():
    if os.path.exists(USED_TOPICS_FILE):
        with open(USED_TOPICS_FILE, "r") as f:
            return json.load(f)
    return []

def save_used_topics(topics):
    with open(USED_TOPICS_FILE, "w") as f:
        json.dump(topics, f, indent=2)

def call_groq_api(model, prompt, max_tokens=3000, temperature=0.7):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

# ------------------------------
# STEP 1: FETCH HEADLINES
# ------------------------------
def fetch_google_rss(rss_url="https://news.google.com/rss/search?q=AI&hl=en-US&gl=US&ceid=US:en"):
    feed = feedparser.parse(rss_url)
    headlines = [{"title": entry.title, "link": entry.link, "source": "Google News"} for entry in feed.entries]
    return headlines

def fetch_reddit(subreddits=REDDIT_SUBREDDITS, limit=REDDIT_LIMIT):
    headers = {"User-Agent": "AutoBlogBot/1.0"}
    all_posts = []
    for subreddit in subreddits:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            continue
        data = resp.json()
        for post in data["data"]["children"]:
            all_posts.append({"title": post["data"]["title"], "link": post["data"]["url"], "source": f"Reddit/{subreddit}", "popularity": post["data"]["score"]})
    return all_posts

def fetch_product_hunt(limit=PRODUCT_HUNT_LIMIT):
    if not PRODUCT_HUNT_API_KEY:
        return []
    headers = {"Authorization": f"Bearer {PRODUCT_HUNT_API_KEY}"}
    url = f"https://api.producthunt.com/v2/api/graphql"
    query = {
        "query": """
        { posts(order: VOTES, first: %d) { edges { node { name tagline url } } } }
        """ % limit
    }
    resp = requests.post(url, headers=headers, json=query)
    posts = []
    try:
        edges = resp.json()["data"]["posts"]["edges"]
        for edge in edges:
            node = edge["node"]
            posts.append({"title": f"{node['name']}: {node['tagline']}", "link": node['url'], "source": "Product Hunt"})
    except:
        pass
    return posts

def fetch_github_trending(limit=GITHUB_TRENDING_LIMIT):
    resp = requests.get(GITHUB_TRENDING_URL)
    repos = []
    if resp.status_code == 200:
        data = resp.json()[:limit]
        for r in data:
            repos.append({"title": f"{r['name']} ({r['description']})", "link": r['url'], "source": "GitHub"})
    return repos

# ------------------------------
# STEP 2: EXTRACT TRENDS
# ------------------------------
def extract_trends(headlines):
    titles = "\n".join([h["title"] for h in headlines])
    prompt = f"""
Extract 8 specific AI trends from these headlines.
- Avoid generic categories like 'AI in business'
- Focus on real tools, models, or events.
- Return JSON array of strings only.

Headlines:
{titles}
"""
    trends_json = call_groq_api(FAST_MODEL, prompt)
    try:
        trends = json.loads(trends_json)
        return trends
    except:
        return [t.strip() for t in trends_json.split("\n") if t.strip()]

# ------------------------------
# STEP 3: RANK TRENDS
# ------------------------------
def rank_trends(trends):
    prompt = f"""
Rank the following AI trends for beginner-friendliness, interest, and timeliness.
- Return JSON array of top 4 trends in order.

Trends:
{json.dumps(trends)}
"""
    ranked_json = call_groq_api(FAST_MODEL, prompt)
    try:
        return json.loads(ranked_json)
    except:
        return trends[:4]

# ------------------------------
# STEP 4: FILTER NEW TOPICS
# ------------------------------
def filter_new_topics(trends, used_topics):
    new = [t for t in trends if t not in used_topics]
    return new[:MAX_BLOGS_PER_DAY]

# ------------------------------
# STEP 5: GENERATE BLOG PER TOPIC
# ------------------------------
def generate_blog(topic):
    prompt = f"""
You are an AI blog writer. Write a Medium-style, beginner-friendly blog about "{topic}".

Structure:

## What is {topic}?
- Give a clear, concise definition.

## Real-world Use Cases
- Only provide accurate, concrete examples.

## Tutorial / How to Get Started
- Beginner-friendly step-by-step guide or setup instructions.
- Include commands or code snippets if applicable.

## Conclusion
- Summarize key points and add tips for beginners.

Return markdown only.
"""
    return call_groq_api(BLOG_MODEL, prompt, max_tokens=4000)

# ------------------------------
# STEP 6: SAVE BLOG TO _posts
# ------------------------------
def save_blog(topic, content):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"{POSTS_DIR}/{today}-{topic.replace(' ', '-').lower()}.md"
    front_matter = f"""---
layout: post
title: "{topic}"
date: {today}
description: "Blog about {topic} and how to get started."
author: "AI Agent"
tags: [AI, Tutorial, {topic}]
---

"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(front_matter + content)
    return filename

# ------------------------------
# MAIN PIPELINE
# ------------------------------
def main():
    os.makedirs(POSTS_DIR, exist_ok=True)
    
    print("🚀 Fetching headlines...")
    # headlines = fetch_google_rss() + fetch_reddit() + fetch_product_hunt() + fetch_github_trending()
    headlines = fetch_google_rss() + fetch_reddit() + fetch_product_hunt()
    print(f"📰 Collected {len(headlines)} headlines from multiple sources")

    trends = extract_trends(headlines)
    print(f"🧠 Extracted trends: {trends}")
    
    ranked_trends = rank_trends(trends)
    print(f"✨ Ranked trends: {ranked_trends}")
    
    used_topics = load_used_topics()
    new_topics = filter_new_topics(ranked_trends, used_topics)
    
    if not new_topics:
        print("⚠️ No new trends to generate blogs for. Exiting.")
        return
    
    print(f"📝 Generating blogs for: {new_topics}")
    
    for topic in new_topics:
        print(f"Generating blog for: {topic}")
        content = generate_blog(topic)
        filename = save_blog(topic, content)
        print(f"✅ Blog saved: {filename}")
        used_topics.append(topic)
    
    save_used_topics(used_topics)
    print("🎉 All blogs generated and saved.")

# ------------------------------
# RUN
# ------------------------------
if __name__ == "__main__":
    main()
