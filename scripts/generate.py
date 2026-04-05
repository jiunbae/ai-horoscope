#!/usr/bin/env python3
"""
Generate daily AI horoscope and save as static data.

Standalone script — no imports from dev-trend-twitter-bot.
Uses Google Gemini API for generation, OpenRouter for model list.
"""

import os
import json
import asyncio
import html
import re
import httpx
import google.generativeai as genai
from datetime import datetime, timezone, timedelta
from pathlib import Path

# =============================================================================
# Constants
# =============================================================================

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PERSONA_PATH = ROOT / "prompts" / "persona.md"

MODELS = [
    "Claude Opus 4.6",
    "Claude Sonnet 4.6",
    "GPT-5.4 Codex",
    "Gemini 3.1 Pro",
    "Gemini 3.1 Flash",
    "Grok 3",
    "Kimi k2",
    "Qwen 3",
]

DAY_NAMES_KO = {
    "Sunday": "일요일", "Monday": "월요일", "Tuesday": "화요일",
    "Wednesday": "수요일", "Thursday": "목요일", "Friday": "금요일",
    "Saturday": "토요일",
}

DAY_NAMES_KO_SHORT = {
    "Sunday": "일", "Monday": "월", "Tuesday": "화",
    "Wednesday": "수", "Thursday": "목", "Friday": "금",
    "Saturday": "토",
}

# =============================================================================
# Seeded PRNG — exact port of TypeScript mulberry32
# =============================================================================

def _to_int32(x: int) -> int:
    x = x & 0xFFFFFFFF
    if x >= 0x80000000:
        return x - 0x100000000
    return x


def _to_uint32(x: int) -> int:
    return x & 0xFFFFFFFF


def _unsigned_right_shift(value: int, shift: int) -> int:
    return (_to_uint32(value)) >> shift


def _imul(a: int, b: int) -> int:
    a = _to_uint32(a)
    b = _to_uint32(b)
    result = (a * b) & 0xFFFFFFFF
    if result >= 0x80000000:
        return result - 0x100000000
    return result


def seeded_random(seed: int):
    state = [_to_int32(seed)]

    def rng() -> float:
        state[0] = _to_int32(state[0] + 0x6D2B79F5)
        s = state[0]
        t = _imul(s ^ _unsigned_right_shift(s, 15), _to_int32(1 | _to_uint32(s)))
        t = _to_int32(t + _imul(t ^ _unsigned_right_shift(t, 7), _to_int32(61 | _to_uint32(t)))) ^ t
        return _unsigned_right_shift(t ^ _unsigned_right_shift(t, 14), 0) / 4294967296

    return rng


def date_seed(date_str: str) -> int:
    h = 0
    for c in date_str:
        h = _to_int32((h << 5) - h + ord(c))
    return h


def generate_rankings(date_str: str):
    rng = seeded_random(date_seed(date_str))
    scored = [(rng(), model) for model in MODELS]
    scored.sort(key=lambda x: x[0], reverse=True)
    sorted_models = [m for _, m in scored]

    top = sorted_models[0]
    avoid = sorted_models[-1]
    middle_idx = 2 + int(rng() * 4)
    dark_horse = sorted_models[middle_idx]
    combo = (sorted_models[0], sorted_models[1])

    return {
        "top": top,
        "avoid": avoid,
        "dark_horse": dark_horse,
        "combo": combo,
        "top_rank": 1,
        "avoid_rank": len(MODELS),
        "dark_horse_rank": middle_idx + 1,
    }


# =============================================================================
# OpenRouter model context
# =============================================================================

