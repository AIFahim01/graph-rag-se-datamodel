#!/usr/bin/env python3
"""
Intelligent Query Parser for autonomous agent decision-making

This module provides advanced query parsing capabilities to:
- Classify queries as QUANTITATIVE (how many, how much, statistics) vs QUALITATIVE (what, which, list)
- Detect query types (count, list, search, comparison, complex)
- Extract entities, filters, and constraints from natural language
- Determine required response format and data retrieval strategy
- Guide intelligent tool selection
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict


class QueryType(Enum):
    """Classification of query types"""
    COUNT = "count"              # How many projects/entities?
    LIST = "list"                # List all projects, give me projects
    SEARCH = "search"            # Find/search for specific information
    COMPARISON = "comparison"    # Compare projects, which is better
    STATISTICS = "statistics"    # Group by, aggregation, statistics
    COMPLEX = "complex"          # Multi-step queries


class DataRequirement(Enum):
    """Determines how much data needs to be retrieved"""
    SAMPLE = "sample"            # Top-k results sufficient (10-30)
    COMPREHENSIVE = "comprehensive"  # Need most/all matching results
    AGGREGATE = "aggregate"      # Need all for aggregation/statistics


class QueryClassification(Enum):
    """Query nature - what the user is looking for"""
    QUANTITATIVE = "quantitative"   # Numerical answers (counts, statistics)
    QUALITATIVE = "qualitative"     # Descriptions, lists, examples
    HYBRID = "hybrid"               # Mix of both


@dataclass
class ParsedQuery:
    """Structured representation of a parsed user query"""
    original_query: str
    query_type: QueryType
    classification: QueryClassification
    data_requirement: DataRequirement

    # Extracted components
    technologies: List[str]      # HVDC, SynCon, SVC/STATCOM
    years: List[int]             # Specific years mentioned
    countries: List[str]         # Geographic locations
    companies: List[str]         # Company/customer names
    keywords: List[str]          # General search terms
    entities: Dict[str, List[str]]  # Named entities by type

    # Query characteristics
    needs_aggregation: bool       # Requires grouping/counting
    specific_filters: bool        # Has specific constraints
    time_based: bool              # Time/temporal aspect

    # Recommendations
    primary_tools: List[str]      # Recommended tools in order
    top_k_estimate: int          # Recommended number of results
    requires_semantic: bool       # Needs semantic/conceptual understanding
    requires_exact_match: bool    # Needs exact text matching

    # Confidence and metadata
    confidence_score: float       # 0.0-1.0, how confident in parsing
    reasoning: str               # Explanation of parsing decisions


class IntelligentQueryParser:
    """
    Advanced query parser that understands user intent and guides agent decision-making.

    Capabilities:
    - Quantitative vs Qualitative classification
    - Query type detection (count, list, search, etc.)
    - Entity extraction (technologies, locations, companies)
    - Filter identification
    - Tool recommendation with reasoning
    - Data requirement estimation
    """

    # Pattern definitions for extracting different entity types
    TECHNOLOGY_PATTERNS = {
        r'\bHVDC\b': 'HVDC',
        r'\bSynCon\b': 'SynCon',
        r'\bSVC\b': 'SVC/STATCOM',
        r'\bSTATCOM\b': 'SVC/STATCOM',
        r'\bBESS\b': 'BESS',
        r'\bFacts?\b': 'FACTS',
        r'\bPower\s+Electronics?\b': 'Power Electronics',
    }

    YEAR_PATTERN = r'\b(20\d{2})\b'

    COUNTRY_PATTERNS = {
        r'\b(USA|United States|US|America)\b': 'USA',
        r'\b(Germany|Deutsche)\b': 'Germany',
        r'\b(Netherlands|Dutch)\b': 'Netherlands',
        r'\b(India|Indian)\b': 'India',
        r'\b(UK|United Kingdom|England|British)\b': 'UK',
        r'\bGermany\b': 'Germany',
        r'\bFrance\b': 'France',
        r'\bSpain\b': 'Spain',
        r'\bItaly\b': 'Italy',
        r'\bDubai\b': 'Dubai',
        r'\bSaudi\b': 'Saudi Arabia',
        r'\bCanada\b': 'Canada',
        r'\bAustralia\b': 'Australia',
        r'\bBrazil\b': 'Brazil',
    }

    COMPANY_PATTERNS = {
        r'\bTenneT\b': 'TenneT',
        r'\bElia\b': 'Elia',
        r'\bSiemens\b': 'Siemens',
        r'\bABB\b': 'ABB',
        r'\bGeneral Electric|GE\b': 'General Electric',
        r'\bAlstom\b': 'Alstom',
        r'\bPowerTech\b': 'PowerTech',
        r'\bNEXANT\b': 'NEXANT',
        r'\bMercury\b': 'Mercury',
        r'\bDTU\b': 'DTU',
    }

    # Query keywords for classification
    QUANTITATIVE_KEYWORDS = {
        'count', 'how many', 'number of', 'total', 'quantity',
        'statistics', 'aggregate', 'group by', 'sum', 'average',
        'distribution', 'breakdown', 'percentage'
    }

    QUALITATIVE_KEYWORDS = {
        'list', 'what', 'which', 'give me', 'show', 'find',
        'describe', 'explain', 'tell me about', 'details', 'information'
    }

    COUNT_KEYWORDS = {
        'how many', 'count', 'number of', 'total number',
        'how much', 'how many', 'how many projects'
    }

    LIST_KEYWORDS = {
        'list', 'give me', 'show me', 'all', 'projects',
        'what are', 'which ones', 'names of'
    }

    SEARCH_KEYWORDS = {
        'find', 'search', 'look for', 'where', 'about',
        'related to', 'involving', 'containing'
    }

    COMPARISON_KEYWORDS = {
        'compare', 'difference', 'better', 'worse', 'more',
        'less', 'versus', 'vs', 'vs.', 'than', 'instead'
    }

    def __init__(self):
        """Initialize the parser with pattern configurations"""
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for faster matching"""
        patterns = {}
        for pattern_dict in [self.TECHNOLOGY_PATTERNS, self.COUNTRY_PATTERNS, self.COMPANY_PATTERNS]:
            for pattern, label in pattern_dict.items():
                patterns[f"{label}_pattern"] = re.compile(pattern, re.IGNORECASE)
        patterns['year_pattern'] = re.compile(self.YEAR_PATTERN)
        return patterns

    def parse(self, query: str) -> ParsedQuery:
        """
        Parse a user query and extract all relevant information.

        Args:
            query: User's natural language query

        Returns:
            ParsedQuery with structured information
        """
        query_lower = query.lower()

        # Classify query as quantitative or qualitative
        classification = self._classify_query(query_lower)

        # Detect query type
        query_type = self._detect_query_type(query_lower)

        # Extract entities
        technologies = self._extract_technologies(query)
        years = self._extract_years(query)
        countries = self._extract_countries(query)
        companies = self._extract_companies(query)
        keywords = self._extract_keywords(query)

        # Determine data requirement
        data_requirement = self._determine_data_requirement(
            query_type, classification, len(keywords)
        )

        # Get tool recommendations
        primary_tools, reasoning = self._recommend_tools(
            query_lower, technologies, countries, companies, keywords
        )

        # Estimate top_k
        top_k = self._estimate_top_k(data_requirement, query_type)

        # Determine semantic vs exact match needs
        requires_semantic = self._needs_semantic_search(technologies, keywords)
        requires_exact_match = self._needs_exact_match(countries, companies)

        # Calculate confidence score
        confidence_score = self._calculate_confidence(
            len(technologies) + len(countries) + len(companies) > 0
        )

        return ParsedQuery(
            original_query=query,
            query_type=query_type,
            classification=classification,
            data_requirement=data_requirement,
            technologies=technologies,
            years=years,
            countries=countries,
            companies=companies,
            keywords=keywords,
            entities={
                'technologies': technologies,
                'countries': countries,
                'companies': companies,
                'keywords': keywords,
            },
            needs_aggregation=query_type in [QueryType.COUNT, QueryType.STATISTICS],
            specific_filters=len(technologies) + len(years) + len(countries) > 0,
            time_based=len(years) > 0,
            primary_tools=primary_tools,
            top_k_estimate=top_k,
            requires_semantic=requires_semantic,
            requires_exact_match=requires_exact_match,
            confidence_score=confidence_score,
            reasoning=reasoning,
        )

    def _classify_query(self, query_lower: str) -> QueryClassification:
        """Determine if query is quantitative, qualitative, or hybrid"""
        quant_score = sum(1 for kw in self.QUANTITATIVE_KEYWORDS if kw in query_lower)
        qual_score = sum(1 for kw in self.QUALITATIVE_KEYWORDS if kw in query_lower)

        if quant_score > qual_score:
            return QueryClassification.QUANTITATIVE
        elif qual_score > quant_score:
            return QueryClassification.QUALITATIVE
        else:
            return QueryClassification.HYBRID

    def _detect_query_type(self, query_lower: str) -> QueryType:
        """Detect the type of query (count, list, search, etc.)"""
        # Check for count queries
        if any(kw in query_lower for kw in self.COUNT_KEYWORDS):
            return QueryType.COUNT

        # Check for list queries
        if any(kw in query_lower for kw in self.LIST_KEYWORDS):
            return QueryType.LIST

        # Check for comparison queries
        if any(kw in query_lower for kw in self.COMPARISON_KEYWORDS):
            return QueryType.COMPARISON

        # Check for statistics/aggregation
        if any(word in query_lower for word in ['statistics', 'aggregate', 'group by', 'breakdown']):
            return QueryType.STATISTICS

        # Check for search queries
        if any(kw in query_lower for kw in self.SEARCH_KEYWORDS):
            return QueryType.SEARCH

        # Check for complex queries (multiple parts)
        if '?' in query_lower and query_lower.count('?') > 1:
            return QueryType.COMPLEX
        if ' and ' in query_lower and len(query_lower) > 50:
            return QueryType.COMPLEX

        # Default to search
        return QueryType.SEARCH

    def _extract_technologies(self, query: str) -> List[str]:
        """Extract technology mentions from query"""
        technologies = []
        for pattern, tech in self.TECHNOLOGY_PATTERNS.items():
            if re.search(pattern, query, re.IGNORECASE):
                technologies.append(tech)
        return list(set(technologies))  # Remove duplicates

    def _extract_years(self, query: str) -> List[int]:
        """Extract year mentions from query"""
        matches = re.findall(self.YEAR_PATTERN, query)
        years = []
        for year_str in matches:
            year = int(year_str)
            if 2020 <= year <= 2030:  # Reasonable range for project data
                years.append(year)
        return sorted(list(set(years)))  # Remove duplicates and sort

    def _extract_countries(self, query: str) -> List[str]:
        """Extract country/location mentions from query"""
        countries = []
        for pattern, country in self.COUNTRY_PATTERNS.items():
            if re.search(pattern, query, re.IGNORECASE):
                countries.append(country)
        return list(set(countries))

    def _extract_companies(self, query: str) -> List[str]:
        """Extract company/customer mentions from query"""
        companies = []
        for pattern, company in self.COMPANY_PATTERNS.items():
            if re.search(pattern, query, re.IGNORECASE):
                companies.append(company)
        return list(set(companies))

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract general search keywords from query"""
        # Remove common words and extract meaningful terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'how', 'what', 'which', 'when', 'where', 'why', 'are', 'is', 'have',
            'do', 'we', 'our', 'projects', 'project', 'many', 'list', 'give', 'me',
            'show', 'find', 'search', 'about', 'of', 'by', 'with', 'from', 'as'
        }

        words = query.lower().split()
        keywords = [w.strip('?,;.!') for w in words if w.lower() not in stop_words and len(w) > 2]
        return list(set(keywords))[:10]  # Return up to 10 unique keywords

    def _determine_data_requirement(
        self, query_type: QueryType, classification: QueryClassification, keyword_count: int
    ) -> DataRequirement:
        """Determine how much data needs to be retrieved"""
        if query_type in [QueryType.COUNT, QueryType.STATISTICS]:
            return DataRequirement.AGGREGATE  # Need all for counting/aggregation
        elif query_type == QueryType.LIST:
            return DataRequirement.COMPREHENSIVE  # Need all for complete lists
        elif query_type == QueryType.COMPARISON:
            return DataRequirement.COMPREHENSIVE  # Need all to compare
        else:
            return DataRequirement.SAMPLE  # Top-k results sufficient

    def _recommend_tools(
        self, query_lower: str, technologies: List[str],
        countries: List[str], companies: List[str], keywords: List[str]
    ) -> Tuple[List[str], str]:
        """
        Recommend optimal tools for this query.

        Returns:
            Tuple of (tool_list, reasoning)
        """
        tools = []
        reasoning_parts = []

        # If we have technology and year filters, use neo4j_count/list
        if technologies and any(f in query_lower for f in ['2021', '2022', '2024', '2025']):
            tools.append('neo4j_list_all')
            reasoning_parts.append("Technology and year are metadata fields")

        # If we have technology but no year, still use neo4j for metadata
        elif technologies and 'count' not in query_lower:
            tools.append('neo4j_list_all')
            reasoning_parts.append("Technology is a structured metadata field")

        # Countries require text search
        if countries:
            if not tools or tools[0] != 'neo4j_list_all':
                tools.append('text_search')
                reasoning_parts.append(f"Countries ({', '.join(countries)}) require text_search for exact matching")

        # Companies require text search
        if companies:
            if 'text_search' not in tools:
                tools.append('text_search')
                reasoning_parts.append(f"Companies ({', '.join(companies)}) require text_search")

        # Short acronyms need semantic search
        short_acronyms = [kw for kw in keywords if len(kw) <= 3]
        if short_acronyms:
            if 'vector_search' not in tools:
                tools.append('vector_search')
                reasoning_parts.append(f"Short acronyms ({', '.join(short_acronyms)}) need semantic search to avoid false matches")

        # Conceptual queries need vector search
        conceptual_terms = ['grid', 'stability', 'control', 'renewable', 'efficiency', 'optimization']
        if any(term in query_lower for term in conceptual_terms):
            if 'vector_search' not in tools:
                tools.append('vector_search')
                reasoning_parts.append("Query has conceptual/technical terms needing semantic understanding")

        # Default tools if none selected
        if not tools:
            tools.append('vector_search')
            tools.append('text_search')
            reasoning_parts.append("General search - using both semantic and exact match")

        # Aggregation may be needed
        if 'count' in query_lower or 'how many' in query_lower:
            if 'aggregate_results' not in tools:
                tools.append('aggregate_results')
                reasoning_parts.append("Query requests counting/aggregation")

        reasoning = " | ".join(reasoning_parts)
        return tools[:4], reasoning  # Limit to 4 tools max

    def _estimate_top_k(self, data_requirement: DataRequirement, query_type: QueryType) -> int:
        """Estimate optimal number of results to retrieve"""
        if data_requirement == DataRequirement.SAMPLE:
            return 30  # Top-k sufficient
        elif data_requirement == DataRequirement.COMPREHENSIVE:
            return 500  # Need most results
        else:  # AGGREGATE
            return 500  # Need all for aggregation

    def _needs_semantic_search(self, technologies: List[str], keywords: List[str]) -> bool:
        """Determine if semantic/vector search is needed"""
        # Short acronyms (AI, ML, IoT) need semantic search
        short_keywords = [kw for kw in keywords if len(kw) <= 3]
        if short_keywords:
            return True

        # Conceptual terms need semantic search
        conceptual = ['grid', 'control', 'stability', 'renewable', 'efficiency', 'optimization']
        if any(ct in ' '.join(keywords).lower() for ct in conceptual):
            return True

        return False

    def _needs_exact_match(self, countries: List[str], companies: List[str]) -> bool:
        """Determine if exact text matching is needed"""
        return len(countries) > 0 or len(companies) > 0

    def _calculate_confidence(self, has_clear_filters: bool) -> float:
        """Calculate confidence in parsing (0.0-1.0)"""
        if has_clear_filters:
            return 0.95
        else:
            return 0.85

    def to_dict(self, parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Convert ParsedQuery to dictionary for JSON serialization"""
        result = asdict(parsed_query)
        # Convert enums to strings
        result['query_type'] = parsed_query.query_type.value
        result['classification'] = parsed_query.classification.value
        result['data_requirement'] = parsed_query.data_requirement.value
        return result


