# Voice Ledger (Windows 10 Tray App)

This app continuously listens on microphone input and records transaction-intent speech.
It captures lines containing spending verbs (for example: `spent`, `spend`, `paid`, `bought`, `purchased`) and parses them as transactions.
It also applies offline vocabulary correction (SymSpell) for common recognition mistakes in categories/merchant tags.
You can edit the correction dictionary in `src/config.py` under `DOMAIN_VOCABULARY`.

It semantically extracts and stores exactly 4 columns per transaction:
- `date`
- `transaction_amount`
- `category`
- `extra_tags`

Example spoken commands:
- `I spent 300 rupees on food today on swiggy`
- `yesterday, I spent 20 rupees on chocolate`
- `I paid 450 rupees for groceries at dmart`
- `i today i spent ten rupees them chocolate` (now works with semantic parsing!)
- `I spent 500 rupees buying a bicycle` (new categories accepted!)

## Features

- **Semantic NLP Parsing**: Uses spaCy for intelligent understanding of noisy speech input
- **Better Speech Recognition**: OpenAI Whisper for improved accuracy with accented speech
- **Flexible Categories**: Accepts new categories not in the predefined vocabulary (e.g., "bicycle", "gaming")
- **Offline Operation**: No internet required for speech recognition or parsing
- **Vocabulary Correction**: SymSpell-based correction for domain-specific terms
- **Multi-transaction Support**: Can parse multiple transactions from a single utterance

## 1) Setup

```powershell
cd d:\github\voice_ledger_app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Download spaCy Language Model

```powershell
python -m spacy download en_core_web_sm
```

## 3) Run

```powershell
cd d:\github\voice_ledger_app
.\.venv\Scripts\python -m src.main
```

The app starts as a system tray icon and keeps running until you click `Exit`.
It also tries to join nearby speech chunks (short pauses) before parsing, to improve recognition of interrupted sentences.

## 4) Export monthly Excel

Right-click tray icon -> `Export Monthly Excel` -> enter month `YYYY-MM`.

Excel file is saved under:

`C:\Users\<your-user>\Documents\ledger\ledger_YYYY_MM.xlsx`

## 5) Run tests

```powershell
cd d:\github\voice_ledger_app
.\.venv\Scripts\python -m pytest
```

## Packaging (optional)

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --name voice-ledger src\main.py
```
