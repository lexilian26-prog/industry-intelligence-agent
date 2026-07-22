import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_BASE_URL = "https://llm-gateway.momenta.works"
ANTHROPIC_MODEL = "claude-sonnet-4.6"

MAX_ROWS_FOR_AI = 500
MAX_STAT_CHARS = 3000
