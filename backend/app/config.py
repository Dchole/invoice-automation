from __future__ import annotations
from typing import List
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "Invoice Automation"
    database_url: str = f"sqlite:///{Path(__file__).resolve().parent.parent.parent / 'data' / 'invoices.db'}"
    default_currency: str = "CAD"
    default_payment_terms: int = 30
    reminder_days: List[int] = [3, 7, 14, 30]
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "invoices@example.com"
    mock_email: bool = True
    # Exchange rates relative to CAD (1 CAD = X of target)
    usd_to_cad: float = 1.36
    cad_to_usd: float = 0.735

    model_config = {"env_prefix": "INV_", "env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
