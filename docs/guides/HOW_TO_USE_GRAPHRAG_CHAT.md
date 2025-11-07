# How to Use Your Hybrid GraphRAG Chat System

## ✅ System is READY and TESTED!

Your complete hybrid GraphRAG system is now running locally with:
- ✅ **ChromaDB** - Vector search (31 chunks embedded)
- ✅ **Neo4j** - Knowledge graph (97 entities, 158 relationships)
- ✅ **Hybrid Retrieval** - Combines vector + graph
- ✅ **Azure OpenAI** - Answer generation with gpt-4.1

## 🚀 Quick Start

### Run a Single Question:

```bash
python scripts/chat_graphrag.py --query "What are the database technologies?" --deployment gpt-4.1
```

### Interactive Chat Mode:

```bash
python scripts/chat_graphrag.py --interactive --deployment gpt-4.1
```

## 📖 Example Queries

```bash
# Ask about technologies
python scripts/chat_graphrag.py --query "What database technologies are used?" --deployment gpt-4.1

# Ask about projects
python scripts/chat_graphrag.py --query "What is the alpha ERP system about?" --deployment gpt-4.1

# Ask about cloud
python scripts/chat_graphrag.py --query "Which projects use Kubernetes?" --deployment gpt-4.1

# Ask about analytics
python scripts/chat_graphrag.py --query "What analytics technologies are mentioned?" --deployment gpt-4.1

# Compare projects
python scripts/chat_graphrag.py --query "How do the projects compare?" --deployment gpt-4.1
```

## 🎯 How It Works

### Step 1: Hybrid Retrieval

When you ask a question:

**ChromaDB Vector Search:**
- Converts your question to 1024-dim embedding
- Searches 31 chunks for semantic similarity
- Returns top 10 most relevant chunks
- Score: 0-1 (higher = more similar)

**Neo4j Graph Search:**
- Extracts potential entities from your question
- Traverses knowledge graph for related entities
- Finds multi-hop relationships
- Score: Based on graph distance

**Fusion:**
- Combines vector results (weight: 0.6)
- Combines graph results (weight: 0.4)
- Ranks by combined score
- Returns top 5 results

### Step 2: Azure OpenAI Answer Generation

- Builds RAG prompt with retrieved context
- Calls Azure OpenAI gpt-4.1
- Generates answer citing sources
- Returns answer with citations

## 📊 Example Output

```
================================================================================
❓ QUESTION: What are the database technologies?
================================================================================

🔍 Retrieving relevant information...
  📊 Searching ChromaDB (vector similarity)...
  🕸️  Searching Neo4j (graph relationships)...

✓ Retrieved 5 relevant chunks

📚 Sources:

1. [VECTOR] Score: 0.155
   Project: beta_cloud_migration
   Source: cloud_migration_proposal.pdf
   Text: relational databases, DynamoDB for NoSQL, S3 for object storage...

2. [VECTOR] Score: 0.101
   Project: gamma_analytics_platform
   Source: analytics_platform_proposal.pdf
   Text: Data Lake (S3/HDFS) for raw data, Elasticsearch...

... (more sources)

🤖 Generating answer with Azure OpenAI...

================================================================================
💬 ANSWER:
================================================================================
The database technologies mentioned are:

- DynamoDB (NoSQL database) [Source 1]
- S3 (object storage/data lake) [Sources 1, 2, 4]
- HDFS (data lake storage) [Source 2]
- Elasticsearch (indexed/searchable data storage) [Sources 2, 4]
- PostgreSQL (relational database for metadata) [Source 2]
- Azure Blob (object storage/data lake) [Source 4]

================================================================================

📖 Citations:
1. beta_cloud_migration - cloud_migration_proposal.pdf (page 1) [vector]
2. gamma_analytics_platform - analytics_platform_proposal.pdf (page 1) [vector]
3. gamma_analytics_platform - analytics_specifications.pdf (page 1) [vector]
... (more citations)
```

## 🎨 Interactive Mode

```bash
python scripts/chat_graphrag.py --interactive --deployment gpt-4.1
```

Then ask questions in a chat loop:

```
🤖 HYBRID GRAPHRAG CHAT

Ask questions about your documents!
Type 'exit' or 'quit' to stop.

❓ Your question: What are the cloud technologies?

[System retrieves and answers...]

❓ Your question: Tell me about Kubernetes

[System retrieves and answers...]

❓ Your question: exit

👋 Goodbye!
```

## ⚙️ Command Line Options

```bash
python scripts/chat_graphrag.py [OPTIONS]

Options:
  --query TEXT          Single question to ask
  --interactive         Start chat mode
  --deployment TEXT     Azure OpenAI deployment (default: gpt-35-turbo)
  --top-k INT           Number of results (default: 5)

Examples:
  # Single question
  python scripts/chat_graphrag.py --query "What is SAP S/4HANA?" --deployment gpt-4.1

  # Interactive with more results
  python scripts/chat_graphrag.py --interactive --deployment gpt-4.1 --top-k 8

  # Different deployment
  python scripts/chat_graphrag.py --query "..." --deployment gpt-4-turbo
```

## 🔍 What the System Does

### 1. **Vector Search (ChromaDB)**
- Searches 31 chunks with embeddings
- Finds semantically similar content
- Fast and accurate for keyword/concept matching

### 2. **Graph Traversal (Neo4j)**
- Explores 97 entities and 158 relationships
- Finds related concepts through graph structure
- Discovers multi-hop connections

### 3. **Hybrid Fusion**
- Combines both approaches
- Weights: 60% vector, 40% graph
- Deduplicates and ranks results

### 4. **Azure OpenAI Generation**
- Uses retrieved context
- Generates coherent answers
- Cites sources automatically

## 📊 Your Data

```
Projects:           3 (alpha_erp_system, beta_cloud_migration, gamma_analytics_platform)
PDFs:               10
Chunks:             31 (with 1024-dim embeddings)
Entities:           97
Relationships:      158
Cross-Project:      2 entities (Kubernetes!)

Vector DB:          ChromaDB @ localhost:8002
Graph DB:           Neo4j @ localhost:7474
LLM:                Azure OpenAI gpt-4.1
```

## 🌐 Access Points

- **Neo4j Browser:** http://localhost:7474 (visualize graph)
- **ChromaDB:** localhost:8002 (in code only)
- **Chat:** Run `chat_graphrag.py` script

## ✅ System Status

All components operational:
- ✅ PDF processing
- ✅ REBEL knowledge extraction
- ✅ Vector embeddings (BGE-large)
- ✅ ChromaDB storage
- ✅ Neo4j storage
- ✅ Hybrid retrieval
- ✅ Azure OpenAI chat

**Your hybrid GraphRAG system is fully functional!** 🎉

## 💡 Pro Tips

1. **Try different queries** - The system understands your documents
2. **Check citations** - Every answer shows sources
3. **Use interactive mode** - Best for exploration
4. **Visit Neo4j browser** - Visualize the knowledge graph
5. **Adjust top-k** - Get more/fewer results

---

**Start chatting with your documents now!**

```bash
python scripts/chat_graphrag.py --interactive --deployment gpt-4.1
```
