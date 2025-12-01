"""
Query Enhancement with Rephrasing and Intent Extraction
"""

from typing import List, Dict

class QueryEnhancer:
    """Enhance search queries with domain knowledge"""

    # HVDC/SynCon domain expansions
    SYNONYMS = {
        'hvdc': ['high voltage direct current', 'dc transmission', 'converter'],
        'syncon': ['synchronous condenser', 'rotating compensator'],
        'vsc': ['voltage source converter', 'mmc', 'modular multilevel'],
        'protection': ['fault detection', 'relay', 'circuit breaker'],
        'technical': ['specification', 'requirements', 'design'],
        'commercial': ['offer', 'pricing', 'contract'],
    }

    def expand_query(self, query: str) -> List[str]:
        """Generate query variations"""
        variations = [query]
        query_lower = query.lower()

        for term, synonyms in self.SYNONYMS.items():
            if term in query_lower:
                for syn in synonyms[:1]:  # Add 1 synonym
                    variations.append(query_lower.replace(term, syn))

        return variations[:3]  # Max 3 variations

    def extract_intent(self, query: str) -> Dict:
        """Extract search intent from query"""
        query_lower = query.lower()

        intent = {
            'type': 'search',
            'filters': {},
            'aggregation': False
        }

        # Detect counting queries
        if any(word in query_lower for word in ['how many', 'count', 'number of']):
            intent['type'] = 'count'
            intent['aggregation'] = True

        # Detect category
        if 'syncon' in query_lower:
            intent['filters']['category'] = 'syncon'
        elif 'hvdc' in query_lower:
            intent['filters']['category'] = 'hvdc'

        # Detect document type
        if 'technical' in query_lower:
            intent['filters']['document_type'] = 'technical'
        elif 'commercial' in query_lower or 'offer' in query_lower:
            intent['filters']['document_type'] = 'commercial'

        return intent
