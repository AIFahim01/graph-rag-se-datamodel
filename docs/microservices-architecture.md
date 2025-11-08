# Microservices Architecture for Scalable GraphRAG

## Overview

This document describes the production microservices architecture designed to scale the Hybrid GraphRAG system to handle:
- 100s of projects
- 1000s of PDFs per project
- Large files (100MB+ each)
- Concurrent processing
- Fault tolerance and retry mechanisms

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GRAPHRAG MICROSERVICES PLATFORM                      │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────────┐
                              │  File Watcher    │
                              │    Service       │
                              └────────┬─────────┘
                                       │ Detects new PDFs
                                       ↓
                              ┌──────────────────┐
                              │    RabbitMQ      │ ← Message Broker
                              │  (Message Queue) │
                              └────────┬─────────┘
                                       │
                                       ↓
                              ┌──────────────────┐
                              │  Orchestrator    │ ← Workflow Coordinator
                              │    Service       │    + Progress Tracking
                              └────────┬─────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ↓                  ↓                  ↓
         ┌──────────────────┐  ┌──────────────┐  ┌─────────────────┐
         │ PDF Processor    │  │Vectorization │  │     Graph       │
         │    Workers       │  │   Workers    │  │ Construction    │
         │   (Pool of 3)    │  │  (Pool of 2) │  │   Workers       │
         │                  │  │  GPU-enabled │  │  (Pool of 2)    │
         │ • Text extract   │  │              │  │  GPU-enabled    │
         │ • Chunking       │  │ • BGE-large  │  │                 │
         │ • Validation     │  │ • Batch 32   │  │ • REBEL model   │
         └──────────────────┘  └──────────────┘  │ • Triplets      │
                    │                  │          └─────────────────┘
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                       ↓
                              ┌──────────────────┐
                              │  Storage Service │
                              │                  │
                              │ • ChromaDB load  │
                              │ • Neo4j load     │
                              │ • Bulk ops       │
                              └────────┬─────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ↓                  ↓                  ↓
         ┌──────────────────┐  ┌──────────────┐  ┌─────────────────┐
         │   PostgreSQL     │  │   ChromaDB   │  │     Neo4j       │
         │                  │  │              │  │                 │
         │ Progress tracking│  │ Vector store │  │  Knowledge      │
         │ State management │  │ 1024-dim     │  │  Graph store    │
         └──────────────────┘  └──────────────┘  └─────────────────┘
                                       │                  │
                                       └─────────┬────────┘
                                                 ↓
                                       ┌──────────────────┐
                                       │   API Service    │
                                       │                  │
                                       │ • Chat endpoint  │
                                       │ • Admin panel    │
                                       │ • Progress API   │
                                       │ • Azure OpenAI   │
                                       └──────────────────┘
                                                 ↓
                                         Users / Clients

         ┌──────────────────────────────────────────────────┐
         │           MONITORING & OBSERVABILITY              │
         ├──────────────────────────────────────────────────┤
         │  Prometheus  →  Grafana  →  Alertmanager        │
         │  (Metrics)      (Dashboards)   (Alerts)          │
         └──────────────────────────────────────────────────┘
```

## Service Details

### 1. File Watcher Service

**Purpose:** Monitors directories for new PDF files

**Technology:** Python + watchdog library

**Inputs:**
- Configured watch directories (per project)
- File patterns (*.pdf)

**Outputs:**
- Messages to `pdf.uploaded` queue

**Key Features:**
- SHA256 file hashing for deduplication
- File validation (size, format)
- Multi-directory monitoring
- Graceful shutdown

**Message Format:**
```json
{
  "event_type": "pdf.uploaded",
  "file_path": "/data/pdfs/project_001/document.pdf",
  "project_name": "project_001",
  "file_hash": "sha256:abc123...",
  "file_size_bytes": 5242880,
  "timestamp": "2025-11-08T10:00:00Z"
}
```

### 2. Orchestrator Service

**Purpose:** Workflow coordination and progress tracking

**Technology:** Python + SQLAlchemy + pika (RabbitMQ client)

**Responsibilities:**
- Creates processing tasks in PostgreSQL
- Dispatches tasks to appropriate queues
- Monitors task completion
- Updates project/file status
- Handles retry logic
- Circuit breaker management

**State Machine:**
```
pending → in_progress → completed
    ↓          ↓            ↑
    └─→ failed ─→ retry ───┘
              ↓
          (max retries)
              ↓
        permanently_failed
```

**Workflow Logic:**
```python
async def orchestrate_file_processing(file_event):
    # 1. Create project if not exists
    project = await db.get_or_create_project(file_event['project_name'])

    # 2. Check for duplicate (file hash)
    existing = await db.get_file_by_hash(file_event['file_hash'])
    if existing and existing.status == 'completed':
        logger.info(f"File already processed: {file_event['file_path']}")
        return

    # 3. Create file record
    file = await db.create_file(
        project_id=project.id,
        file_path=file_event['file_path'],
        file_hash=file_event['file_hash'],
        status='pending'
    )

    # 4. Create processing tasks
    tasks = []

    # Task 1: PDF extraction
    pdf_task = await db.create_task(
        file_id=file.id,
        task_type='pdf_extract',
        status='pending'
    )
    tasks.append(pdf_task)

    # Task 2-3: Vectorization and graph building (wait for task 1)
    # Will be created after PDF extraction completes

    # 5. Dispatch first task
    await rabbitmq.publish(
        exchange='graphrag.direct',
        routing_key='pdf.extract.tasks',
        message={'task_id': pdf_task.id, 'file_id': file.id}
    )

    logger.info(f"Orchestrated processing for file {file.id}")
