"""
Payment Repository

Database operations for payment transactions.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.repositories.base import BaseRepository
from core.database.models.payment import PaymentModel


class PaymentRepository(BaseRepository[PaymentModel]):
    """Repository for payment operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PaymentModel)

    async def get_by_signature(self, signature: str) -> Optional[PaymentModel]:
        """Get payment by transaction signature"""
        result = await self.session.execute(
            select(PaymentModel).where(PaymentModel.transaction_signature == signature)
        )
        return result.scalar_one_or_none()

    async def find_by_wallet(
        self,
        wallet_address: str,
        direction: str = "both",
        limit: int = 100
    ) -> List[PaymentModel]:
        """Find payments by wallet address"""
        if direction == "from":
            condition = PaymentModel.from_wallet == wallet_address
        elif direction == "to":
            condition = PaymentModel.to_wallet == wallet_address
        else:
            condition = (
                (PaymentModel.from_wallet == wallet_address) |
                (PaymentModel.to_wallet == wallet_address)
            )

        result = await self.session.execute(
            select(PaymentModel)
            .where(condition)
            .order_by(PaymentModel.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_pending_payments(self, limit: int = 100) -> List[PaymentModel]:
        """Find all pending payments"""
        result = await self.session.execute(
            select(PaymentModel)
            .where(PaymentModel.status == "pending")
            .order_by(PaymentModel.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_by_reference(
        self,
        reference_type: str,
        reference_id: str
    ) -> List[PaymentModel]:
        """Find payments by reference"""
        result = await self.session.execute(
            select(PaymentModel).where(
                and_(
                    PaymentModel.reference_type == reference_type,
                    PaymentModel.reference_id == reference_id
                )
            )
        )
        return list(result.scalars().all())

    async def confirm_payment(
        self,
        signature: str,
        block_height: int
    ) -> Optional[PaymentModel]:
        """Mark payment as confirmed"""
        payment = await self.get_by_signature(signature)
        if payment:
            payment.status = "confirmed"
            payment.block_height = block_height
            payment.confirmed_at = datetime.utcnow()
            await self.session.flush()
            return payment
        return None

    async def fail_payment(
        self,
        signature: str,
        error_message: Optional[str] = None
    ) -> Optional[PaymentModel]:
        """Mark payment as failed"""
        payment = await self.get_by_signature(signature)
        if payment:
            payment.status = "failed"
            if error_message:
                payment.metadata["error"] = error_message
            await self.session.flush()
            return payment
        return None

    async def get_total_volume(
        self,
        payment_type: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> float:
        """Get total payment volume"""
        query = select(func.sum(PaymentModel.amount_sol)).where(
            PaymentModel.status == "confirmed"
        )

        if payment_type:
            query = query.where(PaymentModel.payment_type == payment_type)

        if since:
            query = query.where(PaymentModel.confirmed_at >= since)

        result = await self.session.execute(query)
        return result.scalar() or 0.0

    async def get_payment_count(
        self,
        status: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> int:
        """Get payment count"""
        query = select(func.count()).select_from(PaymentModel)

        if status:
            query = query.where(PaymentModel.status == status)

        if since:
            query = query.where(PaymentModel.created_at >= since)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_wallet_balance_change(
        self,
        wallet_address: str,
        since: Optional[datetime] = None
    ) -> dict:
        """Get wallet balance changes (received - sent)"""
        since = since or datetime.utcnow() - timedelta(days=30)

        # Calculate received
        received_result = await self.session.execute(
            select(func.sum(PaymentModel.amount_sol)).where(
                and_(
                    PaymentModel.to_wallet == wallet_address,
                    PaymentModel.status == "confirmed",
                    PaymentModel.confirmed_at >= since
                )
            )
        )
        received = received_result.scalar() or 0.0

        # Calculate sent
        sent_result = await self.session.execute(
            select(func.sum(PaymentModel.amount_sol)).where(
                and_(
                    PaymentModel.from_wallet == wallet_address,
                    PaymentModel.status == "confirmed",
                    PaymentModel.confirmed_at >= since
                )
            )
        )
        sent = sent_result.scalar() or 0.0

        return {
            "received": received,
            "sent": sent,
            "net": received - sent,
            "since": since.isoformat()
        }

    async def get_payment_stats(self) -> dict:
        """Get overall payment statistics"""
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        return {
            "total_payments": await self.get_payment_count(),
            "confirmed_payments": await self.get_payment_count(status="confirmed"),
            "pending_payments": await self.get_payment_count(status="pending"),
            "failed_payments": await self.get_payment_count(status="failed"),
            "total_volume_sol": await self.get_total_volume(),
            "volume_24h_sol": await self.get_total_volume(since=day_ago),
            "volume_7d_sol": await self.get_total_volume(since=week_ago),
            "inference_volume_sol": await self.get_total_volume(payment_type="inference"),
            "training_volume_sol": await self.get_total_volume(payment_type="training_reward")
        }
