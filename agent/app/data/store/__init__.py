"""Storage layer. Import `get_store` to obtain the configured singleton store."""
from app.data.store.base import get_store, reset_store, now, month_key

__all__ = ["get_store", "reset_store", "now", "month_key"]
