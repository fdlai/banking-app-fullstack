from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    transaction_type: Mapped[str] = mapped_column(nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    description: Mapped[str | None] = mapped_column(nullable=True)

    # One-directional: Emanuel's real Account model has no reverse "transactions"
    # attribute yet, so back_populates isn't used here.
    account: Mapped["Account"] = relationship()