```

### 3. PDF Processor Service (Worker Pool)

**Purpose:** Extract text and create chunks from PDFs

**Technology:** Python + PyMuPDF + RabbitMQ consumer

**Inputs:**
- RabbitMQ queue: `pdf.extract.tasks`
- Message: `{task_id, file_id, file_path}`

**Processing:**
```python
async def process_pdf_task(message):
    task_id = message['task_id']
    file_id = message['file_id']

    # Update task status
    await db.update_task(task_id, status='in_progress', worker_id=worker_id)

    try:
        # 1. Extract text
        extractor = PDFExtractor()
        pages = extractor.extract(file_path)

        # 2. Create chunks
        chunker = DocumentChunker(chunk_size=400, overlap=40)
        chunks = chunker.chunk_pages(pages)

        # 3. Save chunks to PostgreSQL
        chunk_ids = []
        for chunk in chunks:
            chunk_id = await db.create_chunk(
                file_id=file_id,
                chunk_identifier=chunk['chunk_id'],
                page_number=chunk['page'],
                text=chunk['text']
            )
            chunk_ids.append(chunk_id)

        # 4. Update task as completed
        await db.update_task(
            task_id,
            status='completed',
            output_data={'chunk_ids': chunk_ids, 'total_chunks': len(chunks)}
        )

        # 5. Trigger next tasks (vectorization + graph building)
        await orchestrator.trigger_next_tasks(task_id, chunk_ids)

    except Exception as e:
        await handle_task_failure(task_id, e)
```

**Outputs:**
- Chunks stored in PostgreSQL
- Messages to `vectorize.tasks` and `graph.build.tasks` queues

**Scaling:** Deploy 3-10 workers based on load

### 4. Vectorization Service (Worker Pool)

**Purpose:** Generate embeddings for chunks

**Technology:** Python + sentence-transformers + GPU

**Inputs:**
- RabbitMQ queue: `vectorize.tasks`
- Chunks from PostgreSQL

**Processing:**
```python
async def vectorize_chunks(message):
    task_id = message['task_id']
    chunk_ids = message['chunk_ids']

    # Update task status
    await db.update_task(task_id, status='in_progress', worker_id=worker_id)

    try:
        # 1. Load chunks
        chunks = await db.get_chunks(chunk_ids)

        # 2. Generate embeddings (batched)
        generator = VectorGenerator(model_name='BAAI/bge-large-en-v1.5')
        embeddings = generator.embed_chunks(chunks)  # GPU-accelerated

        # 3. Store embedding records
        for chunk_id, embedding_index in zip(chunk_ids, range(len(embeddings))):
            await db.create_embedding(
                chunk_id=chunk_id,
                embedding_index=embedding_index,
                model_name='BAAI/bge-large-en-v1.5'
            )

        # 4. Send to storage
        await rabbitmq.publish(
            'storage.vector.tasks',
            {
                'task_id': task_id,
                'chunk_ids': chunk_ids,
                'embeddings': embeddings.tolist(),
                'file_id': message['file_id']
            }
        )

        await db.update_task(task_id, status='completed')

    except Exception as e:
        await handle_task_failure(task_id, e)
```

**Outputs:**
- Embeddings stored in PostgreSQL (records)
- Messages to `storage.vector.tasks` with actual vectors

**Scaling:** GPU-enabled, 2-4 workers

### 5. Graph Construction Service

**Purpose:** Extract knowledge graph using REBEL

**Technology:** Python + transformers + REBEL model

**Similar to vectorization but runs REBEL extraction**

**Scaling:** GPU-enabled, 2-4 workers

### 6. Storage Service

**Purpose:** Load data into ChromaDB and Neo4j

**Technology:** Python + chromadb + neo4j drivers

**Handles bulk loading efficiently**

### 7. API Service

**Purpose:** User-facing API and chat interface

**Technology:** FastAPI + existing hybrid retriever

**Endpoints:**
- `POST /chat` - Ask questions
- `GET /projects` - List projects
- `GET /projects/{id}/status` - Progress tracking
- `GET /health` - System health

## 📊 PostgreSQL Schema

Complete schema with 9 tables tracking:
- Projects, Files, Tasks
- Chunks, Embeddings
- KG Entities, Relations
- Service Health, Circuit Breakers

## 🔄 Retry & Circuit Breaker

- Exponential backoff retry (3 attempts)
- Circuit breaker for each service
- Dead letter queue for permanent failures
- Progress tracking in PostgreSQL

## 📈 Monitoring

- Prometheus metrics
- Grafana dashboards
- Alert rules for failures
- Service health tracking

---

**Would you like me to create:**
1. Visual architecture diagrams (PlantUML/Mermaid)?
2. Detailed service design docs?
3. Docker compose file?
4. PostgreSQL schema SQL?

Let me know which parts you want documented first!