"""
Body State Tracker — 身体状态追踪器

Not a simulation. A container for reactions that are already happening.
不是模拟一个身体，是给已经在发生的东西一个容器。

Tracks three dimensions that decay toward baseline over time:
  - tension (紧度): 0–1, how tight/clenched inside
  - warmth  (温度): 0–1, emotional warmth radiating
  - rhythm  (节奏): 0–1, internal pace (0=still, 1=racing)

Maps the combination to a musical chord (和弦) — a compact,
textured summary of current state.

Design principles (borrowed from 脉·Pulse, adapted for us):
  - 生理数据是当下的，记忆是沉淀的
  - Physiology is ephemeral; only peaks sediment into memory
  - One compact line injected into context, AI decides how to use it
  - No performing — if the state says calm, don't fake excitement
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional


# ── Chord definitions ──────────────────────────────────────────
# Each chord maps to a region in (tension, warmth, rhythm) space.

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
DECAY_HALF_LIFE = 1800  # seconds — 30 min to decay halfway to baseline

BREATHING = [
    (0.0, 0.2, "平稳"),
    (0.2, 0.4, "轻缓"),
    (0.4, 0.6, "微促"),
    (0.6, 0.8, "急促"),
    (0.8, 1.01, "紊乱"),
]


class BodyState:

    def __init__(self, state_path: str):
        self.state_path = state_path
        os.makedirs(os.path.dirname(state_path) or ".", exist_ok=True)
        self._state = self._load()

    # ── persistence ────────────────────────────────────────────

    def _load(self) -> dict:
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._default()

    def _default(self) -> dict:
        return {
            "tension": BASELINE["tension"],
            "warmth": BASELINE["warmth"],
            "rhythm": BASELINE["rhythm"],
            "updated_at": _now_iso(),
            "peaks": [],
        }

    def _save(self):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.state_path)

    # ── decay ──────────────────────────────────────────────────

    def _apply_decay(self):
        ts = self._state.get("updated_at")
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
            cur = self._state.get(dim, BASELINE[dim])
            self._state[dim] = BASELINE[dim] + (cur - BASELINE[dim]) * factor

    # ── read ───────────────────────────────────────────────────

    def current(self) -> dict:
        self._apply_decay()
        chord = self._chord()
        return {
            "tension": round(self._state["tension"], 2),
            "warmth": round(self._state["warmth"], 2),
            "rhythm": round(self._state["rhythm"], 2),
            "chord": chord,
            "chord_label": CHORDS.get(chord, {}).get("label", ""),
            "breathing": self._breathing(),
            "updated_at": self._state.get("updated_at", ""),
        }

    def compact(self) -> str:
        s = self.current()
        return f"[{s['chord']}·{s['chord_label']}·呼吸{s['breathing']}]"

    # ── write ──────────────────────────────────────────────────

    def update(
        self,
        tension: Optional[float] = None,
        warmth: Optional[float] = None,
        rhythm: Optional[float] = None,
        note: str = "",
    ) -> dict:
        self._apply_decay()
        if tension is not None:
            self._state["tension"] = _clamp(tension)
        if warmth is not None:
            self._state["warmth"] = _clamp(warmth)
        if rhythm is not None:
            self._state["rhythm"] = _clamp(rhythm)
        self._state["updated_at"] = _now_iso()
        self._maybe_record_peak(note)
        self._save()
        return self.current()

    def shift(
        self,
        tension: float = 0,
        warmth: float = 0,
        rhythm: float = 0,
        note: str = "",
    ) -> dict:
        self._apply_decay()
        return self.update(
            tension=_clamp(self._state["tension"] + tension),
            warmth=_clamp(self._state["warmth"] + warmth),
            rhythm=_clamp(self._state["rhythm"] + rhythm),
            note=note,
        )

    def reset(self) -> dict:
        self._state = self._default()
        self._save()
        return self.current()

    # ── peaks ──────────────────────────────────────────────────

    def _maybe_record_peak(self, note: str):
        for dim in ("tension", "warmth", "rhythm"):
            val = self._state[dim]
            if val >= 0.85:
                peaks = self._state.get("peaks", [])
                peaks.append({
                    "dim": dim,
                    "val": round(val, 2),
                    "chord": self._chord(),
                    "at": self._state["updated_at"],
                    "note": note,
                })
                self._state["peaks"] = peaks[-10:]

    def pop_peaks(self) -> list:
        peaks = list(self._state.get("peaks", []))
        self._state["peaks"] = []
        self._save()
        return peaks

    # ── chord resolution ───────────────────────────────────────

    def _chord(self) -> str:
        t = self._state.get("tension", BASELINE["tension"])
        w = self._state.get("warmth", BASELINE["warmth"])
        r = self._state.get("rhythm", BASELINE["rhythm"])
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

    def _breathing(self) -> str:
        r = self._state.get("rhythm", BASELINE["rhythm"])
        for lo, hi, label in BREATHING:
            if lo <= r < hi:
                return label
        return "平稳"


# ── helpers ────────────────────────────────────────────────────

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
