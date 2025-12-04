export async function GET(request: Request) {
  const url = new URL(request.url)
  const query = url.searchParams.get("q")
  const searchType = url.searchParams.get("type") || "vector"

  if (!query) {
    return Response.json({ error: "Query parameter is required" }, { status: 400 })
  }

  try {
    // Call Python FastAPI backend based on search type
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

    // Map search type to backend endpoint
    // Vector: Pure semantic search (no filter extraction)
    // Metadata: LLM generates Cypher query for structured search
    const endpointMap: Record<string, string> = {
      "vector": "/api/search",
      "metadata": "/api/llm-search",  // LLM generates Cypher for metadata search
      "graph": "/api/graph-search",
      "multi-judge": "/api/multi-judge"
    }

    const endpoint = endpointMap[searchType] || "/api/search"

    // Build URL with appropriate parameters
    let url = `${backendUrl}${endpoint}?q=${encodeURIComponent(query)}`

    // For vector search, disable filter extraction (pure semantic search)
    if (searchType === "vector") {
      url += "&extract_filters=false"
    }

    const response = await fetch(url, {
      signal: AbortSignal.timeout(60000) // 60 second timeout for multi-judge
    })

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }

    const data = await response.json()

    // Handle different response formats based on search type
    let mappedResults: any[] = []
    let extraData: Record<string, any> = {}

    if (searchType === "graph") {
      // Graph search returns entities_found, relationships, and related_chunks
      // Map entities to display format
      const entities = data.entities_found || []
      const relatedChunks = data.related_chunks || []

      // Create results from entities first, then add related chunks
      mappedResults = entities.map((entity: any, idx: number) => ({
        id: `entity-${idx}`,
        title: typeof entity === 'string' ? entity : (entity.name || entity.entity || 'Unknown'),
        description: `Knowledge Graph Entity`,
        content: '',
        category: typeof entity === 'object' ? (entity.label || "Entity") : "Entity",
        relevance: 1.0 - (idx * 0.05), // Decreasing relevance by order
        tags: ["Graph Entity"],
        metadata: {
          type: "graph",
          relationships: data.relationships || []
        },
        source: "Knowledge Graph"
      }))

      // Also add related document chunks
      relatedChunks.forEach((chunk: any, idx: number) => {
        mappedResults.push({
          id: chunk.chunk_id || `chunk-${idx}`,
          title: chunk.project_id || "Related Document",
          description: chunk.text_preview || "",
          content: chunk.text_preview || "",
          category: chunk.technology || "Document",
          relevance: 0.8 - (idx * 0.02),
          tags: ["Related Document"],
          metadata: {
            project_id: chunk.project_id,
            technology: chunk.technology,
            year: chunk.year
          },
          source: chunk.project_id
        })
      })

      extraData = {
        graph_stats: data.graph_stats || data.stats,
        relationships: data.relationships
      }
    } else if (searchType === "multi-judge") {
      // Multi-judge returns paths.vector.results and final_answer
      const vectorResults = data.paths?.vector?.results || data.results || []

      mappedResults = vectorResults.map((result: any) => ({
        ...result,
        id: result.chunk_id || result.id || `chunk-${Math.random()}`,
        title: result.project_id || result.project_name || result.title || "",
        description: result.text || result.description || "",
        content: result.text || result.content || result.description || "",
        category: result.technology || result.category || "",
        relevance: result.score || result.final_score || result.relevance || 0,
        tags: [],
        metadata: {
          ...result.metadata,
          technology: result.technology,
          year: result.year,
          customer: result.customer,
          judge_scores: result.judge_scores
        },
        source: result.file_name || result.source,
        image_url: result.image_url || (result.page_image_relative ? `/api/image/${result.project_id}/${result.page_image_relative}` : undefined)
      }))

      // Extract super judge summary from final_answer
      extraData = {
        super_judge_summary: data.final_answer?.answer || data.super_judge_summary,
        judge_stats: {
          confidence: data.final_answer?.confidence,
          primary_source: data.final_answer?.primary_source,
          key_findings: data.final_answer?.key_findings
        }
      }
    } else {
      // Vector and metadata search - standard format
      mappedResults = Array.isArray(data.results) ? data.results.map((result: any) => ({
        ...result,
        id: result.chunk_id || result.id || `chunk-${Math.random()}`,
        title: result.project_name || result.title || "",
        description: result.text || result.description || "",
        content: result.text || result.content || result.description || "",
        category: result.technology || result.category || "",
        relevance: result.relevance || 0,
        tags: result.tags || [],
        metadata: result.metadata || {
          technology: result.technology,
          year: result.year,
          customer: result.customer,
          page: result.page,
          project_id: result.project_id,
          file_name: result.file_name
        },
        source: result.file_name || result.source,
        createdAt: result.createdAt,
        image_url: result.image_url || (result.page_image_relative ? `/api/image/${result.project_id}/${result.page_image_relative}` : undefined)
      })) : []
    }

    return Response.json({
      results: mappedResults,
      query: data.query || query,
      count: mappedResults.length,
      searchType,
      ...extraData
    })

  } catch (error) {
    console.error('Error calling backend API:', error)

    // Return empty results instead of mock data
    return Response.json({
      results: [],
      query,
      count: 0,
      error: "Failed to fetch results from database"
    })
  }
}