"""
Statistics collector for node metrics aggregation
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class RequestRecord:
    """Record of a single request"""
    request_id: str
    timestamp: datetime
    model: str
    prompt_tokens: int
    completion_tokens: int
    processing_time: float
    cost_sol: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class EarningsRecord:
    """Record of earnings/payment"""
    timestamp: datetime
    amount_sol: float
    transaction_signature: Optional[str] = None
    request_id: Optional[str] = None
    round_id: Optional[str] = None
    payment_type: str = "inference"  # inference, training_reward
    status: str = "confirmed"  # pending, confirmed, failed


class StatsCollector:
    """Collects and aggregates node statistics"""

    def __init__(self, node: Any, max_request_history: int = 10000, max_earnings_history: int = 1000):
        self.node = node
        self.request_history: deque[RequestRecord] = deque(maxlen=max_request_history)
        self.earnings_history: deque[EarningsRecord] = deque(maxlen=max_earnings_history)
        self.start_time = datetime.utcnow()
        self._lock = asyncio.Lock()

        # Aggregated stats
        self._total_earnings_sol = 0.0
        self._pending_earnings_sol = 0.0

    async def record_request(self, record: RequestRecord) -> None:
        """Record a completed request"""
        async with self._lock:
            self.request_history.append(record)
            logger.debug(f"Recorded request {record.request_id}")

    async def record_earning(self, record: EarningsRecord) -> None:
        """Record an earning event"""
        async with self._lock:
            self.earnings_history.append(record)
            if record.status == "confirmed":
                self._total_earnings_sol += record.amount_sol
            elif record.status == "pending":
                self._pending_earnings_sol += record.amount_sol
            logger.debug(f"Recorded earning: {record.amount_sol} SOL")

    async def confirm_pending_earning(self, transaction_signature: str, amount_sol: float) -> None:
        """Move pending earning to confirmed"""
        async with self._lock:
            self._pending_earnings_sol -= amount_sol
            self._total_earnings_sol += amount_sol

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current aggregated statistics"""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        # Get base stats from node
        node_stats = getattr(self.node, 'stats', {})

        # Calculate time-windowed stats
        requests_last_hour = len([r for r in self.request_history if r.timestamp > hour_ago])
        requests_last_24h = len([r for r in self.request_history if r.timestamp > day_ago])

        # Calculate earnings
        earnings_last_24h = sum(
            e.amount_sol for e in self.earnings_history
            if e.timestamp > day_ago and e.status == "confirmed"
        )

        # Calculate success rate from recent requests
        recent_requests = [r for r in self.request_history if r.timestamp > hour_ago]
        if recent_requests:
            success_rate = len([r for r in recent_requests if r.success]) / len(recent_requests)
        else:
            success_rate = 1.0

        # Calculate average response time
        successful_requests = [r for r in recent_requests if r.success]
        if successful_requests:
            avg_response_time = sum(r.processing_time for r in successful_requests) / len(successful_requests)
        else:
            avg_response_time = 0.0

        # Calculate uptime
        uptime_seconds = (now - self.start_time).total_seconds()

        return {
            "requests_served": node_stats.get("requests_served", 0),
            "requests_succeeded": node_stats.get("requests_served", 0) - node_stats.get("errors", 0),
            "requests_failed": node_stats.get("errors", 0),
            "total_tokens_generated": node_stats.get("total_tokens_generated", 0),
            "total_processing_time": node_stats.get("total_processing_time", 0.0),
            "average_response_time": avg_response_time,
            "success_rate": success_rate,
            "total_earnings_sol": self._total_earnings_sol,
            "pending_earnings_sol": self._pending_earnings_sol,
            "last_payment_received": self._get_last_payment_time(),
            "requests_last_hour": requests_last_hour,
            "requests_last_24h": requests_last_24h,
            "earnings_last_24h": earnings_last_24h,
            "uptime_seconds": uptime_seconds,
        }

    def get_request_history(
        self,
        limit: int = 100,
        offset: int = 0,
        success_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get paginated request history"""
        records = list(self.request_history)

        if success_only:
            records = [r for r in records if r.success]

        # Sort by timestamp descending (newest first)
        records.sort(key=lambda r: r.timestamp, reverse=True)

        # Apply pagination
        paginated = records[offset:offset + limit]

        return [
            {
                "request_id": r.request_id,
                "timestamp": r.timestamp.isoformat(),
                "model": r.model,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "processing_time": r.processing_time,
                "cost_sol": r.cost_sol,
                "success": r.success,
                "error_message": r.error_message,
            }
            for r in paginated
        ]

    def get_earnings_history(
        self,
        limit: int = 100,
        offset: int = 0,
        payment_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get paginated earnings history"""
        records = list(self.earnings_history)

        if payment_type:
            records = [r for r in records if r.payment_type == payment_type]

        # Sort by timestamp descending
        records.sort(key=lambda r: r.timestamp, reverse=True)

        # Apply pagination
        paginated = records[offset:offset + limit]

        return [
            {
                "timestamp": r.timestamp.isoformat(),
                "amount_sol": r.amount_sol,
                "transaction_signature": r.transaction_signature,
                "request_id": r.request_id,
                "round_id": r.round_id,
                "payment_type": r.payment_type,
                "status": r.status,
            }
            for r in paginated
        ]

    def get_earnings_summary(self) -> Dict[str, Any]:
        """Get earnings summary with breakdown"""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        confirmed_earnings = [e for e in self.earnings_history if e.status == "confirmed"]

        today_earnings = sum(
            e.amount_sol for e in confirmed_earnings if e.timestamp >= today_start
        )
        week_earnings = sum(
            e.amount_sol for e in confirmed_earnings if e.timestamp >= week_ago
        )
        month_earnings = sum(
            e.amount_sol for e in confirmed_earnings if e.timestamp >= month_ago
        )

        # Breakdown by type
        inference_earnings = sum(
            e.amount_sol for e in confirmed_earnings if e.payment_type == "inference"
        )
        training_earnings = sum(
            e.amount_sol for e in confirmed_earnings if e.payment_type == "training_reward"
        )

        return {
            "total_earned": self._total_earnings_sol,
            "pending": self._pending_earnings_sol,
            "today": today_earnings,
            "this_week": week_earnings,
            "this_month": month_earnings,
            "breakdown": {
                "inference": inference_earnings,
                "training": training_earnings,
            },
            "transaction_count": len(confirmed_earnings),
        }

    def _get_last_payment_time(self) -> Optional[str]:
        """Get timestamp of last confirmed payment"""
        confirmed = [e for e in self.earnings_history if e.status == "confirmed"]
        if confirmed:
            latest = max(confirmed, key=lambda e: e.timestamp)
            return latest.timestamp.isoformat()
        return None
