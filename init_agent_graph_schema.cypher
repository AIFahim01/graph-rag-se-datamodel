// Initialize Agent-as-Graph Schema in Neo4j
// This script creates the Agent Registry with agent/tool/capability nodes
// Run this with: cypher-shell -u neo4j -p siemensenergy < init_agent_graph_schema.cypher

// ==================== CONSTRAINTS & INDEXES ====================

// Create unique constraints for agent/tool/capability IDs
CREATE CONSTRAINT agent_id IF NOT EXISTS
FOR (a:AGENT) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT tool_id IF NOT EXISTS
FOR (t:TOOL) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT capability_id IF NOT EXISTS
FOR (c:CAPABILITY) REQUIRE c.id IS UNIQUE;

// Create indexes for performance
CREATE INDEX agent_name IF NOT EXISTS
FOR (a:AGENT) ON (a.name);

CREATE INDEX agent_role IF NOT EXISTS
FOR (a:AGENT) ON (a.role);

CREATE INDEX tool_name IF NOT EXISTS
FOR (t:TOOL) ON (t.name);

CREATE INDEX tool_type IF NOT EXISTS
FOR (t:TOOL) ON (t.type);

CREATE INDEX capability_name IF NOT EXISTS
FOR (c:CAPABILITY) ON (c.name);

// ==================== CAPABILITY NODES ====================
// Define core capabilities needed for query processing

