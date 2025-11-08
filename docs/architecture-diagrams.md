# Architecture Diagrams - Microservices GraphRAG

## 1. System Context Diagram

```mermaid
graph TB
    Users[Users/Clients]
    PDFs[PDF Documents]

    subgraph "GraphRAG Platform"
        API[API Service<br/>FastAPI]
        FileWatcher[File Watcher]
        Orchestrator[Orchestrator]
        PDFProc[PDF Processors<br/>x3 workers]
        Vector[Vectorization<br/>x2 GPU workers]
        Graph[Graph Construction<br/>x2 GPU workers]
        Storage[Storage Service]
    end

    subgraph "Infrastructure"
        RabbitMQ[RabbitMQ<br/>Message Queue]
        Postgres[(PostgreSQL<br/>Progress DB)]
        Chroma[(ChromaDB<br/>Vector Store)]
        Neo4j[(Neo4j<br/>Knowledge Graph)]
    end

    subgraph "Monitoring"
        Prometheus[Prometheus]
        Grafana[Grafana<br/>Dashboards]
    end

    PDFs --> FileWatcher
    FileWatcher --> RabbitMQ
    RabbitMQ --> Orchestrator
    Orchestrator --> Postgres
    Orchestrator --> RabbitMQ

    RabbitMQ --> PDFProc
    RabbitMQ --> Vector
    RabbitMQ --> Graph

    PDFProc --> Postgres
    Vector --> Postgres
    Graph --> Postgres

    PDFProc --> RabbitMQ
    Vector --> RabbitMQ
    Graph --> RabbitMQ

    RabbitMQ --> Storage
    Storage --> Chroma
    Storage --> Neo4j
    Storage --> Postgres

    API --> Chroma
    API --> Neo4j
    API --> Postgres
    API --> AzureOpenAI[Azure OpenAI]

    Users --> API

    Orchestrator -.-> Prometheus
    PDFProc -.-> Prometheus
    Vector -.-> Prometheus
    Graph -.-> Prometheus
    Storage -.-> Prometheus
    API -.-> Prometheus

    Prometheus --> Grafana
    Grafana --> Users

    style API fill:#4ECDC4
    style FileWatcher fill:#95E1D3
    style Orchestrator fill:#FFD93D
    style PDFProc fill:#FF6B6B
    style Vector fill:#C44569
    style Graph fill:#A8E6CE
    style Storage fill:#FFDAC1
```

## 2. Data Flow Diagram

```mermaid
sequenceDiagram
    participant FS as File System
    participant FW as File Watcher
    participant RMQ as RabbitMQ
    participant ORC as Orchestrator
    participant DB as PostgreSQL
    participant PDF as PDF Processor
    participant VEC as Vectorization
    participant GRP as Graph Builder
    participant STR as Storage
    participant CHR as ChromaDB
    participant NEO as Neo4j

    FS->>FW: New PDF detected
    FW->>FW: Calculate hash
    FW->>RMQ: Publish pdf.uploaded

    RMQ->>ORC: Consume pdf.uploaded
    ORC->>DB: Check if file exists (hash)

    alt File already processed
        DB-->>ORC: File exists, status=completed
        ORC->>ORC: Skip processing
    else New file
        DB-->>ORC: File not found
        ORC->>DB: INSERT project (if new)
        ORC->>DB: INSERT file (status=pending)
        ORC->>DB: INSERT task (type=pdf_extract)
        ORC->>RMQ: Publish to pdf.extract.tasks

        RMQ->>PDF: Consume task
        PDF->>DB: UPDATE task (status=in_progress)
        PDF->>PDF: Extract text + chunk
        PDF->>DB: INSERT chunks
        PDF->>DB: UPDATE task (status=completed)
        PDF->>RMQ: Publish to vectorize.tasks
        PDF->>RMQ: Publish to graph.build.tasks

        par Parallel Processing
            RMQ->>VEC: Consume vectorize task
            VEC->>DB: Get chunks
            VEC->>VEC: Generate embeddings (GPU)
            VEC->>DB: INSERT embeddings
            VEC->>RMQ: Publish to storage.vector.tasks
            VEC->>DB: UPDATE task (completed)
        and
            RMQ->>GRP: Consume graph build task
            GRP->>DB: Get chunks
            GRP->>GRP: REBEL extraction (GPU)
            GRP->>DB: INSERT entities + relations
            GRP->>RMQ: Publish to storage.graph.tasks
            GRP->>DB: UPDATE task (completed)
        end

        par Storage Operations
            RMQ->>STR: Consume storage.vector
            STR->>CHR: Bulk insert vectors
            STR->>DB: UPDATE embedding (chromadb_id)
            STR->>DB: UPDATE task (completed)
        and
            RMQ->>STR: Consume storage.graph
            STR->>NEO: Create entities + relationships
            STR->>DB: UPDATE task (completed)
        end

        STR->>DB: UPDATE file (status=completed)
        STR->>DB: UPDATE project counters
    end
```

