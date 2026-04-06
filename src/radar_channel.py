"""Radar channel — evaluates soft-disabled strategy channels at confidence >= 65
and posts radar alerts to the free channel.

Channels evaluated: CVD, VWAP, SUPERTREND, ICHIMOKU
These are the 4 soft-disabled channels from PR1.

Radar alert threshold: 65 (vs 76-80 for live signals)
"Watching closely" threshold: 70 (gets variant 3 template)

Per-symbol radar cooldown: 900s (15 min) — prevents spam
Cross-symbol radar rate limit: max 3 radar alerts per hour
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Any, Callable, Coroutine, Dict, Deque, List, Optional

from config import (
    RADAR_ALERT_MIN_CONFIDENCE,
    RADAR_ALERT_WATCHING_CLOSELY_CONFIDENCE,
    RADAR_CHANNEL_ENABLED,
    RADAR_MAX_PER_HOUR,
    RADAR_PER_SYMBOL_COOLDOWN_SECONDS,
)
from src import content_engine
from src.utils import get_logger

log = get_logger("radar_channel")

# Names of the soft-disabled channels that the radar evaluator watches
_RADAR_CHANNEL_NAMES: List[str] = [
    "360_SCALP_CVD",
    "360_SCALP_VWAP",
    "360_SCALP_SUPERTREND",
    "360_SCALP_ICHIMOKU",
]

# How often to run the radar evaluation loop (seconds)
_EVAL_INTERVAL: int = 30


class RadarChannel:
    """Evaluates soft-disabled channels and posts radar alerts to the free channel.

    The radar evaluator runs at lower priority than the main scanner and must
    not add latency to signal generation.

    Parameters
    ----------
    post_to_free:
        Coroutine-function that sends text to the free channel.
    scanner_context_fn:
        Zero-argument callable that returns the current scanner context dict.
        The dict must expose ``"channel_scores"`` — a mapping of
        ``channel_name → {symbol, confidence, setup_name, bias, ...}`` for
        any pair that scored above the radar threshold in the last scan cycle.
    """

    def __init__(
        self,
        post_to_free: Callable[[str], Coroutine],
        scanner_context_fn: Callable[[], Dict[str, Any]],
    ) -> None:
        self._post_free = post_to_free
        self._scanner_context_fn = scanner_context_fn

        # Per-symbol cooldown: symbol → monotonic timestamp of last radar post.
        # Default is float('-inf') so a symbol that has never been alerted always
        # passes the cooldown check regardless of how long the process has been running.
        self._symbol_last_post: Dict[str, float] = {}
        # Sliding window of alert timestamps (last hour)
        self._alert_times: Deque[float] = deque()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Run the radar evaluation loop indefinitely."""
        if not RADAR_CHANNEL_ENABLED:
            log.info("Radar channel disabled — not running")
            return

        log.info("Radar channel started (min_conf=%d)", RADAR_ALERT_MIN_CONFIDENCE)
        while True:
            try:
                await self._evaluate()
            except Exception as exc:
                log.error("Radar evaluation error: %s", exc)
            await asyncio.sleep(_EVAL_INTERVAL)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _evaluate(self) -> None:
        """Check soft-disabled channels for radar-worthy setups."""
        ctx = self._scanner_context_fn()
        channel_scores: Dict[str, Any] = ctx.get("channel_scores", {})

        for channel_name in _RADAR_CHANNEL_NAMES:
            score_data = channel_scores.get(channel_name)
            if not score_data:
                continue

            confidence = float(score_data.get("confidence", 0))
            if confidence < RADAR_ALERT_MIN_CONFIDENCE:
                continue

            symbol: str = score_data.get("symbol", "")
            if not symbol:
                continue

            # Per-symbol cooldown check
            if not self._check_symbol_cooldown(symbol):
                continue

            # Cross-symbol hourly rate limit
            if not self._check_hourly_rate():
                log.debug("Radar rate limit reached — skipping %s", symbol)
                break

            log.info(
                "Radar alert: %s conf=%.0f (channel=%s)",
                symbol, confidence, channel_name,
            )
            await self._post_radar_alert(score_data, confidence, ctx)
            self._record_alert(symbol)

    async def _post_radar_alert(
        self,
        score_data: Dict[str, Any],
        confidence: float,
        engine_ctx: Dict[str, Any],
    ) -> None:
        """Generate and post a radar alert to the free channel."""
        # Use "watching closely" variant for high-confidence setups
        if confidence >= RADAR_ALERT_WATCHING_CLOSELY_CONFIDENCE:
            variant = 3
        else:
            variant = None  # let formatter pick contextually

        ctx = {
            "symbol": score_data.get("symbol", "???"),
            "bias": score_data.get("bias", "NEUTRAL"),
            "confidence": int(confidence),
            "setup_name": score_data.get("setup_name", ""),
            "waiting_for": score_data.get("waiting_for", "confirmation"),
            "level": score_data.get("key_level", ""),
            "current_price": score_data.get("current_price", ""),
            "is_active_market": engine_ctx.get("is_active_market", False),
        }

        try:
            text = await content_engine.generate_content(
                "radar_alert",
                ctx,
                template_variant=variant or 0,
            )
            if text:
                await self._post_free(text)
        except Exception as exc:
            log.error("Radar alert post failed for %s: %s", ctx["symbol"], exc)

    def _check_symbol_cooldown(self, symbol: str) -> bool:
        """Return True if the symbol's cooldown has elapsed."""
        if symbol not in self._symbol_last_post:
            return True  # never alerted — always allow
        last = self._symbol_last_post[symbol]
        return (time.monotonic() - last) >= RADAR_PER_SYMBOL_COOLDOWN_SECONDS

    def _check_hourly_rate(self) -> bool:
        """Return True if fewer than RADAR_MAX_PER_HOUR alerts have been sent in the last hour."""
        now = time.monotonic()
        # Prune timestamps older than 1 hour
        while self._alert_times and (now - self._alert_times[0]) > 3600:
            self._alert_times.popleft()
        return len(self._alert_times) < RADAR_MAX_PER_HOUR

    def _record_alert(self, symbol: str) -> None:
        """Record an alert timestamp for rate limiting."""
        now = time.monotonic()
        self._symbol_last_post[symbol] = now
        self._alert_times.append(now)
