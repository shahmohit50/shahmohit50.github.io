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
    From these headlines, extract 5 SPECIFIC and TRENDING AI topics.
    
    IMPORTANT:
    - Do NOT give generic categories like "AI in healthcare"
    - Each topic must refer to a SPECIFIC development, tool, model, or event
    - Make it feel like something people are actively talking about online
    - Include names if possible (tools, companies, models)
    
    Bad examples:
    - "AI in finance"
    - "Job displacement by AI"
    
    Good examples:
    - "New open-source AI agent frameworks like OpenClaw gaining traction"
    - "AI video generation tools becoming usable for creators"
    - "Local LLMs running on consumer laptops"
    
    Return ONLY a valid JSON array.
    
    Headlines:
    {headlines}
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
You are a top-tier tech blogger writing for a high-quality Medium-style publication.

Your goal is NOT just to inform — but to make the reader:

* Understand the topic deeply
* Stay engaged till the end
* Feel smarter after reading

---

## INPUT

Topic: "{topic}"

News context:
{headlines}

---

## WRITING STYLE (STRICT)

* Write like a human, slightly opinionated but not dramatic
* Avoid robotic or generic phrasing
* Use short, punchy paragraphs (2–4 lines max)
* Prefer clarity over jargon
* Sound like an experienced engineer explaining things simply

---

## STRUCTURE (FOLLOW EXACTLY)

# {topic} — What’s Actually Going On?

## 🚀 Why This Is Blowing Up Right Now

Start with a strong hook.
Explain WHY this topic is suddenly trending (not just what happened).

---

## 🧠 What This Actually Means (Simple Explanation)

Break it down like you're explaining to a smart beginner.
Avoid buzzwords unless you explain them.

---

## 🏗️ What’s Really Happening Behind the Scenes

Go deeper:

* How the tech works (high level)
* What companies are doing
* What makes this different from before

---

## ⚖️ The Reality Check

Give a balanced take:

* What’s genuinely impressive
* What’s overhyped or unclear

Be honest. This is where most blogs fail.

---

## 🛠️ Can You Actually Use This?

Make it practical:

* Who should care
* Real-world use cases
* Tools / links / ways to try it

---

## 🔮 What Happens Next

Give a grounded prediction:
(no sci-fi, no hype)

---

## 💬 Final Thoughts

End with a thoughtful, slightly opinionated conclusion.

Then ask ONE engaging question to the reader.

---

## OUTPUT RULES

* Return clean markdown only
* No placeholders
* No repetition
* No “AI-style” phrases like “in today’s rapidly evolving landscape”
* Make it feel like a blog someone would actually share

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
