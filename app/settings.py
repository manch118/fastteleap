import os
from pathlib import Path
from pydantic import BaseModel


def _load_env_files():
    """Load .env files if present without requiring python-dotenv.
    Looks in project root and in test_app/.
    """
    candidates = [
        Path(__file__).resolve().parents[2] / ".env",  # project root/.env
        Path(__file__).resolve().parents[1] / ".env",   # test_app/.env
    ]
    for env_path in candidates:
        try:
            if env_path.exists():
                with env_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" not in line:
                            continue
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ.setdefault(key, value)
        except Exception:
            # Ignore parsing errors, environment may already be set
            pass


_load_env_files()


class AppSettings(BaseModel):
    admin_id: int = int(os.getenv("ADMIN_USER_ID", "123456789"))
    
    # YooKassa settings
    bot_token: str = os.getenv("BOT_TOKEN", "")
    yookassa_shop_id: str = os.getenv("YOOKASSA_SHOP_ID", "")
    yookassa_secret_key: str = os.getenv("YOOKASSA_SECRET_KEY", "")
    yookassa_webhook_url: str = os.getenv("YOOKASSA_WEBHOOK_URL", "")
    
    # Payment settings
    payment_success_url: str = os.getenv("PAYMENT_SUCCESS_URL", "https://t.me/your_bot")
    payment_cancel_url: str = os.getenv("PAYMENT_CANCEL_URL", "https://t.me/your_bot")


settings = AppSettings()
