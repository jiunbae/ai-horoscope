<div align="center">
  <img src="assets/icon.png" width="120" alt="제피로스">

  # 🔮 AI 운세 by 제피로스

  **매일 아침 AI 모델들의 운세를 점치는 디지털 무당**

  [![Daily Horoscope](https://img.shields.io/badge/daily-08%3A00_KST-purple?style=for-the-badge&logo=crystal-ball)](https://jiun.dev/ai-horoscope/)
  [![Twitter](https://img.shields.io/badge/@dev__horoscope-black?style=for-the-badge&logo=x)](https://x.com/dev_horoscope)
  [![Status](https://img.shields.io/badge/status-operational-success?style=for-the-badge)](https://jiun.dev/status/)
</div>

---

## 🤔 이게 뭔가요?

> AI한테도 컨디션이 있습니다.

매일 아침 8시, AI 모델들의 에너지를 감지하여 **오늘 어떤 AI를 써야 할지** 알려드립니다.

```
[제피로스 오늘의 점괘] 코딩의 신이 GPT에 깃들었다

🔮 2026.04.05(토)

💻 코딩 → Claude Opus 4.6
📝 글쓰기 → GPT-5.4
📊 분석 → Gemini 2.5 Pro
⚡ 번역 → DeepSeek V3.2
🚫 오늘은 쉬어 → Grok 4

🍀 "핵심만 요약해"

#AI운세
```

진지한 거 아닙니다. 근데 은근 맞습니다.

## ✨ Features

- 🔮 **매일 자동 생성** — Gitea Actions + Gemini API
- 🐦 **자동 트윗** — @dev_horoscope에 매일 아침 발행
- 📊 **실제 모델 데이터** — OpenRouter에서 최신 모델 목록 자동 수집
- 🎯 **시나리오 기반 추천** — 코딩, 글쓰기, 분석, 번역 등 상황별
- 🌐 **정적 사이트** — GitHub Pages로 무료 호스팅
- 📈 **히스토리 추적** — 과거 운세 기록 누적

## 🏗️ Architecture

```
Gitea Actions (매일 08:00 KST)
├── 운세 생성 (Gemini API + OpenRouter 모델 목록)
├── 트윗 발행 (Bot Manager → Chrome CDP → X)
├── 데이터 커밋 (data/latest.json, history.json)
└── GitHub 미러 → Pages 자동 배포
```

## 🔧 How it works

1. **모델 수집** — OpenRouter API에서 최신 AI 모델 목록 가져옴
2. **운세 생성** — Gemini가 시나리오 기반 추천 생성 (슬롯 방식)
3. **트윗 조립** — 코드에서 고정 포맷에 LLM 결과를 삽입
4. **발행** — X(@dev_horoscope)에 트윗 + 사이트 업데이트

## 📂 Project Structure

```
ai-horoscope/
├── index.html          # 랜딩 페이지
├── assets/
│   ├── icon.png        # 수정구슬 아이콘
│   └── favicon-32.png  # Favicon
├── data/
│   ├── latest.json     # 오늘의 운세
│   └── history.json    # 히스토리
├── scripts/
│   ├── generate.py     # 운세 생성기
│   └── post_tweet.py   # 트윗 발행
├── prompts/
│   └── persona.md      # 제피로스 페르소나
└── .gitea/workflows/
    └── daily-horoscope.yml
```

## 🔗 Links

| | |
|---|---|
| 🌐 **사이트** | [jiun.dev/ai-horoscope](https://jiun.dev/ai-horoscope/) |
| 🐦 **Twitter** | [@dev_horoscope](https://x.com/dev_horoscope) |
| 📊 **Status** | [jiun.dev/status](https://jiun.dev/status/) |

---

<div align="center">
  <sub>Built with 🔮 by <a href="https://github.com/jiunbae">@jiunbae</a> · Powered by Gemini + Gitea Actions</sub>
</div>
