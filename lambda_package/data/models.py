"""Re-exports every ORM model so importing this module registers all
tables on Base.metadata (used by alembic/env.py and tests/conftest.py).

The canonical model definitions live in models/*.py.
"""

from models.account import Account
from models.transactions import Transaction
from models.transfers import Transfer
from models.user import User

__all__ = ["Account", "Transaction", "Transfer", "User"]
