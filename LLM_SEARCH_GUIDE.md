# LLM-Powered Natural Language Search

## Overview
The system now includes an LLM (Large Language Model) that understands your database schema and can translate natural language queries into proper database queries. No more need to specify exact metadata!

## How It Works
1. **Schema Awareness**: The LLM always has your complete Neo4j database schema in its context
2. **Smart Query Generation**: Automatically generates Cypher queries or vector searches based on your intent
3. **Intelligent Parsing**: Understands context like "recent" (2024+), "all" (no filters), etc.

## API Endpoint
```
GET /api/llm-search?q=<your natural language query>
```

Optional parameters:
- `debug=true` - See the generated Cypher query and parsed entities
- `use_llm=false` - Fallback to rule-based parsing

## Example Queries That Now Work

### Counting Queries (No Year Required!)
```bash
# Before: Had to specify year
curl "http://localhost:8001/api/search?q=How%20many%20HVDC%20in%202024"

# Now: Automatically shows breakdown by year
curl "http://localhost:8001/api/llm-search?q=How%20many%20HVDC%20projects?"
```
Returns: Year-by-year breakdown (2021: 1, 2022: 3, 2024: 14, 2025: 16)

### Natural Language Filters
```bash
# "Recent" automatically means 2024+
curl "http://localhost:8001/api/llm-search?q=Show%20recent%20projects"

# Complex queries with multiple conditions
curl "http://localhost:8001/api/llm-search?q=List%20all%20SynCon%20projects%20from%202022"
```

### Content Search (Vector)
```bash
# Automatically uses vector search for content queries
curl "http://localhost:8001/api/llm-search?q=Find%20documents%20about%20transformer%20protection"
curl "http://localhost:8001/api/llm-search?q=Search%20for%20harmonic%20filter%20specifications"
```

## Supported Query Types

### 1. Count Queries
- "How many HVDC projects?" → Shows breakdown by year
- "Count all projects" → Total count
- "How many SynCon in 2022?" → Specific count

### 2. List Queries
- "Show all projects" → Lists all projects
- "List HVDC projects" → Filtered list
- "Recent projects" → Projects from 2024+

### 3. Content Search
- "Find documents about [topic]" → Vector search
- "Search for [technical term]" → Semantic search
- "Documents related to [concept]" → Content matching

### 4. Complex Queries
- "HVDC projects for TenneT" → Multiple filters
- "Transformer protection systems in HVDC projects from last 2 years"
- "Show all grid code compliance documents for German projects"

## Technical Details

### LLM Model
- **Model**: Qwen3:8b (via Ollama)
- **Temperature**: 0.1 (for consistency)
- **Fallback**: Rule-based parsing if LLM fails

### Database Schema (Always in LLM Context)
```
Node: PageChunk
Properties:
- technology: HVDC | SynCon | SVC/STATCOM | Other
- year: 2021, 2022, 2024, 2025 (integer)
- customer: Company name
- project_id: GC[YY]_[NNN] pattern
- text: Document content
- embedding: 1024-dim vector
```

### Query Generation Rules
1. Year is INTEGER (not string)
2. Technology values are case-sensitive
3. Use DISTINCT for project counts
4. Vector search for content queries

## Debugging

To see what the LLM generated:
```bash
curl "http://localhost:8001/api/llm-search?q=Your%20query&debug=true"
```

Returns:
- `generated_cypher`: The Cypher query created
- `parsed_entities`: Extracted entities
- `llm_result`: Full LLM response

## Performance
- **First query**: ~2-3 seconds (LLM generation)
- **Subsequent similar queries**: Faster (cached patterns)
- **Vector search**: ~1 second
- **Metadata queries**: <500ms

## Benefits
✅ No need to remember exact field names
✅ No need to specify years explicitly
✅ Natural language understanding
✅ Automatic query type detection
✅ Smart defaults (e.g., "recent" = 2024+)
✅ Comprehensive breakdowns when no filter specified

## Troubleshooting

### If queries fail:
1. Check Ollama is running: `ollama list`
2. Check API server logs for errors
3. Use `debug=true` to see generated query
4. Fallback uses rule-based parsing automatically

### Common Issues:
- **"LLM generation failed"**: Ollama service may be down
- **Invalid Cypher**: Check debug output for syntax issues
- **No results**: Query may be too specific, try broader terms

## Future Improvements
- Query result caching
- Fine-tuning on your specific query patterns
- Multi-language support
- Query suggestions/autocomplete