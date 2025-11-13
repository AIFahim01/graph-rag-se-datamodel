# Neo4j Browser Visualization Queries
**REBEL Knowledge Graph - HVDC/SYNCON Projects**

Access Neo4j Browser: http://localhost:7474
- Username: `neo4j`
- Password: `password`

---

## Quick Start Queries

### 1. Overview - Sample the Graph
```cypher
MATCH (n)
RETURN n
LIMIT 100
```

### 2. View Projects and Their Entities
```cypher
MATCH (p:Project)-[:MENTIONS]->(e:Entity)
RETURN p, e
LIMIT 50
```

### 3. Find Most Connected Entities (Hub Nodes)
```cypher
MATCH (e:Entity)
WITH e, size((e)-[:RELATED]-()) as connections
WHERE connections > 5
MATCH (e)-[r:RELATED]->(other:Entity)
RETURN e, r, other
LIMIT 100
```

---

## Domain-Specific Queries

### 4. Explore HVDC Entities
```cypher
MATCH (e:Entity)
WHERE e.name CONTAINS 'HVDC' OR e.name CONTAINS 'hvdc'
MATCH path = (e)-[*1..2]-(connected)
RETURN path
LIMIT 50
```

### 5. Find Siemens-Related Network
```cypher
MATCH (e:Entity)
WHERE e.name CONTAINS 'Siemens'
MATCH (e)-[r]-(connected)
RETURN e, r, connected
LIMIT 100
```

### 6. Protection Systems Network
```cypher
MATCH (e:Entity)
WHERE e.name CONTAINS 'protection' OR e.name CONTAINS 'Protection'
MATCH path = (e)-[*1..2]-(connected)
RETURN path
LIMIT 50
```

### 7. VSC Technology Connections
```cypher
MATCH (e:Entity)
WHERE e.name CONTAINS 'VSC'
MATCH path = (e)-[*1..2]-(connected)
RETURN path
LIMIT 50
```

---

## Network Analysis Queries

### 8. Project Network View (Shared Entities)
```cypher
MATCH (p:Project)-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(p2:Project)
WHERE p <> p2
RETURN p, e, p2
LIMIT 50
```

### 9. Entity Relationship Chains
```cypher
MATCH path = (e1:Entity)-[:RELATED]->(e2:Entity)-[:RELATED]->(e3:Entity)
WHERE e1.mentions > 10 AND e2.mentions > 10 AND e3.mentions > 10
RETURN path
LIMIT 25
```

### 10. Find Entities Across Multiple Projects
```cypher
MATCH (e:Entity)
WHERE e.num_projects > 5
MATCH (e)<-[:MENTIONS]-(p:Project)
RETURN e, p
LIMIT 50
```

---

## Statistical Queries

### 11. Top 10 Most Mentioned Entities
```cypher
MATCH (e:Entity)
RETURN e.name as Entity, e.mentions as Mentions, e.num_projects as Projects
ORDER BY e.mentions DESC
LIMIT 10
```

### 12. Top Projects by Entity Count
```cypher
MATCH (p:Project)-[:MENTIONS]->(e:Entity)
WITH p, count(e) as entity_count
RETURN p.name as Project, entity_count
ORDER BY entity_count DESC
LIMIT 10
```

### 13. Full Graph Statistics
```cypher
MATCH (n)
WITH count(n) as TotalNodes
MATCH ()-[r]->()
WITH TotalNodes, count(r) as TotalRelationships
MATCH (e:Entity)
WITH TotalNodes, TotalRelationships, count(e) as Entities
MATCH (p:Project)
RETURN TotalNodes, TotalRelationships, Entities, count(p) as Projects
```

### 14. Relationship Type Distribution
```cypher
MATCH ()-[r:RELATED]->()
RETURN r.type as RelationType, count(*) as Count
ORDER BY Count DESC
LIMIT 20
```

---

## Path Finding Queries

### 15. Find Shortest Path Between Two Entities
```cypher
MATCH (start:Entity {name: 'HVDC'}),
      (end:Entity {name: 'Siemens AG'})
MATCH path = shortestPath((start)-[*..5]-(end))
RETURN path
```

### 16. Find All Paths Between Projects
```cypher
MATCH (p1:Project {name: 'GC25_124_HVDC_VSC_Sarawak_SingaporePowerLtd'}),
      (p2:Project {name: 'GC25_035_SEC_Central_East_HVDC_FEED'})
MATCH path = (p1)-[:MENTIONS]->(:Entity)<-[:MENTIONS]-(p2)
RETURN path
LIMIT 10
```

---

## Advanced Visualization

### 17. Degree Centrality (Most Connected Nodes)
```cypher
MATCH (e:Entity)
WITH e, size((e)--()) as degree
WHERE degree > 10
MATCH (e)-[r]-(connected)
RETURN e, r, connected
ORDER BY degree DESC
LIMIT 50
```

### 18. Community Detection (Clusters)
```cypher
MATCH (e:Entity)
WHERE e.num_projects >= 3
MATCH path = (e)-[:RELATED*1..2]-(other:Entity)
WHERE other.num_projects >= 3
RETURN path
LIMIT 100
```

---

## Exploration Tips

1. **Start Small**: Use `LIMIT` to avoid overwhelming visualizations
2. **Expand Gradually**: Click on nodes to expand their connections
3. **Filter by Properties**: Use `WHERE` clauses to focus on specific entities
4. **Customize Appearance**:
   - Click node types in legend to change colors/sizes
   - Set node size based on `mentions` property
   - Set caption to `name` property
5. **Save Favorites**: Bookmark useful queries in Neo4j Browser

---

## Quick Access Commands

```bash
# Access Neo4j Browser
http://localhost:7474

# Check Neo4j status
docker ps | grep neo4j

# Restart Neo4j if needed
docker restart neo4j
```

---

## Legend

- **Entity** (Entity nodes): Technical entities from documents
- **Project** (Project nodes): HVDC/SYNCON project names
- **RELATED** (Relationships): Entity-to-entity relationships
- **MENTIONS** (Relationships): Project-to-entity connections

---

**Total in Graph:**
- 1,674 Entities
- 12,522 Relationships
- 28 Projects
