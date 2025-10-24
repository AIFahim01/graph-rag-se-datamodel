"""
Training pair generation from document structure (no Q&A needed)
"""

from typing import List, Dict, Tuple
from loguru import logger
import re


class TrainingPairGenerator:
    """
    Generate training pairs from document structure

    Creates positive and negative pairs automatically using:
    - Adjacent chunks (same PDF)
    - Same section chunks
    - Cross-PDF chunks with shared technical terms
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logger

    def generate_from_structure(self, chunks: List[Dict]) -> List[Dict]:
        """
        Generate training pairs from document structure

        Args:
            chunks: List of chunk dicts from DocumentChunker

        Returns:
            List of training pair dicts with confidence scores
        """
        positive_pairs = []

        # Group chunks by source PDF
        pdf_groups = self._group_by_source(chunks)

        # Rule 1: Adjacent chunks (within same PDF)
        positive_pairs.extend(self._generate_adjacent_pairs(pdf_groups))

        # Rule 2: Same section (if section info available)
        # positive_pairs.extend(self._generate_same_section_pairs(pdf_groups))

        # Rule 3: Cross-PDF with shared entities
        positive_pairs.extend(self._generate_cross_pdf_pairs(chunks))

        self.logger.info(f"Generated {len(positive_pairs)} positive training pairs")
        return positive_pairs

    def _group_by_source(self, chunks: List[Dict]) -> Dict[str, List[Dict]]:
        """Group chunks by source PDF"""
        groups = {}
        for chunk in chunks:
            source = chunk['source']
            if source not in groups:
                groups[source] = []
            groups[source].append(chunk)
        return groups

    def _generate_adjacent_pairs(self, pdf_groups: Dict[str, List[Dict]]) -> List[Dict]:
        """Generate pairs from adjacent chunks"""
        pairs = []

        for pdf, pdf_chunks in pdf_groups.items():
            # Sort by position
            sorted_chunks = sorted(pdf_chunks, key=lambda x: x['position'])

            for i in range(len(sorted_chunks) - 1):
                pairs.append({
                    'chunk_a': sorted_chunks[i],
                    'chunk_b': sorted_chunks[i + 1],
                    'confidence': 0.95,
                    'rule': 'adjacent',
                    'source_type': 'within_pdf'
                })

        return pairs

    def _generate_cross_pdf_pairs(self, chunks: List[Dict]) -> List[Dict]:
        """Generate pairs across PDFs with shared technical terms"""
        pairs = []

        # Extract technical terms for each chunk
        for chunk in chunks:
            chunk['technical_terms'] = self._extract_technical_terms(chunk['text'])

        # Find chunks with shared terms from different PDFs
        processed = set()

        for i, chunk_a in enumerate(chunks):
            for chunk_b in chunks[i+1:]:
                # Skip if same PDF
                if chunk_a['source'] == chunk_b['source']:
                    continue

                # Check for shared technical terms
                shared = chunk_a['technical_terms'] & chunk_b['technical_terms']

                if len(shared) >= 2:  # At least 2 shared terms
                    pair_key = tuple(sorted([chunk_a['chunk_id'], chunk_b['chunk_id']]))

                    if pair_key not in processed:
                        confidence = len(shared) / min(
                            len(chunk_a['technical_terms']),
                            len(chunk_b['technical_terms'])
                        )

                        pairs.append({
                            'chunk_a': chunk_a,
                            'chunk_b': chunk_b,
                            'confidence': min(confidence, 0.70),  # Cap at 0.70
                            'shared_terms': list(shared),
                            'rule': 'cross_pdf_entity',
                            'source_type': 'cross_pdf'
                        })

                        processed.add(pair_key)

        return pairs

    def _extract_technical_terms(self, text: str) -> set:
        """Extract technical terms for similarity matching"""
        terms = set()

        # Voltage patterns (690V, 400V)
        terms.update(re.findall(r'\d+V\b', text))

        # Current patterns (100A, 50A)
        terms.update(re.findall(r'\d+A\b', text))

        # Frequency patterns (50Hz, 60Hz)
        terms.update(re.findall(r'\d+Hz\b', text))

        # Standards (IEC 61508, ISO 9001)
        terms.update(re.findall(r'IEC\s+\d+', text))
        terms.update(re.findall(r'ISO\s+\d+', text))
        terms.update(re.findall(r'EN\s+\d+', text))

        # Part numbers (customize for your domain)
        terms.update(re.findall(r'[A-Z]{2,3}-\d{3,5}', text))

        return terms
