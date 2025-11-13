# Client Demo Script

## Pre-Demo Setup (5 minutes before)

```bash
# 1. Verify services running
docker ps | grep chromadb
docker ps | grep neo4j

# 2. Open visualizations in browser
# Tab 1:
datasets/knowledge_graphs/HIGHLY_VISIBLE_graph.html

# Tab 2:
datasets/knowledge_graphs/project_relationships_interactive.html

# 3. Start chat system (keep terminal ready)
python scripts/chat_graphrag.py --interactive --deployment gpt-4.1
```

## Demo Flow (30 minutes)

### Slide 1: Introduction (2 min)

**Say:**
"Today I'll demonstrate an intelligent document retrieval system that uses hybrid GraphRAG - combining knowledge graphs with semantic search to answer questions from technical documents."

**Show:** README.md architecture diagram

---

### Slide 2: The Data (3 min)

**Say:**
"We've processed 10 technical PDFs across 3 real-world projects:"

**Run in terminal:**
```bash
python scripts/dataset_stats.py
```

**Point out:**
- 3 different domains (ERP, Cloud, Analytics)
- 10 PDFs with real technical content
- Organized by project

**Say:**
"The system automatically processes these documents without manual tagging."

---

### Slide 3: Knowledge Graph Visualization (5 min)

**Switch to browser - Show HIGHLY_VISIBLE_graph.html**

**Say:**
"This is the knowledge graph automatically extracted from those 10 PDFs."

**Point out:**
1. **Three colored clusters:**
   - "Red = Alpha ERP project (SAP, HANA, S/4HANA entities)"
   - "Teal = Beta Cloud project (AWS, Kubernetes, migration entities)"
   - "Green = Gamma Analytics project (Kafka, Spark, ML entities)"

2. **Relationship labels:**
   - "Every edge shows the relationship type"
   - "For example: SAP 'produces' S/4HANA"

3. **Gold stars:**
   - "These are cross-project entities"
   - "Kubernetes appears in BOTH Beta and Gamma"
   - "This cross-project discovery is automatic!"

4. **Interactive features:**
   - Drag nodes around
   - Hover to see source PDFs
   - "Every relationship is traceable to the original document"

---

### Slide 4: Live Chat Demo (15 min) ⭐ MAIN EVENT

**Switch to terminal**

**Say:**
"Now let me show you the chat interface. You can ask natural language questions about these documents."

#### Demo Query 1: Simple Factual
```
Your question: What database technologies are mentioned?
```

**Wait for response, then point out:**
- "Notice it searched BOTH databases (vector + graph)"
- "Found information across multiple projects"
- "Cites exact sources: beta_cloud_migration, gamma_analytics_platform"
- "Lists specific technologies: DynamoDB, S3, Elasticsearch, PostgreSQL"
- "All in under 5 seconds"

#### Demo Query 2: Cross-Project Discovery
```
Your question: Which projects use Kubernetes?
```

**Point out:**
- "Look - it found Kubernetes in the knowledge graph"
- "Shows [GRAPH] result: Kubernetes → containerization"
- "Also shows [VECTOR] results from PDF chunks"
- "Answer correctly identifies: Beta AND Gamma projects"
- "This cross-project intelligence is the key advantage"

#### Demo Query 3: Domain-Specific
```
Your question: What is SAP S/4HANA?
```

**Point out:**
- "Retrieves from alpha_erp_system project"
- "Shows it's an ERP system"
- "Explains the relationship: SAP produces S/4HANA"
- "Source: technical_offer.pdf, commercial_offer.pdf"

#### Demo Query 4: Temporal/Date Query
```
Your question: What happened on October 29, 2025?
```

**Point out:**
- "Found the date in multiple documents"
- "Synthesizes information across projects"
- "Shows these were proposal submission dates"

#### Demo Query 5: Safety Check
```
Your question: What is Harvard University?
```

**Point out - VERY IMPORTANT:**
- "Notice: System says 'no information found'"
- "It doesn't make things up"
- "Only answers from available documents"
- "This reliability is crucial for enterprise use"

**Say:**
"Unlike some AI systems that hallucinate, ours is honest about what it knows and doesn't know."

---

### Slide 5: How It Works (5 min)

**Show architecture diagram**

**Explain simply:**

"The system works in two phases:

**Phase 1: Setup (one-time)**
1. Process PDFs → Extract text
2. Build knowledge graph → 97 entities, 158 relationships
3. Generate embeddings → Convert text to vectors
4. Store → ChromaDB for vectors, Neo4j for graph

**Phase 2: Query (real-time)**
1. User asks question
2. System searches BOTH:
   - ChromaDB for semantically similar chunks
   - Neo4j for related entities via graph
3. Combines results (hybrid fusion)
4. Azure OpenAI generates answer
5. Returns with source citations

**Say:**
"This hybrid approach gives us the best of both worlds: semantic understanding from vectors, plus relationship discovery from the graph."

---

## Closing (2 min)

**Summary:**
"We've demonstrated a production-ready system that:
- Extracts knowledge automatically from technical documents
- Discovers cross-project connections
- Answers questions in <5 seconds
- Provides source citations
- Refuses to hallucinate

The system is currently running locally and ready for integration."

**Next Steps:**
1. Add your actual project PDFs
2. Scale to more documents
3. Customize for your domain
4. Integrate with existing tools

**Q&A**

---

## Emergency Backup Plans

**If live demo fails:**
- Show pre-recorded screenshots
- Walk through the visualization files
- Explain the architecture conceptually

**If asked about specific tech:**
- Refer to REBEL_KNOWLEDGE_GRAPH_GUIDE.md
- Show docs/knowledge-graph-extraction.md
- Explain research foundation (papers cited)

**If Neo4j browser needed:**
- http://localhost:7474
- Run: `MATCH (n) RETURN n LIMIT 25`
- Shows visual graph

---

## Post-Demo Follow-Up

**Send these files:**
1. `EXECUTIVE_SUMMARY.md` - High-level overview
2. `CLIENT_PRESENTATION_GUIDE.md` - This file
3. `HOW_TO_USE_GRAPHRAG_CHAT.md` - Usage instructions
4. `HIGHLY_VISIBLE_graph.html` - Interactive visualization
5. Link to GitHub repo (once pushed)

**Offer:**
- Technical deep-dive session
- Custom dataset processing
- Integration planning
- Scaling discussion

---

**You're ready to present! Practice the 5 demo queries beforehand and you'll impress your clients.**