async def fetch_model_context() -> dict:
    """Fetch real-time model list from OpenRouter API."""
    priority_ids = [
        "anthropic/claude-opus-4.6",
        "anthropic/claude-sonnet-4.6",
        "openai/gpt-5.4",
        "openai/gpt-5.3-codex",
        "google/gemini-2.5-pro",
        "google/gemini-2.5-flash",
        "x-ai/grok-4",
        "qwen/qwen3-235b-a22b",
        "deepseek/deepseek-v3.2",
        "meta-llama/llama-4-maverick",
        "moonshot/kimi-k2",
    ]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://openrouter.ai/api/v1/models")
            if resp.status_code != 200:
                raise ValueError(f"OpenRouter API returned {resp.status_code}")

            data = resp.json()
            models = data.get("data", [])

            flagships = []
            model_map = {m["id"]: m for m in models}

            def clean_name(name: str) -> str:
                if ": " in name:
                    return name.split(": ", 1)[1]
                return name

            for pid in priority_ids:
                if pid in model_map:
                    m = model_map[pid]
                    flagships.append(clean_name(m["name"]))

            if len(flagships) < 8:
                for m in models:
                    mid = m.get("id", "")
                    name = m.get("name", "")
                    if any(p in mid for p in ["anthropic/", "openai/", "google/", "x-ai/", "deepseek/", "qwen/", "meta-llama/", "moonshot/"]):
                        cname = clean_name(name)
                        if cname not in flagships and "free" not in mid and "preview" not in mid:
                            flagships.append(cname)
                    if len(flagships) >= 12:
                        break

            model_list = "\n".join(f"- {name}" for name in flagships[:10])

            return {
                "models": flagships[:10],
                "context": (
                    f"아래는 현재(2026년 기준) OpenRouter에 등록된 실제 AI 모델 목록이야. "
                    f"이 목록에 있는 **정확한 모델명**만 사용해. 모델명을 임의로 바꾸거나 만들지 마.\n\n"
                    f"{model_list}\n\n"
                    f"위 모델 중 8개를 골라서 오늘의 운세에 활용해. "
                    f"각 모델의 실제 강점/약점을 너의 지식으로 판단해서 상황별 추천을 만들어."
                )
            }
    except Exception as e:
        print(f"OpenRouter API fetch failed: {e}, using fallback models")
        model_list = "\n".join(f"- {name}" for name in MODELS)
        return {
            "models": MODELS,
            "context": (
                f"아래 모델 목록에서 **정확한 모델명**만 사용해:\n\n"
                f"{model_list}\n\n"
                f"모델명을 임의로 바꾸지 마. 위 목록의 이름을 그대로 써."
            )
        }


# =============================================================================
# Prompt building
# =============================================================================

def load_persona() -> str:
    return PERSONA_PATH.read_text(encoding="utf-8")


def build_prompt(
    rankings: dict,
    date_str: str,
    day_of_week: str,
    recent_history: list | None = None,
    model_context: dict | None = None,
) -> str:
    persona = load_persona()
    day_ko = DAY_NAMES_KO.get(day_of_week, day_of_week)
    day_ko_short = DAY_NAMES_KO_SHORT.get(day_of_week, day_of_week[:1])
    date_display = date_str.replace("-", ".")

    if recent_history:
        history_lines = "\n".join(
            f"- {h['date']}: 원탑={h.get('top_model','?')}, 피해야할={h.get('avoid_model','?')}"
            for h in recent_history
        )
        history_section = f"## 최근 히스토리 (겹치지 않게 참고)\n{history_lines}"
    else:
        history_section = "최근 히스토리 없음 (첫 회차)"

    context_section = ""
    if model_context and model_context.get("context"):
        context_section = f"\n## 모델 동향 참고\n{model_context['context']}\n"

    return f"""{persona}

---

## 오늘의 입력

- 날짜: {date_str} ({day_ko})
- 날짜 표시 형식: {date_display}({day_ko_short})
- 원탑: **{rankings['top']}** (랭킹 {rankings['top_rank']}위)
- 피해야 할 에이전트: **{rankings['avoid']}** (랭킹 {rankings['avoid_rank']}위)
- 다크호스: **{rankings['dark_horse']}** (랭킹 {rankings['dark_horse_rank']}위)
{context_section}
{history_section}

위 배정에 맞게 코멘트를 작성하고, fullTweet을 만들어줘.
topRank, avoidRank, darkHorseRank 값은 위에서 알려준 랭킹 숫자를 그대로 써.
형식 A (단일 트윗 모드)로 출력해.
반드시 JSON 코드블록으로만 응답해."""


