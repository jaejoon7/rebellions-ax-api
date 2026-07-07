import os
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

# ── Gemini 설정 ──
# 키는 코드에 넣지 않는다 — Cloud Run 서비스의 환경변수(GOOGLE_API_KEY)에서 읽는다.
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash") if GOOGLE_API_KEY else None

app = FastAPI()

# 정적 파일을 이 서버가 직접 서빙하지 않는다 (GitHub Pages가 프론트를 서빙).
# 프론트 도메인만 허용하고 싶으면 allow_origins를 좁혀도 되지만,
# GitHub Pages 사용자명/저장소가 바뀔 수 있어 우선 전체 허용으로 둔다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptRequest(BaseModel):
    text: str


@app.get("/")
def health():
    return {"status": "ok", "gemini_configured": bool(GOOGLE_API_KEY)}


@app.post("/control-cube")
def get_cube_settings(request: PromptRequest):
    if model is None:
        return {"status": "error", "reason": "GOOGLE_API_KEY not configured on server"}

    user_input = request.text

    system_prompt = f"""
너는 Rebellions의 고성능 3D 큐브 그리드 그래픽 컨트롤러야.
사용자의 요구사항(자연어)을 분석해서 디자인 엔진에 주입할 15가지 파라미터를 정확한 JSON 형태로 출력해.

- motion: 'breathe', 'wave', 'pulse', 'cascade', 'static' 중 하나 (*반드시 소문자)
- speed: 0~200 정수
- neon: 0~15 정수
- scale: 0~100 정수
- gridSize: 1~20 정수 (기본값 11)
- gap: 0~200 정수
- angle: 10~60 정수
- zoom: 20~300 정수
- direction: 'up', 'down', 'random' 중 하나
- variation: 0~300 정수
- lineW: 0.0 ~ 2.0 실수
- opacity: 20~100 정수
- fillOp: 0 또는 100 정수
- heightBrightness: true 또는 false 불리언
- hbRange: 0~100 정수

[사용자 요구사항]: "{user_input}"

반드시 다른 설명 없이 아래 예시 규칙을 완벽히 지킨 순수한 JSON 형식으로만 답변해:
{{
    "motion": "wave",
    "speed": 60,
    "neon": 8,
    "scale": 70,
    "gridSize": 12,
    "gap": 15,
    "angle": 30,
    "zoom": 100,
    "direction": "up",
    "variation": 50,
    "lineW": 1.0,
    "opacity": 90,
    "fillOp": 100,
    "heightBrightness": true,
    "hbRange": 50,
    "label": "Cosmic Wave",
    "reason": "요청을 분석하여 이 수치로 세팅한 디자인적 이유 요약"
}}
"""
    try:
        response = model.generate_content(
            system_prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        return json.loads(response.text)
    except Exception as error_message:
        return {"status": "error", "reason": str(error_message)}
