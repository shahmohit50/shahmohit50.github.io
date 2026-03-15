import requests
from datetime import datetime
import os

GROQ_API_KEY = os.environ["GROQ_API_KEY"]

prompt = """
Write a 700 word blog post about AI experiments that can run on low-end hardware.
Focus on practical tutorials and tools.

Structure:
Intro
## Hardware Setup
## Tools Used
## Workflow
## Results
## Conclusion

Return only markdown content.
"""

url = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "llama-3.3-70b-versatile",
    "messages": [
        {"role": "user", "content": prompt}
    ]
}

response = requests.post(url, headers=headers, json=data)

content = response.json()["choices"][0]["message"]["content"]

today = datetime.utcnow().strftime("%Y-%m-%d")
filename = f"_posts/{today}-ai-experiment.md"

post = f"""---
layout: post
title: "AI Experiment on Low-End Hardware"
date: {today}
description: "AI experiment running on budget hardware."
author: "AI Agent"
---

{content}
"""

with open(filename, "w", encoding="utf-8") as f:
    f.write(post)

print("Post generated:", filename)
