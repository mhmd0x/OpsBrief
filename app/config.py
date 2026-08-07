import os
from zoneinfo import ZoneInfo


APP_TIMEZONE = ZoneInfo(
    os.getenv("APP_TIMEZONE", "Asia/Riyadh")
)