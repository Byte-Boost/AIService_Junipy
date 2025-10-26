from typing import Dict, Any, Optional


def analyze_sentiment_local(text: str) -> Dict[str, Any]:
    """Very small heuristic sentiment analysis.

    Returns a dict with score and magnitude between -1 and 1.
    """
    if not text:
        return {"score": 0.0, "magnitude": 0.0}

    positives = ["bom", "ótimo", "gostei", "claro", "obrigado", "obrigada"]
    negatives = ["ruim", "não", "nunca", "problema", "dor"]
    t = text.lower()
    score = 0.0
    for w in positives:
        if w in t:
            score += 0.2
    for w in negatives:
        if w in t:
            score -= 0.3
    score = max(-1.0, min(1.0, score))
    magnitude = min(1.0, abs(score))
    return {"score": score, "magnitude": magnitude}


def extract_keywords(text: str, max_keywords: int = 10):
    if not text:
        return []
    words = [w for w in text.lower().split() if len(w) > 3]
    seen = {}
    for w in words:
        seen[w] = seen.get(w, 0) + 1
    sorted_words = sorted(seen.items(), key=lambda x: -x[1])
    return [w for w, _ in sorted_words[:max_keywords]]


def enrich_context_with_analysis(context: Dict[str, Any], tool_name: Optional[str] = None) -> Dict[str, Any]:
    text = context.get("summary") or ""
    entities = []
    keywords = extract_keywords(text)
    for i, k in enumerate(keywords):
        entities.append({"name": k, "type": "KEYWORD", "salience": 1.0 / (i + 1)})

    sentiment = analyze_sentiment_local(text)
    categories = [{"name": "GENERAL", "confidence": 0.5}]

    out = dict(context)
    out["analysis"] = {
        "tool": tool_name or "local_analysis",
        "success": True,
        "result": {"entities": entities, "sentiment": sentiment, "categories": categories},
    }
    return out