## 3. Database Schema Diagram

```mermaid
erDiagram
    PROJECTS ||--o{ FILES : contains
    FILES ||--o{ PROCESSING_TASKS : has
    FILES ||--o{ CHUNKS : contains
    CHUNKS ||--o{ EMBEDDINGS : has
    KG_ENTITIES ||--o{ KG_RELATIONS : "head/tail"
    CHUNKS ||--o{ KG_RELATIONS : source
    PROJECTS ||--o{ KG_ENTITIES : mentions

    PROJECTS {
        int project_id PK
        string project_name UK
        string status
        int total_files
        int completed_files
        int failed_files
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    FILES {
        int file_id PK
        int project_id FK
        string file_path
        string file_name
        string file_hash UK
        bigint file_size_bytes
        string status
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    PROCESSING_TASKS {
        int task_id PK
        int file_id FK
        string task_type
        string status
        string worker_id
        int retry_count
        int max_retries
        text error_message
        jsonb input_data
        jsonb output_data
        timestamp started_at
        timestamp completed_at
    }

    CHUNKS {
        int chunk_id PK
        int file_id FK
        string chunk_identifier
        int page_number
        text text
        jsonb metadata
    }

    EMBEDDINGS {
        int embedding_id PK
        int chunk_id FK
        int embedding_index
        string chromadb_id
        string model_name
    }

    KG_ENTITIES {
        int entity_id PK
        string entity_name
        int[] project_ids
        int total_mentions
        bool is_cross_project
        jsonb metadata
    }

    KG_RELATIONS {
        int relation_id PK
        int head_entity_id FK
        int tail_entity_id FK
        string relation_type
        int project_id FK
        int source_chunk_id FK
        jsonb metadata
    }

    SERVICE_HEALTH {
        int health_id PK
        string service_name
        string status
        timestamp last_heartbeat
        int error_count
    }

    CIRCUIT_BREAKERS {
        int breaker_id PK
        string service_name
        string target_service UK
        string state
        int failure_count
        timestamp last_failure_time
        timestamp next_retry_time
    }
```

## 4. Service Communication Diagram

