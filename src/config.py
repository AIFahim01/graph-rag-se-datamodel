"""
Configuration management for PDF-to-GraphRAG system
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class ProcessingConfig(BaseSettings):
    """PDF processing configuration"""
    chunk_size: int = Field(default=1000, description="Chunk size in characters")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    min_chunk_size: int = Field(default=200, description="Minimum chunk size")
    max_chunk_size: int = Field(default=1500, description="Maximum chunk size")


class TrainingConfig(BaseSettings):
    """Embedding training configuration"""
    base_model: str = Field(default="BAAI/bge-large-en-v1.5", description="Base embedding model")
    epochs: int = Field(default=3, description="Training epochs")
    batch_size: int = Field(default=32, description="Batch size per GPU")
    learning_rate: float = Field(default=2e-5, description="Learning rate")
    warmup_steps: int = Field(default=100, description="Warmup steps")

    # Pair generation
    adjacent_confidence: float = Field(default=0.95, description="Confidence for adjacent chunks")
    same_section_confidence: float = Field(default=0.80, description="Confidence for same section")
    cross_pdf_min_shared_terms: int = Field(default=2, description="Min shared terms for cross-PDF pairs")
    cross_pdf_confidence: float = Field(default=0.70, description="Confidence for cross-PDF pairs")


class LLMConfig(BaseSettings):
    """Local LLM configuration"""
    model: str = Field(default="llama3.1:70b", description="LLM model name")
    api_base: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    temperature: float = Field(default=0.3, description="LLM temperature")
    max_tokens: int = Field(default=1000, description="Max tokens for generation")


class GraphConfig(BaseSettings):
    """Knowledge graph configuration"""
    community_algorithm: str = Field(default="leiden", description="Community detection algorithm")
    max_traversal_hops: int = Field(default=2, description="Maximum graph traversal hops")
    min_entity_frequency: int = Field(default=2, description="Minimum entity frequency")


class RetrievalConfig(BaseSettings):
    """GraphRAG retrieval configuration"""
    top_k: int = Field(default=5, description="Number of results to return")

    # Score weights for fusion
    chunk_similarity_weight: float = Field(default=0.4)
    entity_match_weight: float = Field(default=0.3)
    community_relevance_weight: float = Field(default=0.2)
    graph_proximity_weight: float = Field(default=0.1)


class DatabaseConfig(BaseSettings):
    """Database configuration"""

    # Vector DB
    vector_db_type: str = Field(default="chromadb", description="Vector DB type: chromadb, qdrant, neo4j")
    vector_db_path: str = Field(default="./chroma_data", description="Vector DB storage path")

    # Graph DB
    graph_db_type: str = Field(default="neo4j", description="Graph DB type: neo4j, networkx")
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="password", description="Neo4j password")


class ProjectConfig(BaseSettings):
    """Main project configuration"""

    project_name: str = Field(default="default_project", description="Project name")
    data_dir: Path = Field(default=Path("./data"), description="Data directory")
    models_dir: Path = Field(default=Path("./models"), description="Models directory")
    logs_dir: Path = Field(default=Path("./logs"), description="Logs directory")

    # Sub-configurations
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    graph: GraphConfig = Field(default_factory=GraphConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_config(config_path: Optional[str] = None) -> ProjectConfig:
    """
    Load configuration from file or environment

    Args:
        config_path: Optional path to YAML config file

    Returns:
        ProjectConfig instance
    """
    if config_path:
        import yaml
        with open(config_path) as f:
            config_dict = yaml.safe_load(f)
        return ProjectConfig(**config_dict)

    return ProjectConfig()
