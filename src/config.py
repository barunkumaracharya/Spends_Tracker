from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT_DIR / "logs"
# Export all ledgers to the project exports directory.
EXPORT_DIR = ROOT_DIR / "exports"
DB_PATH = ROOT_DIR / "ledger.db"

# Speech-to-Text Configuration
# Options: "vosk" or "whisper"
STT_ENGINE = "whisper"  # Recommended: "whisper" for better accuracy

# For Vosk (legacy)
VOSK_MODEL_DIR = ROOT_DIR / "models" / "vosk-model-en-in-0.5"

# For Whisper
WHISPER_MODEL_SIZE = "base"  # Options: "tiny", "base", "small", "medium", "large"
WHISPER_DEVICE = "cpu"  # Options: "cpu" or "cuda" (nvidia GPU)
WHISPER_LANGUAGE = "en"

# Transaction Parser Configuration
# Options: "regex" or "spacy"
PARSER_ENGINE = "spacy"  # Recommended: "spacy" for semantic understanding

# For spaCy NLU (no training required - uses spacy pre-trained model)
# Clear this config if moving back to regex
SPACY_NLU_ENABLED = True

# Audio Settings
SAMPLE_RATE = 16_000
CHANNELS = 1
BLOCKSIZE = 8_000
PAUSE_JOIN_SECONDS = 3.0

# Editable domain dictionary for offline token correction.
DOMAIN_VOCABULARY = [
    "biryani",
    "pizza",
    "burger",
    "sandwich",
    "wrap",
    "salad",
    "soup",
    "drink",
    "juice",
    "education",
    "school",
    "college",
    "university",
    "school fees",
    "college fees",
    "university fees",
    "school tuition",
    "college tuition",
    "university tuition",
    "food",
    "groceries",
    "grocery",
    "chocolate",
    "snacks",
    "snack",
    "coffee",
    "tea",
    "lunch",
    "dinner",
    "breakfast",
    "rent",
    "fuel",
    "petrol",
    "diesel",
    "travel",
    "taxi",
    "uber",
    "ola",
    "metro",
    "bus",
    "train",
    "medicine",
    "medical",
    "hospital",
    "fees",
    "tuition",
    "shopping",
    "clothes",
    "clothing",
    "shoes",
    "electronics",
    "bills",
    "electricity",
    "internet",
    "mobile",
    "phone",
    "entertainment",
    "movie",
    "swiggy",
    "zomato",
    "blinkit",
    "zepto",
    "instamart",
    "dmart",
    "bigbasket",
    "amazon",
    "flipkart",
    "myntra",
    "paytm",
    "gpay",
    "phonepe",
    "rent"
]