```mermaid
graph LR
    subgraph "Entry Point"
        FW[File Watcher]
    end

    subgraph "Message Broker"
        RMQ[RabbitMQ<br/>7 Queues]
    end

    subgraph "Coordination"
        ORC[Orchestrator<br/>+Circuit Breakers]
    end

    subgraph "Worker Pools"
        PDF1[PDF Worker 1]
        PDF2[PDF Worker 2]
        PDF3[PDF Worker 3]
        VEC1[Vector Worker 1<br/>GPU]
        VEC2[Vector Worker 2<br/>GPU]
        GRP1[Graph Worker 1<br/>GPU]
        GRP2[Graph Worker 2<br/>GPU]
    end

    subgraph "Storage"
        STR[Storage Service]
    end

    subgraph "Databases"
        PG[(PostgreSQL)]
        CHR[(ChromaDB)]
        N4J[(Neo4j)]
    end

    subgraph "User Interface"
        API[API Service]
    end

    FW -->|pdf.uploaded| RMQ
    RMQ -->|dispatch| ORC
    ORC -->|tasks| RMQ
    ORC <-->|track state| PG

    RMQ -->|pdf.extract| PDF1
    RMQ -->|pdf.extract| PDF2
    RMQ -->|pdf.extract| PDF3

    PDF1 -->|chunks| RMQ
    PDF2 -->|chunks| RMQ
    PDF3 -->|chunks| RMQ

    PDF1 <-->|status| PG
    PDF2 <-->|status| PG
    PDF3 <-->|status| PG

    RMQ -->|vectorize| VEC1
    RMQ -->|vectorize| VEC2

    VEC1 -->|vectors| RMQ
    VEC2 -->|vectors| RMQ

    VEC1 <-->|status| PG
    VEC2 <-->|status| PG

    RMQ -->|graph.build| GRP1
    RMQ -->|graph.build| GRP2

    GRP1 -->|triplets| RMQ
    GRP2 -->|triplets| RMQ

    GRP1 <-->|status| PG
    GRP2 <-->|status| PG

    RMQ -->|storage| STR
    STR -->|vectors| CHR
    STR -->|graph| N4J
    STR <-->|status| PG

    API <-->|query| CHR
    API <-->|traverse| N4J
    API <-->|progress| PG

    style ORC fill:#FFD93D
    style PDF1 fill:#FF6B6B
    style PDF2 fill:#FF6B6B
    style PDF3 fill:#FF6B6B
    style VEC1 fill:#C44569
    style VEC2 fill:#C44569
    style GRP1 fill:#A8E6CE
    style GRP2 fill:#A8E6CE
    style STR fill:#FFDAC1
    style API fill:#4ECDC4
```

## 5. Retry & Circuit Breaker State Machine

```mermaid
stateDiagram-v2
    [*] --> Pending: Task Created

    Pending --> InProgress: Worker picks up
    InProgress --> Completed: Success
    InProgress --> Failed: Error

    Failed --> Retry: retry_count < max_retries
    Retry --> Pending: Retry scheduled

    Failed --> PermanentlyFailed: retry_count >= max_retries
    PermanentlyFailed --> DeadLetterQueue

    Completed --> [*]

    note right of Failed
        Circuit Breaker
        monitors failures

        5 failures → OPEN
        Blocks requests

        After timeout → HALF_OPEN
        Test with 1 request

        Success → CLOSED
    end note
```

## 6. Deployment Architecture

```
Production Environment:

┌─────────────────────────────────────────────────────────────┐
│                      Docker Swarm / Kubernetes               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │  ← Auto-scaling │
│  │  Node    │  │  Node    │  │  Node    │                 │
│  ├──────────┤  ├──────────┤  ├──────────┤                 │
│  │ PDF x3   │  │ PDF x3   │  │ PDF x3   │                 │
│  │ Vec x2   │  │ Vec x2   │  │ Vec x2   │                 │
│  │ Graph x2 │  │ Graph x2 │  │ Graph x2 │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│                                                              │
│  ┌──────────────────────────────────────┐                  │
│  │     Shared Services (Single)         │                  │
│  ├──────────────────────────────────────┤                  │
│  │ • RabbitMQ (clustered)              │                  │
│  │ • PostgreSQL (primary + replicas)   │                  │
│  │ • ChromaDB (distributed)            │                  │
│  │ • Neo4j (clustered)                 │                  │
│  │ • API (load balanced)               │                  │
│  │ • Prometheus + Grafana              │                  │
│  └──────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## 7. Security Architecture

```
External → Nginx (SSL/TLS) → API Service (JWT Auth) → Internal Services