CREATE (cap_semantic:CAPABILITY {
    id: "cap_semantic_search",
    name: "Semantic Search",
    category: "search",
    description: "Understand meaning and context of queries using vector embeddings",
    complexity_level: "medium",
    prerequisites: ["embeddings"],
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (cap_metadata:CAPABILITY {
    id: "cap_metadata_filtering",
    name: "Metadata Filtering",
    category: "filtering",
    description: "Filter results by technology, year, customer and other metadata fields",
    complexity_level: "low",
    prerequisites: ["database_access"],
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (cap_text_search:CAPABILITY {
    id: "cap_text_search",
    name: "Text Search",
    category: "search",
    description: "Exact keyword matching for proper nouns and specific terms",
    complexity_level: "low",
    prerequisites: ["database_access"],
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (cap_query_planning:CAPABILITY {
    id: "cap_query_planning",
    name: "Query Planning",
    category: "reasoning",
    description: "Analyze queries and create multi-step execution plans",
    complexity_level: "high",
    prerequisites: ["llm_access"],
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (cap_graph_traversal:CAPABILITY {
    id: "cap_graph_traversal",
    name: "Graph Traversal",
    category: "search",
    description: "Navigate knowledge graph relationships to enrich context",
    complexity_level: "medium",
    prerequisites: ["database_access"],
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (cap_aggregation:CAPABILITY {
    id: "cap_aggregation",
    name: "Result Aggregation",
    category: "processing",
    description: "Group, count, and summarize results by different dimensions",
    complexity_level: "medium",
    prerequisites: ["database_access"],
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (cap_nlg:CAPABILITY {
    id: "cap_nlg",
    name: "Natural Language Generation",
    category: "output",
    description: "Generate human-readable answers with proper formatting and citations",
    complexity_level: "high",
    prerequisites: ["llm_access"],
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (cap_self_correction:CAPABILITY {
    id: "cap_self_correction",
    name: "Self-Correction",
    category: "reasoning",
    description: "Evaluate result quality and retry with alternative strategies",
    complexity_level: "high",
    prerequisites: ["llm_access"],
    created_at: datetime(),
    updated_at: datetime()
});

// ==================== TOOL NODES ====================
// Define individual tools that agents can use

CREATE (tool_vec_search:TOOL {
    id: "tool_vector_search",
    name: "Vector Search",
    type: "search",
    description: "Semantic search using BAAI/bge-large-en-v1.5 embeddings",
    endpoint: "vector_search",
    cost_estimate: 0.1,
    latency_ms: 500,
    success_rate: 0.98,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (tool_text_search:TOOL {
    id: "tool_text_search",
    name: "Text Search",
    type: "search",
    description: "Exact keyword matching in document content",
    endpoint: "text_search",
    cost_estimate: 0.05,
    latency_ms: 300,
    success_rate: 0.99,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (tool_metadata_count:TOOL {
    id: "tool_neo4j_count",
    name: "Metadata Count",
    type: "aggregation",
    description: "Count projects matching metadata filters (technology, year, customer)",
    endpoint: "neo4j_count",
    cost_estimate: 0.02,
    latency_ms: 100,
    success_rate: 1.0,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (tool_metadata_list:TOOL {
    id: "tool_neo4j_list",
    name: "Metadata List All",
    type: "aggregation",
    description: "List all projects matching metadata filters",
    endpoint: "neo4j_list_all",
    cost_estimate: 0.05,
    latency_ms: 200,
    success_rate: 0.99,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (tool_entity_search:TOOL {
    id: "tool_entity_search",
    name: "Entity Search",
    type: "search",
    description: "Find entities in knowledge graph and related projects",
    endpoint: "entity_search",
    cost_estimate: 0.08,
    latency_ms: 400,
    success_rate: 0.95,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (tool_aggregate:TOOL {
    id: "tool_aggregate_results",
    name: "Aggregate Results",
    type: "processing",
    description: "Group and count results by technology, year, and other dimensions",
    endpoint: "aggregate_results",
    cost_estimate: 0.01,
    latency_ms: 50,
    success_rate: 1.0,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (tool_llm_plan:TOOL {
    id: "tool_llm_planning",
    name: "LLM Query Planning",
    type: "reasoning",
    description: "Use LLM to analyze query and create execution plan",
    endpoint: "plan_execution",
    cost_estimate: 0.2,
    latency_ms: 3000,
    success_rate: 0.90,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (tool_llm_answer:TOOL {
    id: "tool_llm_answer_generation",
    name: "LLM Answer Generation",
    type: "output",
    description: "Generate natural language answer from query results",
    endpoint: "generate_answer",
    cost_estimate: 0.15,
    latency_ms: 2000,
    success_rate: 0.92,
    created_at: datetime(),
    updated_at: datetime()
});

// ==================== AGENT NODES ====================
// Define specialized agents with their capabilities

CREATE (agent_analyst:AGENT {
    id: "agent_query_analyst",
    name: "Query Analyst",
    role: "query_understanding",
    description: "Analyzes user queries to understand intent, classify query types, and extract key entities",
    status: "active",
    model: "gpt-oss:120b",
    backstory: "Expert data analyst who specializes in understanding natural language queries and translating them into structured requirements.",
    success_rate_initial: 0.98,
    avg_latency_ms_initial: 1500,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (agent_search:AGENT {
    id: "agent_search_specialist",
    name: "Search Specialist",
    role: "data_retrieval",
    description: "Executes optimal search strategies combining vector search, text search, and metadata queries",
    status: "active",
    model: "gpt-oss:120b",
    backstory: "Database query expert who knows exactly which search tool works best for each situation.",
    success_rate_initial: 0.96,
    avg_latency_ms_initial: 800,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (agent_navigator:AGENT {
    id: "agent_graph_navigator",
    name: "Graph Navigator",
    role: "context_enrichment",
    description: "Explores entity relationships in the knowledge graph to provide rich context",
    status: "active",
    model: "gpt-oss:120b",
    backstory: "Knowledge graph specialist who understands relationships between entities and can discover hidden connections.",
    success_rate_initial: 0.88,
    avg_latency_ms_initial: 600,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (agent_aggregator:AGENT {
    id: "agent_analytics_aggregator",
    name: "Analytics Aggregator",
    role: "result_processing",
    description: "Deduplicates, counts, groups results and generates statistical summaries",
    status: "active",
    model: "gpt-oss:120b",
    backstory: "Data analyst who excels at summarizing large result sets and creating meaningful statistics.",
    success_rate_initial: 0.99,
    avg_latency_ms_initial: 300,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (agent_synthesizer:AGENT {
    id: "agent_response_synthesizer",
    name: "Response Synthesizer",
    role: "answer_generation",
    description: "Generates natural language answers with proper formatting, citations, and explanations",
    status: "active",
    model: "gpt-oss:120b",
    backstory: "Communication expert who translates raw data into clear, well-structured answers.",
    success_rate_initial: 0.94,
    avg_latency_ms_initial: 2000,
    created_at: datetime(),
    updated_at: datetime()
});

// ==================== RELATIONSHIPS ====================
// Connect tools to capabilities

MATCH (t:TOOL {id: "tool_vector_search"}), (c:CAPABILITY {id: "cap_semantic_search"})
CREATE (t)-[:REQUIRES]->(c);

MATCH (t:TOOL {id: "tool_text_search"}), (c:CAPABILITY {id: "cap_text_search"})
CREATE (t)-[:REQUIRES]->(c);

MATCH (t:TOOL {id: "tool_neo4j_count"}), (c:CAPABILITY {id: "cap_metadata_filtering"})
CREATE (t)-[:REQUIRES]->(c);

MATCH (t:TOOL {id: "tool_neo4j_list"}), (c:CAPABILITY {id: "cap_metadata_filtering"})
CREATE (t)-[:REQUIRES]->(c);

MATCH (t:TOOL {id: "tool_aggregate_results"}), (c:CAPABILITY {id: "cap_aggregation"})
CREATE (t)-[:REQUIRES]->(c);

MATCH (t:TOOL {id: "tool_entity_search"}), (c:CAPABILITY {id: "cap_graph_traversal"})
CREATE (t)-[:REQUIRES]->(c);

// Connect agents to capabilities

MATCH (a:AGENT {id: "agent_query_analyst"}), (c:CAPABILITY {id: "cap_query_planning"})
CREATE (a)-[:HAS_CAPABILITY]->(c);

MATCH (a:AGENT {id: "agent_search_specialist"}), (c:CAPABILITY {id: "cap_semantic_search"})
CREATE (a)-[:HAS_CAPABILITY]->(c);

MATCH (a:AGENT {id: "agent_search_specialist"}), (c:CAPABILITY {id: "cap_text_search"})
CREATE (a)-[:HAS_CAPABILITY]->(c);

MATCH (a:AGENT {id: "agent_search_specialist"}), (c:CAPABILITY {id: "cap_metadata_filtering"})
CREATE (a)-[:HAS_CAPABILITY]->(c);

MATCH (a:AGENT {id: "agent_graph_navigator"}), (c:CAPABILITY {id: "cap_graph_traversal"})
CREATE (a)-[:HAS_CAPABILITY]->(c);

MATCH (a:AGENT {id: "agent_analytics_aggregator"}), (c:CAPABILITY {id: "cap_aggregation"})
CREATE (a)-[:HAS_CAPABILITY]->(c);

MATCH (a:AGENT {id: "agent_response_synthesizer"}), (c:CAPABILITY {id: "cap_nlg"})
CREATE (a)-[:HAS_CAPABILITY]->(c);

// Connect agents to tools

MATCH (a:AGENT {id: "agent_search_specialist"}), (t:TOOL {id: "tool_vector_search"})
CREATE (a)-[:USES]->(t);

MATCH (a:AGENT {id: "agent_search_specialist"}), (t:TOOL {id: "tool_text_search"})
CREATE (a)-[:USES]->(t);

MATCH (a:AGENT {id: "agent_search_specialist"}), (t:TOOL {id: "tool_neo4j_count"})
CREATE (a)-[:USES]->(t);

MATCH (a:AGENT {id: "agent_search_specialist"}), (t:TOOL {id: "tool_neo4j_list"})
CREATE (a)-[:USES]->(t);

MATCH (a:AGENT {id: "agent_graph_navigator"}), (t:TOOL {id: "tool_entity_search"})
CREATE (a)-[:USES]->(t);

MATCH (a:AGENT {id: "agent_analytics_aggregator"}), (t:TOOL {id: "tool_aggregate_results"})
CREATE (a)-[:USES]->(t);

MATCH (a:AGENT {id: "agent_query_analyst"}), (t:TOOL {id: "tool_llm_planning"})
CREATE (a)-[:USES]->(t);

MATCH (a:AGENT {id: "agent_response_synthesizer"}), (t:TOOL {id: "tool_llm_answer_generation"})
CREATE (a)-[:USES]->(t);

// Connect agents in workflow order (dependency relationships)

MATCH (a1:AGENT {id: "agent_query_analyst"}), (a2:AGENT {id: "agent_search_specialist"})
CREATE (a2)-[:DEPENDS_ON]->(a1);

MATCH (a1:AGENT {id: "agent_search_specialist"}), (a2:AGENT {id: "agent_analytics_aggregator"})
CREATE (a2)-[:DEPENDS_ON]->(a1);

MATCH (a1:AGENT {id: "agent_analytics_aggregator"}), (a2:AGENT {id: "agent_response_synthesizer"})
CREATE (a2)-[:DEPENDS_ON]->(a1);

MATCH (a1:AGENT {id: "agent_graph_navigator"}), (a2:AGENT {id: "agent_response_synthesizer"})
CREATE (a2)-[:DEPENDS_ON]->(a1);

// ==================== VERIFICATION ====================
// Count created nodes and relationships

MATCH (a:AGENT) RETURN "AGENT nodes" as entity, count(a) as count
UNION
MATCH (t:TOOL) RETURN "TOOL nodes" as entity, count(t) as count
UNION
MATCH (c:CAPABILITY) RETURN "CAPABILITY nodes" as entity, count(c) as count
UNION
MATCH ()-[r:USES]->() RETURN "USES relationships" as entity, count(r) as count
UNION
MATCH ()-[r:HAS_CAPABILITY]->() RETURN "HAS_CAPABILITY relationships" as entity, count(r) as count
UNION
MATCH ()-[r:REQUIRES]->() RETURN "REQUIRES relationships" as entity, count(r) as count
UNION
MATCH ()-[r:DEPENDS_ON]->() RETURN "DEPENDS_ON relationships" as entity, count(r) as count;