# =============================================================================
# LLM response parsing
# =============================================================================

def _sanitize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return html.escape(clean)


def parse_llm_response(raw: str, rankings: dict, date_str: str, day_of_week: str) -> dict:
    """Parse the LLM JSON response into a horoscope result dict."""
    json_match = re.search(r"```json\s*([\s\S]*?)```", raw)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_match = re.search(r'\{[\s\S]*(?:"fullTweet"|"scenario1_model")[\s\S]*\}', raw)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise ValueError(f"No JSON block found in LLM response: {raw[:300]}")

    parsed = json.loads(json_str)

    day_short = DAY_NAMES_KO_SHORT.get(day_of_week, "")

    # Scenario slot mode
    scenarios = []
    for i in range(1, 7):
        emoji = parsed.get(f"scenario{i}_emoji", "")
        task = parsed.get(f"scenario{i}_task", "")
        model = parsed.get(f"scenario{i}_model", "")
        if emoji and task and model:
            scenarios.append({"emoji": emoji, "task": task, "model": model})

    avoid_model = parsed.get("avoid_model", rankings["avoid"])
    avoid_reason = parsed.get("avoid_reason", "")
    lucky_prompt = parsed.get("lucky_prompt", "")
    hook = parsed.get("hook", "")

    # Assemble tweet from template
    date_dots = date_str.replace("-", ".")
    lines = []
    if hook:
        lines.append(f"[제피로스 오늘의 점괘] {hook}")
        lines.append("")
    lines.append(f"\U0001f52e {date_dots}({day_short})")
    lines.append("")
    for s in scenarios:
        lines.append(f"{s['emoji']} {s['task']} \u2192 {s['model']}")
    lines.append(f"\U0001f6ab 오늘은 쉬어 \u2192 {avoid_model}")
    if lucky_prompt:
        lines.append(f"\n\U0001f340 \"{lucky_prompt}\"")
    lines.append("\n#AI\uc6b4\uc138")

    full_tweet = "\n".join(lines)

    top_comment = _sanitize_text(parsed.get("topComment", ""))
    avoid_comment = _sanitize_text(parsed.get("avoidComment", ""))

    return {
        "date": date_str,
        "day_of_week": day_of_week,
        "day_short": day_short,
        "hook": hook,
        "scenarios": scenarios,
        "avoid": {"model": avoid_model, "reason": avoid_reason},
        "lucky_prompt": lucky_prompt,
        "full_tweet": full_tweet,
        "top_comment": top_comment,
        "avoid_comment": avoid_comment,
        "generated_at": datetime.now(KST).isoformat(),
    }


# =============================================================================
# Tweet character counting (Twitter weighted rules)
# =============================================================================

def tweet_char_count(text: str) -> int:
    count = 0
    for ch in text:
        code = ord(ch)
        if (
            (0x1100 <= code <= 0x11FF)
            or (0x2E80 <= code <= 0x9FFF)
            or (0xAC00 <= code <= 0xD7AF)
            or (0xF900 <= code <= 0xFAFF)
            or (0xFE30 <= code <= 0xFE4F)
            or (0xFF00 <= code <= 0xFF60)
            or (0x1F000 <= code <= 0x1FAFF)
            or (0x20000 <= code <= 0x2FA1F)
        ):
            count += 2
        else:
            count += 1
    return count


# =============================================================================
# Gemini API call with round-robin keys
# =============================================================================

