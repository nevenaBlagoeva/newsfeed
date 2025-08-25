from newsfeed.lambdas.filter.filter_algorithms.baseline_scoring import calculate_keyword_relevance_score
from newsfeed.lambdas.filter.filter_algorithms.openai_scoring import get_openai_relevance_score

def calculate_relevance_score(item: dict, algorithm: str) -> float:
    if algorithm == 'word_score':
        return calculate_keyword_relevance_score(item)
    
    """
    elif algorithm == 'openai_score':
        try:
            # Attempt OpenAI scoring
            return get_openai_relevance_score(item)
        except Exception as e:
            # Fallback to keyword-based score if OpenAI fails
            print(f"OpenAI scoring failed ({e}), falling back to keyword score.")
            return calculate_keyword_relevance_score(item)
    """
    
    # Add more algorithms as needed
    return 0.0