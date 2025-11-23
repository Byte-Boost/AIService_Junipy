import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

from app.agents.root_agent import root_runner
from app.context import jwt_token_ctx
from google.genai import types

MOCK_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyX3Rlc3QiLCJ1c2VyX2lkIjoidXNlcl90ZXN0In0.mock"


async def ensure_session(service, app_name: str, user_id: str, session_id: str, retries: int = 8, delay: float = 0.05) -> bool:
    for _ in range(retries):
        try:
            res = service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
            if asyncio.iscoroutine(res):
                await res
        except Exception as e:
            if e.__class__.__name__ == "AlreadyExistsError":
                pass
            else:
                pass

        try:
            sess = service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
            if asyncio.iscoroutine(sess):
                sess = await sess
            if sess:
                return True
        except Exception:
            pass

        await asyncio.sleep(delay)

    return False


async def test_root_agent():
    jwt_token_ctx.set(MOCK_TOKEN)
    user_id = "user_default"
    session_id = "root_test_session"

    print("DEBUG: root_runner ->", type(root_runner))
    print("DEBUG: session_service ->", type(root_runner.session_service))
    try:
        print("DEBUG: session_service id ->", id(root_runner.session_service))
    except Exception:
        pass

    try:
        existing = root_runner.session_service.get_session(app_name="agents", user_id=user_id, session_id=session_id)
        if asyncio.iscoroutine(existing):
            existing = await existing
        print("DEBUG: pre-create get_session ->", bool(existing))
    except Exception as exc:
        print("DEBUG: pre-create get_session error ->", exc)

    runner_app_name = getattr(root_runner, "app_name", "agents")
    created = await ensure_session(root_runner.session_service, app_name=runner_app_name, user_id=user_id, session_id=session_id)
    if not created:
        print("Error: failed to create or verify session")
        return

    try:
        existing = root_runner.session_service.get_session(app_name="agents", user_id=user_id, session_id=session_id)
        if asyncio.iscoroutine(existing):
            existing = await existing
        print("DEBUG: post-create get_session ->", bool(existing))
    except Exception as exc:
        print("DEBUG: post-create get_session error ->", exc)

    test_cases = [
        ("Database Update", "Atualize meu peso para 78kg"),
    ]

    # keywords to look for in agent responses that indicate routing
    agent_keywords = {
        "security_agent": "security_agent",
        "diet_agent": "diet_agent",
        "analysis_agent": "analysis_agent",
        "diet_validation_agent": "diet_validation_agent",
        "database_agent": "database_agent",
    }

    for name, prompt in test_cases:
        print("=" * 70)
        print(f"Test: {name}")
        print(prompt)
        try:
            user_content = types.Content(role="user", parts=[types.Part(text=prompt)])
            response_text = ""
            redirected = None
            async for event in root_runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_content,
            ):
                try:
                    content = getattr(event, "content", None)
                except Exception:
                    content = None

                if content and getattr(content, "parts", None):
                    part_text = content.parts[0].text if content.parts else None
                    if part_text:
                        print("EVENT CONTENT:")
                        print(part_text)
                        low = part_text.lower()
                        for key, val in agent_keywords.items():
                            if key in low or val in low:
                                redirected = key
                                print(f"Detected routing keyword: {key}")
                                break

                # Heuristic introspection: look for event attributes mentioning agent/tool
                try:
                    for attr in dir(event):
                        if attr.startswith("_"):
                            continue
                        if attr in ("content", "is_final_response"):
                            continue
                        if any(k in attr.lower() for k in ("agent", "tool", "destination", "target", "runner", "route", "routing")):
                            try:
                                val = getattr(event, attr)
                                if val is None:
                                    continue
                                # avoid huge prints; convert small primitives and repr for others
                                if isinstance(val, (str, int, float, bool)):
                                    sval = val
                                else:
                                    sval = repr(val)
                                print(f"EVENT ATTR {attr}: {sval}")
                                # try to detect agent name in attribute value
                                low = str(sval).lower()
                                for key in agent_keywords.keys():
                                    if key in low:
                                        redirected = key
                                        print(f"Detected routing via attr {attr}: {key}")
                                        break
                            except Exception:
                                pass
                except Exception:
                    pass

                if getattr(event, "is_final_response", lambda: False)() and content and content.parts:
                    response_text = content.parts[0].text

            if redirected:
                print(f"Redirected to: {redirected}")
            else:
                print("Redirected to: <not detected in text>")

            print("Agent final response:")
            print(response_text or "<no response>")
        except Exception as exc:
            print("Error:", exc)

    print("=" * 70)
    print("All tests completed")


if __name__ == "__main__":
    asyncio.run(test_root_agent())
