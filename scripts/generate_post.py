import requests
import feedparser
import json
import os
import ast
from datetime import datetime
from rapidfuzz import fuzz

# ==============================
# CONFIG
# ==============================
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
TOPIC_FILE = "topics.json"
POSTS_DIR = "_posts"

os.makedirs(POSTS_DIR, exist_ok=True)

# ==============================
# FETCH NEWS (RSS)
# ==============================
def fetch_google_news():
    url = "https://news.google.com/rss/search?q=artificial+intelligence"
    feed = feedparser.parse(url)

    return [entry.title for entry in feed.entries[:10]]


def fetch_product_hunt():
    url = "https://www.producthunt.com/feed"
    feed = feedparser.parse(url)

    titles = []
    for entry in feed.entries[:10]:
        if "ai" in entry.title.lower():
            titles.append(entry.title)

    return titles


# ==============================
# TOPIC STORAGE
# ==============================
def load_topics():
    if not os.path.exists(TOPIC_FILE):
        return set()

    with open(TOPIC_FILE, "r") as f:
        return set(json.load(f))


def save_topics(topics):
    with open(TOPIC_FILE, "w") as f:
        json.dump(list(topics), f, indent=2)


def normalize(text):
    return text.lower().strip()


def is_duplicate(new_topic, stored_topics, threshold=85):
    for old in stored_topics:
        if fuzz.ratio(new_topic, old) > threshold:
            return True
    return False


# ==============================
# LLM CALL
# ==============================
def call_llm(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

# ==============================
# EXTRACT TOPICS
# ==============================
def extract_topics(headlines):
    prompt = f"""
    From these headlines, extract 4 UNIQUE AI topics.

    Rules:
    - No duplicates
    - Combine similar ideas
    - Beginner-friendly wording
    - Max 4 topics

    Headlines:
    {headlines}

    Return ONLY a valid JSON array.
    """

    result = call_llm(prompt)

    try:
        # return ast.literal_eval(result)
         return json.loads(result)
    except:
        print("❌ Parsing failed:", e)
        return []



# ==============================
# GENERATE BLOG
# ==============================
def generate_blog(topic, headlines):
    prompt = f"""
    Write a beginner-friendly blog post about this AI topic:

    "{topic}"

    Use this context from recent news:
    {headlines}

    Keep language simple for non-technical readers.

    Structure:
    Intro
    ## What is this?
    ## Why it matters
    ## Real-life example
    ## Simple explanation of how it works
    ## Conclusion

    Return markdown only.
    """

    return call_llm(prompt)

# ==============================
# SAVE BLOG
# ==============================
def save_blog(content, topic, index):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    slug = normalize(topic).replace(" ", "-")

    filename = f"{POSTS_DIR}/{today}-{slug}-{index}.md"

    post = f"""---
layout: post
title: "{topic}"
date: {today}
description: "Simple explanation of {topic}"
author: "AI Agent"
---

{content}
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(post)

    print("✅ Saved:", filename)


# ==============================
# MAIN PIPELINE
# ==============================
def main():
    print("🚀 Fetching news...")

    headlines = fetch_google_news() + fetch_product_hunt()

    print(f"📰 Found {len(headlines)} headlines")

    topics = extract_topics(headlines)

    print("🧠 Extracted topics:", topics)

    stored_topics = load_topics()
    new_topics = []

    for topic in topics:
        norm = normalize(topic)

        if not is_duplicate(norm, stored_topics):
            new_topics.append(topic)
            stored_topics.add(norm)

    print("✨ New topics:", new_topics)

    if not new_topics:
        print("⚠️ No new topics found. Exiting.")
        return

    for i, topic in enumerate(new_topics):
        print(f"✍️ Generating blog for: {topic}")
        content = generate_blog(topic, headlines)
        save_blog(content, topic, i)

    save_topics(stored_topics)
    print("💾 Topics updated")


# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    main()
                        

# prompt = """
# Write a blog post about AI experiments that can run on low-end hardware.
# Focus on practical tutorials and tools.

# Structure:
# Intro
# ## Hardware Setup
# ## Tools Used
# ## Workflow
# ## Results
# ## Conclusion

# Return only markdown content.
# """

# url = "https://api.groq.com/openai/v1/chat/completions"

# headers = {
#     "Authorization": f"Bearer {GROQ_API_KEY}",
#     "Content-Type": "application/json"
# }

# data = {
#     "model": "llama-3.3-70b-versatile",
#     "messages": [
#         {"role": "user", "content": prompt}
#     ]
# }

# response = requests.post(url, headers=headers, json=data)

# content = response.json()["choices"][0]["message"]["content"]

# today = datetime.utcnow().strftime("%Y-%m-%d")
# filename = f"_posts/{today}-ai-experiment.md"

# post = f"""---
# layout: post
# title: "AI Experiment on Low-End Hardware"
# date: {today}
# description: "AI experiment running on budget hardware."
# author: "AI Agent"
# ---

# {content}
# """

# with open(filename, "w", encoding="utf-8") as f:
#     f.write(post)

# print("Post generated:", filename)
