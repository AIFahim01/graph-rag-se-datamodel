#!/usr/bin/env python3
"""
Intelligent Response Formatter - Formats answers based on query type

This module provides smart response formatting by:
- Adapting format to query type (count, list, search, etc.)
- Adding appropriate context and citations
- Formatting data structures for different query classifications
- Providing summary statistics
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

from crewai_agent_system.utils.query_parser import ParsedQuery, QueryType, QueryClassification


@dataclass
class FormattedResponse:
    """A formatted response ready for user display"""
    original_query: str
    query_type: str
    classification: str
    answer: str
    answer_type: str  # "count", "list", "narrative", etc.
    data: Dict[str, Any]  # Structured data for the response
    citations: List[Dict[str, str]]  # Sources/citations
    confidence: float  # 0.0-1.0
    metadata: Dict[str, Any]  # Additional metadata


class ResponseFormat(Enum):
    """Type of response format"""
    COUNT = "count"
    LIST = "list"
    NARRATIVE = "narrative"
    STATISTICS = "statistics"
    COMPARISON = "comparison"


class IntelligentResponseFormatter:
    """
    Intelligently formats responses based on query characteristics.

    Adapts response structure and content to match user expectations.
    """

    # Response format templates for different query types
    RESPONSE_TEMPLATES = {
        QueryType.COUNT: "count_summary",
        QueryType.LIST: "list_format",
        QueryType.SEARCH: "narrative_with_results",
        QueryType.COMPARISON: "comparison_format",
        QueryType.STATISTICS: "statistics_format",
        QueryType.COMPLEX: "detailed_narrative",
    }

    def __init__(self):
        """Initialize the formatter"""
        pass

    def format_response(self, parsed_query: ParsedQuery, raw_data: Dict[str, Any],
                       confidence: float = 0.85) -> FormattedResponse:
        """
        Format a response based on query characteristics.

        Args:
            parsed_query: ParsedQuery with analysis of the query
            raw_data: Raw structured data from agents (counts, lists, etc.)
            confidence: Confidence score 0.0-1.0

        Returns:
            FormattedResponse object ready for display
        """
        # Determine response format
        response_format = self._determine_format(parsed_query)

        # Special case: if we have statistics data, use that format
        if "statistics" in raw_data:
            response_format = ResponseFormat.STATISTICS

        # Format the answer text
        answer_text = self._format_answer(parsed_query, raw_data, response_format)

        # Extract citations
        citations = self._extract_citations(raw_data)

        # Get data structure for this response type
        formatted_data = self._structure_data(raw_data, response_format)

        # Create metadata
        metadata = {
            "response_format": response_format.value,
            "has_filters": parsed_query.specific_filters,
            "time_based": parsed_query.time_based,
            "needs_aggregation": parsed_query.needs_aggregation,
        }

        return FormattedResponse(
            original_query=parsed_query.original_query,
            query_type=parsed_query.query_type.value,
            classification=parsed_query.classification.value,
            answer=answer_text,
            answer_type=response_format.value,
            data=formatted_data,
            citations=citations,
            confidence=confidence,
            metadata=metadata,
        )

    def _determine_format(self, parsed_query: ParsedQuery) -> ResponseFormat:
        """Determine the best response format for this query"""
        if parsed_query.query_type == QueryType.COUNT:
            return ResponseFormat.COUNT
        elif parsed_query.query_type == QueryType.LIST:
            return ResponseFormat.LIST
        elif parsed_query.query_type == QueryType.COMPARISON:
            return ResponseFormat.COMPARISON
        elif parsed_query.query_type == QueryType.STATISTICS:
            return ResponseFormat.STATISTICS
        elif parsed_query.classification == QueryClassification.QUANTITATIVE:
            return ResponseFormat.COUNT
        elif parsed_query.classification == QueryClassification.QUALITATIVE:
            return ResponseFormat.LIST
        else:
            return ResponseFormat.NARRATIVE

    def _format_answer(self, parsed_query: ParsedQuery, raw_data: Dict[str, Any],
                      response_format: ResponseFormat) -> str:
        """Format the answer text based on response type"""
        if response_format == ResponseFormat.COUNT:
            return self._format_count_answer(parsed_query, raw_data)
        elif response_format == ResponseFormat.LIST:
            return self._format_list_answer(parsed_query, raw_data)
        elif response_format == ResponseFormat.STATISTICS:
            return self._format_statistics_answer(parsed_query, raw_data)
        elif response_format == ResponseFormat.COMPARISON:
            return self._format_comparison_answer(parsed_query, raw_data)
        else:
            return self._format_narrative_answer(parsed_query, raw_data)

    def _format_count_answer(self, parsed_query: ParsedQuery, raw_data: Dict[str, Any]) -> str:
        """Format a count/quantitative answer"""
        count = raw_data.get("total_count", 0)
        breakdown = raw_data.get("breakdown", {})

        answer = f"There are **{count}** projects "

        # Add context from query
        if parsed_query.technologies:
            tech_str = " and ".join(parsed_query.technologies)
            answer += f"with {tech_str} technology "

        if parsed_query.countries:
            country_str = " and ".join(parsed_query.countries)
            answer += f"in {country_str} "

        if parsed_query.years:
            year_str = ", ".join(map(str, parsed_query.years))
            answer += f"in {year_str} "

        answer = answer.rstrip() + "."

        # Add breakdown if available
        if breakdown:
            answer += "\n\n**Breakdown:**\n"
            if "by_technology" in breakdown:
                answer += "\n- By Technology:\n"
                for tech, count in breakdown["by_technology"].items():
                    answer += f"  - {tech}: {count}\n"
            if "by_year" in breakdown:
                answer += "\n- By Year:\n"
                for year, count in breakdown["by_year"].items():
                    answer += f"  - {year}: {count}\n"

        return answer

    def _format_list_answer(self, parsed_query: ParsedQuery, raw_data: Dict[str, Any]) -> str:
        """Format a list answer"""
        projects = raw_data.get("projects", [])
        total = raw_data.get("total", len(projects))

        answer = f"Found **{total} projects**"

        # Add filters used
        filters = []
        if parsed_query.technologies:
            filters.append(f"technology: {', '.join(parsed_query.technologies)}")
        if parsed_query.countries:
            filters.append(f"location: {', '.join(parsed_query.countries)}")
        if parsed_query.companies:
            filters.append(f"company: {', '.join(parsed_query.companies)}")

        if filters:
            answer += f" matching {', '.join(filters)}"

        answer += ":\n\n"

        # Format project list - show ALL projects
        if projects:
            for i, project in enumerate(projects, 1):  # Show ALL projects
                proj_name = project.get("project_name", "Unknown")
                proj_id = project.get("project_id", "")
                tech = project.get("technology", "")
                year = project.get("year", "")

                answer += f"{i}. **{proj_name}**"
                if tech or year:
                    details = []
                    if tech:
                        details.append(f"Tech: {tech}")
                    if year:
                        details.append(f"Year: {year}")
                    answer += f" ({', '.join(details)})"
                answer += "\n"
        else:
            answer += "No projects found matching your criteria."

        return answer

    def _format_statistics_answer(self, parsed_query: ParsedQuery, raw_data: Dict[str, Any]) -> str:
        """Format a statistics answer with aggregated information"""
        stats = raw_data.get("statistics", {})
        total = raw_data.get("total_count", 0)

        answer = f"**Statistics Summary**\n\n"
        answer += f"Total Projects: {total}\n\n"

        if "by_technology" in stats:
            answer += "**By Technology:**\n"
            for tech, count in stats["by_technology"].items():
                pct = (count / total * 100) if total > 0 else 0
                answer += f"- {tech}: {count} ({pct:.1f}%)\n"

        if "by_year" in stats:
            answer += "\n**By Year:**\n"
            for year, count in stats["by_year"].items():
                pct = (count / total * 100) if total > 0 else 0
                answer += f"- {year}: {count} ({pct:.1f}%)\n"

        return answer

    def _format_comparison_answer(self, parsed_query: ParsedQuery, raw_data: Dict[str, Any]) -> str:
        """Format a comparison answer"""
        comparisons = raw_data.get("comparisons", {})

        answer = "**Comparison Results**\n\n"

        for item1, item2 in comparisons.items():
            answer += f"- **{item1}** vs **{item2}**:\n"
            if isinstance(item2, dict):
                for key, value in item2.items():
                    answer += f"  - {key}: {value}\n"
            answer += "\n"

        return answer

    def _format_narrative_answer(self, parsed_query: ParsedQuery, raw_data: Dict[str, Any]) -> str:
        """Format a general narrative answer"""
        # Use provided narrative or create one
        if "narrative" in raw_data:
            return raw_data["narrative"]

        # Create simple narrative from available data
        answer = "Based on the search results:\n\n"

        if "summary" in raw_data:
            answer += raw_data["summary"] + "\n\n"

        if "key_findings" in raw_data:
            answer += "**Key Findings:**\n"
            for finding in raw_data["key_findings"]:
                answer += f"- {finding}\n"

        return answer if answer != "Based on the search results:\n\n" else "Search completed successfully."

    def _extract_citations(self, raw_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract citations from the raw data"""
        citations = []

        # Get citations from data
        if "sources" in raw_data:
            for source in raw_data["sources"]:
                if isinstance(source, dict):
                    citations.append({
                        "title": source.get("title", "Source"),
                        "url": source.get("url", ""),
                        "project_id": source.get("project_id", "")
                    })

        # Add auto-generated citation info
        if "total_count" in raw_data:
            citations.append({
                "title": "Project Database Query",
                "url": "",
                "project_id": ""
            })

        return citations

    def _structure_data(self, raw_data: Dict[str, Any], response_format: ResponseFormat) -> Dict[str, Any]:
        """Structure the data appropriately for this response format"""
        structured = {
            "response_format": response_format.value,
            "raw_data": raw_data,
        }

        if response_format == ResponseFormat.COUNT:
            structured["count"] = raw_data.get("total_count", 0)
            structured["breakdown"] = raw_data.get("breakdown", {})

        elif response_format == ResponseFormat.LIST:
            structured["projects"] = raw_data.get("projects", [])
            structured["total"] = raw_data.get("total", 0)

        elif response_format == ResponseFormat.STATISTICS:
            structured["statistics"] = raw_data.get("statistics", {})
            structured["total"] = raw_data.get("total_count", 0)

        return structured

    def format_for_json(self, response: FormattedResponse) -> Dict[str, Any]:
        """Convert response to JSON-serializable dictionary"""
        return {
            "query": response.original_query,
            "type": response.query_type,
            "classification": response.classification,
            "answer": response.answer,
            "answer_type": response.answer_type,
            "data": response.data,
            "citations": response.citations,
            "confidence": response.confidence,
            "metadata": response.metadata,
        }


def get_response_formatter() -> IntelligentResponseFormatter:
    """Get or create a response formatter"""
    return IntelligentResponseFormatter()


if __name__ == "__main__":
    # Test the formatter
    from crewai_agent_system.utils.query_parser import IntelligentQueryParser

    parser = IntelligentQueryParser()
    formatter = IntelligentResponseFormatter()

    # Test query and sample data
    query = "How many HVDC projects do we have in 2024?"
    parsed = parser.parse(query)

    sample_data = {
        "total_count": 12,
        "breakdown": {
            "by_technology": {"HVDC": 12},
            "by_year": {"2024": 12}
        },
        "sources": [
            {"title": "Project Database", "project_id": "GC24_001"}
        ]
    }

    # Format response
    response = formatter.format_response(parsed, sample_data, confidence=0.95)

    print("\n" + "="*80)
    print("FORMATTED RESPONSE")
    print("="*80)
    print(f"\nQuery: {response.original_query}")
    print(f"Type: {response.answer_type}")
    print(f"Confidence: {response.confidence:.0%}")
    print("\n" + response.answer)
    print(f"\nCitations: {len(response.citations)} source(s)")
    for citation in response.citations:
        print(f"  - {citation['title']}")
    print("\n" + "="*80)
