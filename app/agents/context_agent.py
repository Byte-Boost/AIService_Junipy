"""Context builder for chat messages.

This module focuses on deriving a concise context summary and simple
topic extraction from a list of chat messages. Database access is handled
by the application database layer; this module intentionally avoids
direct database dependencies so it can be easily tested.
"""

from typing import List, Dict, Any, Optional
from collections import Counter
from datetime import date, datetime
import re

from app.models.models import UserHistory, UserInfo

try:
    from agents.text_analysis import enrich_context_with_analysis
except Exception:

    def enrich_context_with_analysis(
        context: Dict[str, Any], tool_name: Optional[str] = None
    ) -> Dict[str, Any]:
        out = dict(context)
        out.setdefault("analysis", {"note": "text_analysis not available"})
        return out


def build_context_from_messages(
    messages: UserHistory, profile: Optional[UserInfo] = None, max_chars: int = 3000
) -> Dict[str, Any]:
    texts: List[str] = []
    for message in messages:
        txt = None
        for key in ("userMessage", "aiResponse"):
            if hasattr(message, key) and isinstance(getattr(message, key), str):
                txt = getattr(message, key)
                break
        if txt is None:
            txt = " ".join(
                str(value)
                for value in message.dict().values()
                if isinstance(value, (str, int, float))
            )
        if txt:
            texts.append(txt.strip())

    full_text = "\n".join(texts)
    if len(full_text) > max_chars:
        full_text = full_text[-max_chars:]

    last_messages = texts[-20:] if len(texts) > 20 else texts
    summary = "\n".join(last_messages)

    stopwords = {
        "o",
        "a",
        "e",
        "de",
        "do",
        "da",
        "que",
        "para",
        "com",
        "é",
        "em",
        "por",
        "um",
        "uma",
    }
    words = re.findall(r"\w+", full_text.lower(), flags=re.UNICODE)
    words = [word for word in words if word not in stopwords and len(word) > 2]
    top = [word for word, _ in Counter(words).most_common(10)]

    profile_summary = None
    if profile:
        pieces = []
        bd = profile.birthDate
        if bd:
            try:
                if isinstance(bd, str):
                    by = datetime.fromisoformat(bd)
                else:
                    by = bd
                age = date.today().year - by.year
                pieces.append(f"idade: {age}")
            except Exception:
                pass
        if profile.sex:
            pieces.append(f"sexo: {profile.sex}")
        if profile.occupation:
            pieces.append(f"ocupação: {profile.occupation}")
        if profile.consultationReason:
            pieces.append(f"motivo: {profile.consultationReason}")
        if profile.healthConditions:
            pieces.append(f"condições: {', '.join(profile.healthConditions or [])}")
        if profile.allergies:
            pieces.append(f"alergias: {', '.join(profile.allergies or [])}")
        if profile.surgeries:
            pieces.append(f"cirurgias: {', '.join(profile.surgeries or [])}")
        if profile.takesMedication:
            pieces.append(f"medicação: {profile.takesMedication}")
        if profile.medicationDetails:
            pieces.append(f"medicações tomadas: {profile.medicationDetails}")
        if profile.activityType:
            pieces.append(
                f"atividade física: {profile.activityType}, frequência: {profile.activityFrequency}, duração: {profile.activityDuration}"
            )
        if profile.sleepQuality:
            pieces.append(
                f"sono: qualidade {profile.sleepQuality}, acorda à noite: {profile.wakeDuringNight}"
            )
        if profile.bowelFrequency:
            pieces.append(f"frequência intestinal: {profile.bowelFrequency}")
        if profile.stressLevel:
            pieces.append(f"nível de estresse: {profile.stressLevel}")
        if profile.alcoholConsumption:
            pieces.append(f"consumo de álcool: {profile.alcoholConsumption}")
        if profile.smoking:
            pieces.append(f"tabagismo: {profile.smoking}")
        if profile.hydrationLevel:
            pieces.append(f"hidratação: {profile.hydrationLevel}")

        profile_summary = "; ".join(pieces)

    prompt_patch = "Resumo do chat (últimas mensagens):\n" + summary + "\n\n"
    if profile_summary:
        prompt_patch += "Perfil do usuário: " + profile_summary + "\n\n"
    prompt_patch += "Sugestão: inclua esse resumo no início do prompt do agente para manter contexto."

    out = {
        "messages": messages,
        "summary": summary,
        "topics": top,
        "prompt_patch": prompt_patch,
    }
    if profile:
        out["profile"] = profile
    return out
