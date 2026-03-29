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
Write a deep-dive blog post about this trending AI topic:

    "{topic}"

    Use these news headlines as context:
    {headlines}

    The blog should feel like a Medium article.

    IMPORTANT:
    - Focus on helping the reader actually understand AND try it
    - Write like a human, slightly opinionated
    - Include practical steps if possible

    Structure:

    Intro (why everyone is suddenly talking about this)

    ## What is this and why is it trending?
    (Explain simply, no jargon)

    ---
**News Headline**: 
**Summary**: 
**Company**: 
**Key Claims**:

---
### **RULES**
- **Name names**: Call out executives, investors, or competitors by name.
- **Use past scandals**: Reference similar past incidents (e.g., “Remember when [Company] did [X] in [Year]?”).
- **End with a question**: Leave readers with a **provocative, open-ended** question.
- **No fluff**: Every sentence must either **inform, enrage, or amuse**.

---
### **EXAMPLE OUTPUT** (For reference)
# **Anthropic’s Claude 3.5: Ethical AI or Ethical Theater?**

**The Official Story**
Anthropic today unveiled Claude 3.5, calling it “the most ethical AI ever built.” New features include “constitutional guardrails” and “bias self-audits.” CEO Dario Amodei claimed it’s “a model that finally aligns with human values.”

**What They’re Not Saying**
✅ **The Good**: Claude 3.5 refuses to generate harmful content—unlike *some* competitors (*cough* Meta *cough*).
⚠️ **The Spin**: “Ethical” here means “safe for enterprises,” not “safe for society.” Remember when Google said the same about Bard?
❌ **The Lie**: Anthropic’s own safety board quit last month over “unresolved ethical concerns.” (Source: [The Information](#))

**Twitter vs. Reality**
> *@AI_Enthusiast: “Finally, an AI with a conscience!”*
> *@RealEthicist: “Lol, the same company that sold Claude 2 to the Pentagon is lecturing us on ethics.”*
> *@VC_Hustler: “Ethical = ‘won’t badmouth our investors.’”*

**The Hypocrisy No One’s Talking About**
Anthropic’s “constitutional AI” schtick is a smokescreen for their real innovation: **corporate absolution**. By framing ethics as a technical problem, they’re selling indemnity to CEOs. (“See? Our AI has a *constitution*—we’re not liable!”)

**Devil’s Advocate**
*What if this is the only way?*
In a world where every AI startup races to the bottom, Anthropic’s theater might be the lesser evil. But when “ethical” becomes a marketing term, who’s left to ask the hard questions?

*But here’s the catch:*
Anthropic’s “safety” is just **risk management for shareholders**. Their constitution is as binding as a Terms of Service no one reads.

**Prediction**
Within 6 months, Claude 3.5 will be caught generating misinfo—just like every “safe” model before it. The only difference? Anthropic’s PR team will call it “a learning opportunity.”

**How to Prepare**
- **Developers**: Audit Claude’s outputs like it’s 2016 and you’re Facebook.
- **Users**: Treat “ethical AI” like “organic cigarettes.” It’s better, but still bad for you.
- **Regulators**: Stop falling for self-audits. Demand **third-party red-teaming**.

---

    ## Final thoughts
    (Insightful, slightly opinionated)

    Keep it beginner-friendly but insightful.

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
