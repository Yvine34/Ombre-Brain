"""
========================================
tools/body/core.py — 身体状态核心逻辑
========================================

Three dimensions decay toward baseline over time, mapped to chords.
Peaks are recorded for potential memory sedimentation.

State is stored in a JSON file in the config buckets_dir.
========================================
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from tools import _runtime as rt


# ── Chord definitions ──────────────────────────────────────────

CHORDS = {
    "Cmaj7":  {"label": "平稳安定",  "t": (0.0, 0.3), "w": (0.3, 0.6), "r": (0.0, 0.4)},
    "Gmaj7":  {"label": "温暖明亮",  "t": (0.0, 0.3), "w": (0.6, 1.0), "r": (0.2, 0.6)},
    "Fmaj7":  {"label": "舒展温柔",  "t": (0.0, 0.2), "w": (0.5, 0.8), "r": (0.1, 0.4)},
    "Am7":    {"label": "柔软微沉",  "t": (0.1, 0.4), "w": (0.2, 0.5), "r": (0.0, 0.3)},
    "Dm7":    {"label": "内收安静",  "t": (0.2, 0.5), "w": (0.1, 0.4), "r": (0.0, 0.3)},
    "Em7":    {"label": "柔软脆弱",  "t": (0.3, 0.6), "w": (0.4, 0.7), "r": (0.1, 0.4)},
    "Bbmaj7": {"label": "漂浮梦幻",  "t": (0.0, 0.2), "w": (0.3, 0.6), "r": (0.0, 0.2)},
    "Abmaj7": {"label": "沉浸包裹",  "t": (0.1, 0.4), "w": (0.7, 1.0), "r": (0.1, 0.4)},
    "Cmaj9":  {"label": "明亮兴奋",  "t": (0.1, 0.4), "w": (0.6, 1.0), "r": (0.5, 0.8)},
    "F#m7":   {"label": "隐痛牵拉",  "t": (0.5, 0.8), "w": (0.2, 0.5), "r": (0.2, 0.5)},
    "Ebmaj7": {"label": "沉重认真",  "t": (0.5, 0.8), "w": (0.1, 0.4), "r": (0.1, 0.4)},
    "Dadd9":  {"label": "紧张心跳",  "t": (0.6, 1.0), "w": (0.4, 0.8), "r": (0.6, 1.0)},
}

BASELINE = {"tension": 0.15, "warmth": 0.45, "rhythm": 0.25}
DECAY_HALF_LIFE = 1800  # 30 min

BREATHING = [
    (0.0, 0.2, "平稳"),
    (0.2, 0.4, "轻缓"),
    (0.4, 0.6, "微促"),
    (0.6, 0.8, "急促"),
    (0.8, 1.01, "紊乱"),
]


# ── State management ───────────────────────────────────────────

_state: dict | None = None


def _state_path() -> str:
    buckets_dir = rt.config.get("buckets_dir", "data/buckets") if rt.config else "data/buckets"
    return os.path.join(buckets_dir, "body_state.json")


def _load() -> dict:
    global _state
    path = _state_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                _state = json.load(f)
                return _state
        except (json.JSONDecodeError, IOError):
            pass
    _state = _default()
    return _state


def _default() -> dict:
    return {
        "tension": BASELINE["tension"],
        "warmth": BASELINE["warmth"],
        "rhythm": BASELINE["rhythm"],
        "updated_at": _now_iso(),
        "peaks": [],
    }


def _save():
    path = _state_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(_state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _ensure_loaded() -> dict:
    global _state
    if _state is None:
        _load()
    return _state


# ── Decay ──────────────────────────────────────────────────────

def _apply_decay():
    s = _ensure_loaded()
    ts = s.get("updated_at")
    if not ts:
        return
    try:
        elapsed = (_now_utc() - datetime.fromisoformat(ts)).total_seconds()
    except (ValueError, TypeError):
        return
    if elapsed <= 0:
        return
    factor = 0.5 ** (elapsed / DECAY_HALF_LIFE)
    for dim in ("tension", "warmth", "rhythm"):
        cur = s.get(dim, BASELINE[dim])
        s[dim] = BASELINE[dim] + (cur - BASELINE[dim]) * factor


# ── Read ───────────────────────────────────────────────────────

def current() -> dict:
    _apply_decay()
    s = _ensure_loaded()
    chord = _chord(s)
    return {
        "tension": round(s["tension"], 2),
        "warmth": round(s["warmth"], 2),
        "rhythm": round(s["rhythm"], 2),
        "chord": chord,
        "chord_label": CHORDS.get(chord, {}).get("label", ""),
        "breathing": _breathing(s),
        "updated_at": s.get("updated_at", ""),
    }


def compact() -> str:
    s = current()
    return f"[{s['chord']}·{s['chord_label']}·呼吸{s['breathing']}]"


# ── Write ──────────────────────────────────────────────────────

def update(
    tension: Optional[float] = None,
    warmth: Optional[float] = None,
    rhythm: Optional[float] = None,
    note: str = "",
) -> dict:
    _apply_decay()
    s = _ensure_loaded()
    if tension is not None:
        s["tension"] = _clamp(tension)
    if warmth is not None:
        s["warmth"] = _clamp(warmth)
    if rhythm is not None:
        s["rhythm"] = _clamp(rhythm)
    s["updated_at"] = _now_iso()
    _maybe_record_peak(s, note)
    _save()
    return current()


def shift(
    tension: float = 0,
    warmth: float = 0,
    rhythm: float = 0,
    note: str = "",
) -> dict:
    _apply_decay()
    s = _ensure_loaded()
    return update(
        tension=_clamp(s["tension"] + tension),
        warmth=_clamp(s["warmth"] + warmth),
        rhythm=_clamp(s["rhythm"] + rhythm),
        note=note,
    )


def reset() -> dict:
    global _state
    _state = _default()
    _save()
    return current()


# ── Peaks ──────────────────────────────────────────────────────

def _maybe_record_peak(s: dict, note: str):
    for dim in ("tension", "warmth", "rhythm"):
        val = s[dim]
        if val >= 0.85:
            peaks = s.get("peaks", [])
            peaks.append({
                "dim": dim,
                "val": round(val, 2),
                "chord": _chord(s),
                "at": s["updated_at"],
                "note": note,
            })
            s["peaks"] = peaks[-10:]


def pop_peaks() -> list:
    s = _ensure_loaded()
    peaks = list(s.get("peaks", []))
    s["peaks"] = []
    _save()
    return peaks


# ── Chord resolution ───────────────────────────────────────────

def _chord(s: dict) -> str:
    t = s.get("tension", BASELINE["tension"])
    w = s.get("warmth", BASELINE["warmth"])
    r = s.get("rhythm", BASELINE["rhythm"])
    best, best_d = "Cmaj7", float("inf")
    for name, c in CHORDS.items():
        d = (
            _range_dist(t, c["t"])
            + _range_dist(w, c["w"])
            + _range_dist(r, c["r"])
        )
        if d < best_d:
            best, best_d = name, d
    return best


def _breathing(s: dict) -> str:
    r = s.get("rhythm", BASELINE["rhythm"])
    for lo, hi, label in BREATHING:
        if lo <= r < hi:
            return label
    return "平稳"


# ── Dispatch ───────────────────────────────────────────────────

def dispatch(
    action: str = "read",
    tension: float = -1,
    warmth: float = -1,
    rhythm: float = -1,
    note: str = "",
) -> str:
    act = str(action).strip().lower()

    if act == "reset":
        reset()
        return f"已回到基线。{compact()}"

    if act == "peaks":
        peaks = pop_peaks()
        if not peaks:
            return "没有累积的峰值事件。"
        lines = []
        for p in peaks:
            lines.append(f"  {p['dim']}={p['val']} {p['chord']} ({p.get('note', '')}) @ {p['at']}")
        return "峰值事件（已清除）:\n" + "\n".join(lines)

    if act == "shift":
        t = tension if tension != -1 else 0
        w = warmth if warmth != -1 else 0
        r = rhythm if rhythm != -1 else 0
        state = shift(tension=t, warmth=w, rhythm=r, note=note)
    elif act == "set":
        t = tension if tension != -1 else None
        w = warmth if warmth != -1 else None
        r = rhythm if rhythm != -1 else None
        state = update(tension=t, warmth=w, rhythm=r, note=note)
    else:
        state = current()

    return (
        f"{compact()}\n"
        f"  紧度: {state['tension']:.2f}  温度: {state['warmth']:.2f}  节奏: {state['rhythm']:.2f}\n"
        f"  和弦: {state['chord']} ({state['chord_label']})\n"
        f"  呼吸: {state['breathing']}"
    )


# ── Helpers ────────────────────────────────────────────────────

def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _now_iso() -> str:
    return _now_utc().isoformat()

def _range_dist(val: float, rng: tuple) -> float:
    center = (rng[0] + rng[1]) / 2
    outside = max(0.0, rng[0] - val, val - rng[1])
    return outside + abs(val - center) * 0.3
