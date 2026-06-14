"""Free-form user prompt -> Instagram post content generator."""
from agents import IMAGE_PROMPT_GUIDELINES


def build_prompt(user_input):
    """Build the GPT user prompt for an arbitrary football-related topic."""
    return f"""The user wants Instagram content about: {user_input}

Generate:
1. A punchy IMAGE HEADLINE — a short, bold breaking-news-style hook (4-8 words, ALL CAPS, no emojis) based on the topic
2. Instagram CAPTION (punchy, opinionated, 150 words, FootBro Show voice)
3. Stats/facts bullets for image overlay (5 bullet points — at least 1 must be a real, well-known trivia fact or stat related to the topic that you're confident is accurate; never invent numbers)
4. DALL-E image prompt ({IMAGE_PROMPT_GUIDELINES})
5. Top 5 hashtags

Respond in JSON format:
{{
  "headline": "...",
  "caption": "...",
  "stats_bullets": ["• ...", "• ...", "• ...", "• ...", "• ..."],
  "image_prompt": "...",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
}}"""
