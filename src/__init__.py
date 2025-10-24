"""
PDF-to-GraphRAG: Domain-Specific Document Intelligence

Train custom embeddings from PDFs using contrastive learning and build
knowledge graphs for intelligent retrieval.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from . import processing
from . import training
from . import graph
from . import embeddings
from . import storage
from . import retrieval
from . import qa

__all__ = [
    "processing",
    "training",
    "graph",
    "embeddings",
    "storage",
    "retrieval",
    "qa",
]
