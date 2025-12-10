#!/usr/bin/env python3
"""
Ollama Configuration for CrewAI

Configures CrewAI agents to use local Ollama models
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class OllamaConfig:
    """Configuration for Ollama LLM integration with CrewAI"""

    # Default Ollama settings
    DEFAULT_OLLAMA_URL = "http://localhost:11434"
    DEFAULT_MODEL = "mistral"  # Fast, good quality, ~4.1GB
    ALTERNATIVE_MODELS = {
        "neural-chat": "7B model, good for conversation",
        "llama2": "7B model, general purpose",
        "dolphin-mixtral": "8x7B, very good quality (requires >16GB RAM)",
        "orca-mini": "3B model, smallest and fastest",
        "phi": "2.7B model, super fast for edge cases",
    }

    @staticmethod
    def get_ollama_url() -> str:
        """Get Ollama server URL from environment or use default"""
        return os.getenv("OLLAMA_URL", OllamaConfig.DEFAULT_OLLAMA_URL)

    @staticmethod
    def get_model() -> str:
        """Get model from environment or use default"""
        return os.getenv("OLLAMA_MODEL", OllamaConfig.DEFAULT_MODEL)

    @staticmethod
    def check_ollama_connection() -> bool:
        """Check if Ollama server is running"""
        try:
            from ollama import Client
            client = Client(host=OllamaConfig.get_ollama_url())
            # Try to get available models
            models = client.list()
            if models:
                logger.info(f"✓ Ollama connected at {OllamaConfig.get_ollama_url()}")
                logger.info(f"✓ Available models: {[m['name'].split(':')[0] for m in models.get('models', [])]}")
                return True
            else:
                logger.warning("⚠ Ollama server running but no models available")
                return False
        except Exception as e:
            logger.error(f"✗ Cannot connect to Ollama: {e}")
            logger.info(f"  Make sure Ollama is running at {OllamaConfig.get_ollama_url()}")
            logger.info("  You can start Ollama with: ollama serve")
            return False

    @staticmethod
    def pull_model(model_name: str = None) -> bool:
        """Pull a model from Ollama hub if not already downloaded"""
        model = model_name or OllamaConfig.get_model()
        try:
            from ollama import Client
            client = Client(host=OllamaConfig.get_ollama_url())
            logger.info(f"Pulling model {model}... (this may take a few minutes)")
            client.pull(model)
            logger.info(f"✓ Model {model} pulled successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to pull model {model}: {e}")
            return False

    @staticmethod
    def list_available_models() -> None:
        """List available models for Ollama"""
        print("\n" + "="*80)
        print("AVAILABLE OLLAMA MODELS")
        print("="*80)
        print(f"\nDefault Model: {OllamaConfig.DEFAULT_MODEL}\n")
        print("Alternative Models:")
        for model, description in OllamaConfig.ALTERNATIVE_MODELS.items():
            print(f"  • {model:20} - {description}")
        print("\nTo download a model:")
        print("  ollama pull <model_name>")
        print("\nTo run Ollama server:")
        print("  ollama serve")
        print("\n" + "="*80 + "\n")

    @staticmethod
    def setup_environment(ollama_url: str = None, model: str = None) -> None:
        """Setup environment variables for Ollama"""
        if ollama_url:
            os.environ["OLLAMA_URL"] = ollama_url
        if model:
            os.environ["OLLAMA_MODEL"] = model


# Configure Ollama when module is imported
try:
    if not OllamaConfig.check_ollama_connection():
        logger.warning("⚠ Ollama not available. Will use mock LLM")
except Exception as e:
    logger.warning(f"⚠ Could not verify Ollama: {e}")
