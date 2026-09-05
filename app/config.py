import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]

# Default reminder times (24-hour, local time)
MORNING_HOUR: int = 9
MORNING_MINUTE: int = 0

EVENING_HOUR: int = 21
EVENING_MINUTE: int = 0