Authentication Flow:
1. User → API: Login (username/password)
2. API → PostgreSQL: Validate credentials
3. API → User: JWT token
4. User → API: Request + JWT
5. API: Validate JWT
6. API → Services: Process request

Internal Communication:
- Service-to-service: mTLS or service mesh (Istio)
- Database: Connection pooling with credentials from secrets
- RabbitMQ: User/password authentication
```

## 8. Scaling Strategy

```
Load Distribution:

Light Load (< 100 PDFs/day):
├─ PDF Processors: 2 workers
├─ Vectorization: 1 worker (GPU)
├─ Graph Building: 1 worker (GPU)
└─ Storage: 1 service

Medium Load (100-1000 PDFs/day):
├─ PDF Processors: 5 workers
├─ Vectorization: 2 workers (GPU)
├─ Graph Building: 2 workers (GPU)
└─ Storage: 2 services

Heavy Load (> 1000 PDFs/day):
├─ PDF Processors: 10+ workers (auto-scale)
├─ Vectorization: 4+ workers (multi-GPU)
├─ Graph Building: 4+ workers (multi-GPU)
└─ Storage: 3+ services (partitioned)

Bottleneck Identification:
- Monitor RabbitMQ queue depths
- Track PostgreSQL task status distribution
- Watch GPU utilization
- Auto-scale based on queue backlog
```

## 9. Failure Recovery

```
Failure Scenarios & Recovery:

1. Worker Crash:
   ├─ RabbitMQ: Message not ACKed → requeued
   ├─ PostgreSQL: Task status=in_progress → reset to pending
   └─ Orchestrator: Detects stale task → reassigns

2. Database Unavailable:
   ├─ Circuit Breaker: Opens after 5 failures
   ├─ Workers: Cache operations locally
   ├─ Queue: Messages accumulate
   └─ Recovery: Circuit breaker closes → replay

3. GPU Out of Memory:
   ├─ Worker: Catches OOM error
   ├─ Retry: Reduces batch size
   └─ Success: Completes with smaller batches

4. Network Partition:
   ├─ RabbitMQ: Message TTL expires
   ├─ Worker: Health check fails
   └─ Orchestrator: Marks worker as down → redistributes

5. Corrupt PDF:
   ├─ PDF Processor: Extraction fails
   ├─ Retry: 3 attempts with backoff
   ├─ Permanent Failure: Moves to DLQ
   └─ Admin: Manual review required
```

## 10. Progress Tracking

```
Real-time Progress Dashboard:

Project: alpha_erp_system
├─ Total Files: 100
├─ Completed: 75 (75%)
├─ In Progress: 15 (15%)
├─ Failed: 5 (5%)
├─ Pending: 5 (5%)
│
├─ Stage Breakdown:
│   ├─ PDF Extraction: 100/100 ✓
│   ├─ Vectorization: 85/100 (85%)
│   ├─ Graph Building: 80/100 (80%)
│   └─ Storage: 75/100 (75%)
│
└─ ETA: 45 minutes (based on current throughput)

Query Endpoint:
GET /api/projects/alpha_erp_system/status

Response:
{
  "project_name": "alpha_erp_system",
  "progress": {
    "total_files": 100,
    "completed": 75,
    "in_progress": 15,
    "failed": 5,
    "pending": 5,
    "percentage": 75.0
  },
  "stages": {
    "pdf_extraction": {"completed": 100, "total": 100},
    "vectorization": {"completed": 85, "total": 100},
    "graph_building": {"completed": 80, "total": 100},
    "storage": {"completed": 75, "total": 100}
  },
  "eta_minutes": 45,
  "throughput_files_per_hour": 120
}
```

---

These diagrams can be rendered using:
- **Mermaid**: Supported in GitHub, VS Code, many markdown viewers
- **PlantUML**: For more detailed diagrams
- **draw.io**: For custom architecture diagrams

Copy the mermaid code blocks into tools like:
- https://mermaid.live/ (online viewer)
- VS Code with Mermaid extension
- GitHub markdown (renders automatically)
