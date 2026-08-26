from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from database import Base


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True)
    from_account_id = Column(Integer, ForeignKey("accounts.id"))
    to_account_id = Column(Integer, ForeignKey("accounts.id"))
    amount = Column(Numeric(12, 2))
    timestamp = Column(DateTime)
    status = Column(String)