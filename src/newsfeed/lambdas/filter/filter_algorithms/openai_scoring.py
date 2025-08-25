# import openai
import os

# openai.api_key = os.getenv("OPENAI_API_KEY")

def get_openai_relevance_score(item: dict) -> float:
    """
    Use OpenAI to determine relevance of a news item.
    Returns a score between 0.0 (not relevant) and 1.0 (highly relevant).
    """
    # prompt = f"""
    # You are an AI assistant. Rate the relevance of the following news item for an IT manager.
    # Relevance criteria: security incidents, major outages, critical software bugs or updates, IT disruptions.
    # Return only a number between 0.0 and 1.0, where 1.0 is highly relevant.
    #
    # Title: {item.get('title', '')}
    # Body: {item.get('body', '')}
    # """

    # try:
    #     response = openai.ChatCompletion.create(
    #         model="gpt-4",
    #         messages=[{"role": "user", "content": prompt}],
    #         temperature=0.0
    #     )
    #     score_text = response['choices'][0]['message']['content'].strip()
    #     score = float(score_text)
    #     return max(0.0, min(1.0, score))  # ensure score is within 0.0–1.0
    # except Exception as e:
    #     print(f"OpenAI scoring failed: {e}")
    #     return 0.0

    # Since OpenAI is disabled, return 0.0 by default
    return 0.0
