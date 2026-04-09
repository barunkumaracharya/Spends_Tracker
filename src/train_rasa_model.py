"""
Rasa NLU model training script.

Run this once to train the Rasa NLU model from the training data.
Usage: python -m src.train_rasa_model
"""

from pathlib import Path
from rasa.nlu.training_data import load_data
from rasa.nlu.config import RasaNLUModelConfig
from rasa.nlu.model import Trainer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[1]
TRAINING_DATA_PATH = ROOT_DIR / "src" / "nlu_training_data.yml"
MODELS_DIR = ROOT_DIR / "models" / "rasa_nlu"


def train_rasa_model():
    """Train the Rasa NLU model."""
    if not TRAINING_DATA_PATH.exists():
        raise FileNotFoundError(f"Training data not found at {TRAINING_DATA_PATH}")
    
    logger.info("Starting Rasa NLU training...")
    logger.info("Training data: %s", TRAINING_DATA_PATH)
    logger.info("Model output directory: %s", MODELS_DIR)
    
    # Load training data
    training_data = load_data(str(TRAINING_DATA_PATH))
    
    # Configure model
    config = RasaNLUModelConfig(
        {
            "pipeline": [
                {"name": "WhitespaceTokenizer"},
                {"name": "RegexFeaturizer"},
                {"name": "LexicalSyntacticFeaturizer"},
                {"name": "CountVectorsFeaturizer"},
                {"name": "DietClassifier", "epochs": 100},
                {"name": "EntitySynonymMapper"},
                {"name": "CRFEntityExtractor"},
            ],
            "language": "en",
        }
    )
    
    # Train model
    trainer = Trainer(config)
    trainer.train(training_data)
    
    # Save model
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = trainer.persist(str(MODELS_DIR))
    logger.info("Training complete. Model saved to: %s", model_path)
    return model_path


if __name__ == "__main__":
    train_rasa_model()
