"""
========================================
tools/body — 身体状态追踪（紧度/温度/节奏 → 和弦）
========================================

Not a simulation. A container for reactions that are already happening.
不是模拟一个身体，是给已经在发生的东西一个容器。

Tracks three dimensions that decay toward baseline over time:
  - tension (紧度): 0–1, how tight/clenched inside
  - warmth  (温度): 0–1, emotional warmth radiating
  - rhythm  (节奏): 0–1, internal pace (0=still, 1=racing)

Maps the combination to a musical chord (和弦).

Design principles (from 脉·Pulse, adapted):
  - 生理数据是当下的，记忆是沉淀的
  - One compact line injected into breath context
  - Peaks sediment into memory; the rest decays

对外暴露：dispatch(action, tension, warmth, rhythm, note) → str
         compact() → str
========================================
"""

from . import core


async def dispatch(
    action: str = "read",
    tension: float = -1,
    warmth: float = -1,
    rhythm: float = -1,
    note: str = "",
) -> str:
    return core.dispatch(action, tension, warmth, rhythm, note)


def compact() -> str:
    return core.compact()