async def call_gemini(prompt: str) -> str:
    """Call Gemini API. Supports comma-separated keys for round-robin."""
    keys_str = os.environ.get("GEMINI_API_KEY", "")
    if not keys_str:
        raise RuntimeError("GEMINI_API_KEY environment variable not set")

    keys = [k.strip() for k in keys_str.split(",") if k.strip()]

    for i, key in enumerate(keys):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            if response.text:
                return response.text
            raise ValueError("Empty response from Gemini")
        except Exception as e:
            print(f"Gemini key {i + 1}/{len(keys)} failed: {e}")
            if i == len(keys) - 1:
                raise

    raise RuntimeError("All Gemini keys exhausted")


# =============================================================================
# Save data
# =============================================================================

def save_data(result: dict):
    """Save result to data/latest.json and append to data/history.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Save latest
    latest_path = DATA_DIR / "latest.json"
    latest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {latest_path}")

    # Append to history
    history_path = DATA_DIR / "history.json"
    history = []
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            history = []

    # Build history entry
    entry = {
        "date": result["date"],
        "day_of_week": result["day_of_week"],
        "top_model": result["scenarios"][0]["model"] if result["scenarios"] else "",
        "avoid_model": result["avoid"]["model"],
        "scenarios": result["scenarios"],
        "avoid_reason": result["avoid"]["reason"],
        "lucky_prompt": result["lucky_prompt"],
    }

    # Remove existing entry for same date
    history = [h for h in history if h.get("date") != result["date"]]

    # Prepend new entry
    history.insert(0, entry)

    # Keep last 90 days
    history = history[:90]

    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated {history_path} ({len(history)} entries)")


# =============================================================================
# Main
# =============================================================================

async def main():
    now = datetime.now(KST)
    date_str = now.strftime("%Y-%m-%d")
    day_of_week = now.strftime("%A")

    print(f"Generating horoscope for {date_str} ({day_of_week})")

    # Generate rankings
    rankings = generate_rankings(date_str)
    print(f"Rankings: top={rankings['top']}, avoid={rankings['avoid']}, dark_horse={rankings['dark_horse']}")

    # Fetch model context from OpenRouter
    model_context = await fetch_model_context()
    print(f"Fetched {len(model_context.get('models', []))} models from OpenRouter")

    # Load recent history for deduplication
    history_path = DATA_DIR / "history.json"
    recent_history = None
    if history_path.exists():
        try:
            all_history = json.loads(history_path.read_text(encoding="utf-8"))
            recent_history = all_history[:7]
        except (json.JSONDecodeError, ValueError):
            pass

    # Build prompt
    prompt = build_prompt(rankings, date_str, day_of_week, recent_history, model_context)

    # Try up to 3 times
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            final_prompt = prompt
            if attempt > 0:
                final_prompt += (
                    "\n\n(이전 시도에서 글자수 초과됨. "
                    "더 짧게 작성해줘. 각 코멘트를 15자 이내로.)"
                )

            print(f"LLM call (attempt {attempt + 1})...")
            raw = await call_gemini(final_prompt)

            if not raw or not raw.strip():
                last_error = ValueError("Empty LLM response")
                print(f"Attempt {attempt + 1}: empty response")
                continue

            result = parse_llm_response(raw, rankings, date_str, day_of_week)

            # Validate tweet length
            char_count = tweet_char_count(result["full_tweet"])
            print(f"Tweet char count: {char_count}/280")

            if char_count > 280:
                last_error = ValueError(f"Tweet too long: {char_count} chars")
                print(f"Attempt {attempt + 1}: tweet too long ({char_count} chars)")
                continue

            # Success
            save_data(result)
            print(f"Horoscope generated successfully!")
            print(f"Tweet:\n{result['full_tweet']}")
            return

        except Exception as e:
            last_error = e
            print(f"Attempt {attempt + 1} failed: {e}")

    raise last_error or RuntimeError("Failed to generate horoscope")


if __name__ == "__main__":
    asyncio.run(main())
