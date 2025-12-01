export async function GET(request: Request) {
  const url = new URL(request.url)
  const query = url.searchParams.get("q")

  if (!query) {
    return Response.json({ error: "Query parameter is required" }, { status: 400 })
  }

  try {
    // Call Python FastAPI backend for real Neo4j vector search
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
    const response = await fetch(`${backendUrl}/api/llm-search?q=${encodeURIComponent(query)}`, {
      signal: AbortSignal.timeout(30000) // 30 second timeout
    })

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }

    const data = await response.json()

    // Map the results to ensure compatibility with frontend
    const mappedResults = Array.isArray(data.results) ? data.results.map((result: any) => ({
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

    return Response.json({
      results: mappedResults,
      query: data.query || query,
      count: mappedResults.length
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