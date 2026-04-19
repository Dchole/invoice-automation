from __future__ import annotations
from typing import List
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "Invoice Automation"
    database_url: str = (
        f"sqlite:///{Path(__file__).resolve().parent.parent.parent / 'data' / 'invoices.db'}"
    )
    default_currency: str = "CAD"
    default_payment_terms: int = 30
    reminder_days: List[int] = [3, 7, 14, 30]
    resend_api_key: str = ""
    email_from: str = "InvoiceFlow <onboarding@resend.dev>"
    mock_email: bool = True
    # Exchange rates relative to CAD (1 CAD = X of target)
    usd_to_cad: float = 1.36
    cad_to_usd: float = 0.735

    model_config = {
        "env_prefix": "INV_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
