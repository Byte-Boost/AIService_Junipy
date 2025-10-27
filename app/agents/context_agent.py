"""Context builder for chat messages.

This module focuses on deriving a concise context summary and simple
topic extraction from a list of chat messages. Database access is handled
by the application database layer; this module intentionally avoids
direct database dependencies so it can be easily tested.
"""

from typing import List, Dict, Any, Optional
from collections import Counter
import re

try:
	from app.agents.text_analysis import enrich_context_with_analysis
except Exception:
	def enrich_context_with_analysis(context: Dict[str, Any], tool_name: Optional[str] = None) -> Dict[str, Any]:
		out = dict(context)
		out.setdefault("analysis", {"note": "text_analysis not available"})
		return out


def build_context_from_messages(messages: List[Dict[str, Any]], profile: Optional[Dict[str, Any]] = None, max_chars: int = 3000) -> Dict[str, Any]:
	texts: List[str] = []
	for m in messages:
		txt = None
		for k in ("text", "message", "content", "body", "msg"):
			if k in m and isinstance(m[k], str):
				txt = m[k]
				break
		if txt is None:
			txt = " ".join(str(v) for v in m.values() if isinstance(v, (str, int, float)))
		if txt:
			texts.append(txt.strip())

	full_text = "\n".join(texts)
	if len(full_text) > max_chars:
		full_text = full_text[-max_chars:]

	last_messages = texts[-20:] if len(texts) > 20 else texts
	summary = "\n".join(last_messages)

	stopwords = {"o", "a", "e", "de", "do", "da", "que", "para", "com", "é", "em", "por", "um", "uma"}
	words = re.findall(r"\w+", full_text.lower(), flags=re.UNICODE)
	words = [w for w in words if w not in stopwords and len(w) > 2]
	top = [w for w, _ in Counter(words).most_common(10)]

	profile_summary = None
	if profile:
		pieces = []
		bd = profile.get("birthDate") or profile.get("birth_date")
		if bd:
			try:
				from datetime import date, datetime

				if isinstance(bd, str):
					by = datetime.fromisoformat(bd)
				else:
					by = bd
				age = date.today().year - by.year
				pieces.append(f"idade: {age}")
			except Exception:
				pass
		if profile.get("gender"):
			pieces.append(f"sexo: {profile.get('gender')}")
		if profile.get("occupation"):
			pieces.append(f"ocupação: {profile.get('occupation')}")
		if profile.get("consultationReason"):
			pieces.append(f"motivo: {profile.get('consultationReason')}")
		if profile.get("healthConditions"):
			pieces.append(f"condições: {', '.join(profile.get('healthConditions') or [])}")
		if profile.get("allergies"):
			pieces.append(f"alergias: {', '.join(profile.get('allergies') or [])}")
		profile_summary = "; ".join(pieces)

	prompt_patch = ("Resumo do chat (últimas mensagens):\n" + summary + "\n\n")
	if profile_summary:
		prompt_patch += "Perfil do usuário: " + profile_summary + "\n\n"
	prompt_patch += "Sugestão: inclua esse resumo no início do prompt do agente para manter contexto."

	out = {"messages": messages, "summary": summary, "topics": top, "prompt_patch": prompt_patch}
	if profile:
		out["profile"] = profile
	return out
