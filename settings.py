import os
from dotenv import load_dotenv


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash") # Modelo padrão
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.7")) # Temp padrão