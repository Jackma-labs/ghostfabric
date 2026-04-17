#!/usr/bin/env python3
"""
Sanitized public reference implementation of the GhostFabric DeepConf proxy.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


def env(name: str, default: str) -> str:
    return os.getenv(name, default)


MINDIE_BASE_URL = env("DEEPConf_MINDIE_BASE_URL", "http://127.0.0.1:1035/v1")
MINDIE_BASE_URL_2 = env("DEEPConf_MINDIE_BASE_URL_2", MINDIE_BASE_URL)
MODEL_NAME = env("DEEPConf_MODEL_NAME", "qwen2.5-32b")
VALID_API_KEY = env("DEEPConf_API_KEY", "change-me")
LOG_PATH = Path(env("DEEPConf_LOG_PATH", "./artifacts/deepconf.log"))
ALLOWED_ROOTS = [Path(item).resolve() for item in env("DEEPConf_ALLOWED_ROOTS", "./workspace").split(",") if item.strip()]
ALLOWED_COMMANDS = {
    item.strip()
    for item in env(
        "DEEPConf_ALLOWED_COMMANDS",
        "pwd,ls,cat,head,tail,sed,grep,find,stat,python3,pytest,git",
    ).split(",")
    if item.strip()
}

DEFAULT_NUM_SAMPLES = 4
DEFAULT_MIN_SAMPLES = 1
DEFAULT_GROUP_SIZE = 32
DEFAULT_CONFIDENCE_PERCENTILE = 0.1
DEFAULT_CONFIDENCE_THRESHOLD = 0.88
DEFAULT_MARGIN = 0.15

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_PATH, encoding="utf-8")],
)
logger = logging.getLogger("deepconf-public")

app = FastAPI(title="GhostFabric", version="0.1.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def verify_api_key(authorization: str | None) -> bool:
    if not authorization:
        return False
    if authorization.startswith("Bearer "):
        return authorization[7:] == VALID_API_KEY
    return authorization == VALID_API_KEY


def normalize_content(content: Any) -> str:
    if isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                texts.append(str(part.get("text", "")))
        return "\n".join(texts).strip()
    return "" if content is None else str(content).strip()


def clean_output_text(text: str) -> str:
    return text.replace("<|im_end|>", "").replace("<|endoftext|>", "").strip()


SHELL_META_PATTERN = re.compile(r"[;&|><`]")


def is_allowed_path(path_str: str) -> bool:
    try:
        candidate = Path(path_str).expanduser().resolve()
    except Exception:
        return False
    for root in ALLOWED_ROOTS:
        try:
            candidate.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def validate_command(command: str) -> tuple[bool, str]:
    command = command.strip()
    if not command:
        return False, "empty command"
    if SHELL_META_PATTERN.search(command):
        return False, "shell metacharacters are not allowed"
    parts = command.split()
    if not parts:
        return False, "empty command"
    if parts[0] not in ALLOWED_COMMANDS:
        return False, f"command not allowed: {parts[0]}"
    return True, ""


def run_allowlisted_command(command: str, cwd: str | None = None, timeout: int = 30) -> dict[str, Any]:
    ok, reason = validate_command(command)
    if not ok:
        return {"ok": False, "error": reason}
    if cwd and not is_allowed_path(cwd):
        return {"ok": False, "error": "cwd is outside allowed roots"}
    try:
        proc = subprocess.run(
            command.split(),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def sanitize_messages(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    sanitized: list[dict[str, str]] = []
    for msg in messages:
        role = str(msg.get("role", "user"))
        content = clean_output_text(normalize_content(msg.get("content", "")))
        if role not in {"system", "user", "assistant"}:
            if content:
                sanitized.append({"role": "user", "content": f"[{role}]\n{content}"})
            continue
        if content:
            sanitized.append({"role": role, "content": content})
    return sanitized


async def call_backend(messages: list[dict[str, str]], *, temperature: float, max_tokens: int, top_p: float, base_url: str) -> dict[str, Any]:
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "stream": False,
        "logprobs": True,
    }
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(f"{base_url}/chat/completions", json=payload)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()


def compute_trace_confidence(logprobs_data: list[dict[str, Any]], group_size: int) -> float:
    token_confs = []
    for token in logprobs_data:
        lp = token.get("logprob", -10.0)
        token_confs.append(math.exp(lp) if lp > -100 else 0.0)
    if not token_confs:
        return 0.0
    if len(token_confs) < group_size:
        return sum(token_confs) / max(len(token_confs), 1)
    groups = []
    for i in range(len(token_confs) - group_size + 1):
        groups.append(sum(token_confs[i : i + group_size]) / group_size)
    groups.sort()
    bottom = max(1, int(len(groups) * DEFAULT_CONFIDENCE_PERCENTILE))
    return sum(groups[:bottom]) / bottom


def extract_answer(content: str) -> str:
    if "</think>" in content:
        return clean_output_text(content.split("</think>")[-1])
    return clean_output_text(content)


async def deepconf_online(messages: list[dict[str, str]], *, temperature: float, max_tokens: int, top_p: float, num_samples: int, min_samples: int, group_size: int) -> dict[str, Any]:
    backends = [MINDIE_BASE_URL, MINDIE_BASE_URL_2]
    traces: list[dict[str, Any]] = []
    total_prompt_tokens = 0
    total_completion_tokens = 0

    stages = [max(1, min_samples)]
    while stages[-1] < num_samples:
        stages.append(min(num_samples, stages[-1] * 2))

    for stage in stages:
        pending = stage - len(traces)
        if pending <= 0:
            continue
        results = await asyncio.gather(
            *[
                call_backend(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    base_url=backends[(len(traces) + i) % len(backends)],
                )
                for i in range(pending)
            ],
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, Exception):
                logger.warning("sample failed: %s", result)
                continue
            choice = result.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "")
            logprobs = choice.get("logprobs", {}).get("content", [])
            usage = result.get("usage", {})
            total_prompt_tokens += usage.get("prompt_tokens", 0)
            total_completion_tokens += usage.get("completion_tokens", 0)
            traces.append({"answer": extract_answer(content), "confidence": compute_trace_confidence(logprobs, group_size)})
        if len(traces) >= min_samples:
            ranked = sorted(traces, key=lambda item: item["confidence"], reverse=True)
            if len(ranked) == 1:
                break
            margin = ranked[0]["confidence"] - ranked[1]["confidence"]
            if ranked[0]["confidence"] >= DEFAULT_CONFIDENCE_THRESHOLD and margin >= DEFAULT_MARGIN:
                break

    if not traces:
        raise HTTPException(status_code=502, detail="All samples failed")

    best = sorted(traces, key=lambda item: item["confidence"], reverse=True)[0]
    return {
        "id": f"deepconf-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": f"{MODEL_NAME}-deepconf",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": best["answer"]}, "finish_reason": "stop"}],
        "usage": {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
        },
        "deepconf_meta": {"mode": "online", "used_samples": len(traces), "best_confidence": round(best["confidence"], 4)},
    }


AGENT_PLANNER_PROMPT = """You are a tool-calling planner.
Return exactly one JSON object.
If you can answer directly: {"decision":"answer","answer":"..."}
If you need tools: {"decision":"tool_calls","tool_calls":[{"name":"tool_name","arguments":{...}}]}
Use only provided tool names.
"""


def format_tool_catalog(tools: list[dict[str, Any]]) -> str:
    lines = []
    for tool in tools:
        fn = tool.get("function", {})
        lines.append(f"- {fn.get('name', 'tool')}: {fn.get('description', '')}")
    return "\n".join(lines) if lines else "- (no tools)"


def extract_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        obj = json.loads(text[start : end + 1])
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


async def agent_plan(messages: list[dict[str, Any]], tools: list[dict[str, Any]], *, temperature: float, max_tokens: int, top_p: float) -> dict[str, Any]:
    planner_messages = [
        {"role": "system", "content": AGENT_PLANNER_PROMPT},
        {"role": "user", "content": f"Available tools:\n{format_tool_catalog(tools)}\n\nConversation:\n{json.dumps(messages, ensure_ascii=False)}"},
    ]
    data = await call_backend(sanitize_messages(planner_messages), temperature=temperature, max_tokens=max_tokens, top_p=top_p, base_url=MINDIE_BASE_URL)
    raw = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    payload = extract_json(raw or "")
    if payload and payload.get("decision") == "tool_calls":
        tool_calls = []
        for item in payload.get("tool_calls", []):
            tool_calls.append({
                "id": f"call_{uuid.uuid4().hex[:12]}",
                "type": "function",
                "function": {"name": item.get("name", "tool"), "arguments": json.dumps(item.get("arguments", {}), ensure_ascii=False)},
            })
        return {
            "id": f"agent-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": f"{MODEL_NAME}-agent",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": None, "tool_calls": tool_calls}, "finish_reason": "tool_calls"}],
        }
    answer = clean_output_text(payload.get("answer", raw) if payload else raw)
    return {
        "id": f"agent-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": f"{MODEL_NAME}-agent",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": answer}, "finish_reason": "stop"}],
    }


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "model": MODEL_NAME}


@app.get("/v1/models")
async def models() -> dict[str, Any]:
    now = int(time.time())
    return {
        "object": "list",
        "data": [
            {"id": MODEL_NAME, "object": "model", "created": now, "owned_by": "deepconf-public"},
            {"id": f"{MODEL_NAME}-deepconf", "object": "model", "created": now, "owned_by": "deepconf-public"},
            {"id": f"{MODEL_NAME}-agent", "object": "model", "created": now, "owned_by": "deepconf-public"},
        ],
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    auth = request.headers.get("Authorization")
    if not verify_api_key(auth):
        raise HTTPException(status_code=401, detail={"error": {"message": "Invalid API key"}})

    body = await request.json()
    messages = sanitize_messages(body.get("messages", []))
    temperature = float(body.get("temperature", 0.7))
    max_tokens = int(body.get("max_tokens", 1024))
    top_p = float(body.get("top_p", 0.95))
    tools = body.get("tools") or []
    model = body.get("model", MODEL_NAME)

    if tools:
        return JSONResponse(content=await agent_plan(body.get("messages", []), tools, temperature=temperature, max_tokens=max_tokens, top_p=top_p))

    if model.endswith("-deepconf"):
        deepconf = body.get("deepconf", {})
        return JSONResponse(content=await deepconf_online(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            num_samples=int(deepconf.get("num_samples", DEFAULT_NUM_SAMPLES)),
            min_samples=int(deepconf.get("min_samples", DEFAULT_MIN_SAMPLES)),
            group_size=int(deepconf.get("group_size", DEFAULT_GROUP_SIZE)),
        ))

    data = await call_backend(messages, temperature=temperature, max_tokens=max_tokens, top_p=top_p, base_url=MINDIE_BASE_URL)
    for choice in data.get("choices", []):
        msg = choice.get("message", {})
        if isinstance(msg.get("content"), str):
            msg["content"] = clean_output_text(msg["content"])
    return JSONResponse(content=data)