def analyze_query_for_agents(query: str) -> Dict[str, Any]:
    """
    Main entry point for query analysis.

    This function provides agent decision-making support by:
    1. Understanding user intent (quantitative vs qualitative)
    2. Extracting key information (entities, filters)
    3. Recommending optimal tools and strategies
    4. Estimating data requirements

    Args:
        query: User's natural language query

    Returns:
        Dictionary with parsing results suitable for agent use
    """
    parser = IntelligentQueryParser()
    parsed = parser.parse(query)
    return parser.to_dict(parsed)


if __name__ == "__main__":
    # Test the parser
    parser = IntelligentQueryParser()

    test_queries = [
        "How many HVDC projects do we have in 2024?",
        "List all SynCon projects in Germany",
        "What AI and grid-related projects are there?",
        "HVDC projects in India and USA?",
        "Give me details about TenneT projects",
        "How many projects are in Netherlands?",
    ]

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print('='*80)
        result = parser.parse(query)
        print(f"Type: {result.query_type.value}")
        print(f"Classification: {result.classification.value}")
        print(f"Data Requirement: {result.data_requirement.value}")
        print(f"Technologies: {result.technologies}")
        print(f"Countries: {result.countries}")
        print(f"Companies: {result.companies}")
        print(f"Recommended Tools: {result.primary_tools}")
        print(f"Top-K Estimate: {result.top_k_estimate}")
        print(f"Reasoning: {result.reasoning}")
        print(f"Confidence: {result.confidence_score}")
