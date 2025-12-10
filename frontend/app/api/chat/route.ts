export const dynamic = "force-dynamic"
export const maxDuration = 600  // 10 minutes timeout

interface SearchResult {
  id: string
  chunk_id?: string
  project_id?: string
  project_name?: string
  title?: string
  description?: string
  category?: string
  relevance?: number
  content?: string
  tags?: string[]
  metadata?: Record<string, unknown>
  source?: string
  file_name?: string
  page?: number
  year?: number
  technology?: string
  customer?: string
  createdAt?: string
  page_image?: string
  image_url?: string
  vector_score?: number
  llm_relevance_score?: number
  combined_score?: number
}

interface ChatMessage {
  role: "user" | "assistant"
  content: string
}

interface ChatRequestBody {
  query?: string
  topK?: number
  history?: ChatMessage[]
  useStreaming?: boolean
}

interface StreamEvent {
  step: string
  status: string
  message?: string
  projects_found?: number
  projects?: Array<{
    project_id: string
    project_name: string
    technology?: string
    year?: number
  }>
  chunks_found?: number
  top_chunks?: Array<{
    project_name: string
    page: number
    content: string
  }>
  answer?: string
  summary?: {
    projects: number
    chunks: number
  }
  all_projects?: Array<{
    project_id: string
    project_name: string
    technology?: string
    year?: number
  }>
}

export async function POST(req: Request) {
  let body: ChatRequestBody
  try {
    body = await req.json()
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 })
  }

  const query = body.query?.trim()
  if (!query) {
    return Response.json({ error: "Query is required" }, { status: 400 })
  }

  const topK = body.topK && body.topK > 0 ? Math.min(body.topK, 50) : 30
  const useStreaming = body.useStreaming !== false // Default to streaming

  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"

    if (useStreaming) {
      // ========== STREAMING MODE ==========
      // Use NEW Agentic Search SSE endpoint with gpt-oss:120b planning
      console.log(`[Chat] Using AGENTIC search for: "${query}"`)

      const streamUrl = `${backendUrl}/api/agentic-search-stream?` + new URLSearchParams({
        q: query,
        top_k: String(topK)
      })

      const encoder = new TextEncoder()

      const stream = new ReadableStream({
        async start(controller) {
          // Create AbortController with 5-minute timeout for streaming
          const abortController = new AbortController()
          const timeout = setTimeout(() => abortController.abort(), 300000) // 5 min timeout

          try {
            const response = await fetch(streamUrl, {
              signal: abortController.signal,
              headers: { 'Connection': 'keep-alive' }
            })

            if (!response.ok) {
              clearTimeout(timeout)
              controller.enqueue(encoder.encode(`data: ${JSON.stringify({ step: 'error', message: 'Backend error - please try again' })}\n\n`))
              controller.close()
              return
            }

            const reader = response.body?.getReader()
            if (!reader) {
              clearTimeout(timeout)
              controller.enqueue(encoder.encode(`data: ${JSON.stringify({ step: 'error', message: 'No response body' })}\n\n`))
              controller.close()
              return
            }

            const decoder = new TextDecoder()
            let buffer = ''

            while (true) {
              const { done, value } = await reader.read()
              if (done) break

              buffer += decoder.decode(value, { stream: true })

              // Process complete SSE events
              const lines = buffer.split('\n\n')
              buffer = lines.pop() || '' // Keep incomplete event in buffer

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  controller.enqueue(encoder.encode(line + '\n\n'))
                }
              }
            }

            // Process any remaining buffer
            if (buffer.startsWith('data: ')) {
              controller.enqueue(encoder.encode(buffer + '\n\n'))
            }

            clearTimeout(timeout)
            controller.close()
          } catch (error: any) {
            clearTimeout(timeout)
            console.error('[Chat] Streaming error:', error)
            const errorMsg = error.name === 'AbortError'
              ? 'Request timed out - please try again'
              : 'Connection error - please try again'
            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ step: 'error', message: errorMsg })}\n\n`))
            controller.close()
          }
        }
      })

      return new Response(stream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        }
      })
    } else {
      // ========== NON-STREAMING MODE ==========
      // Use NEW Agentic Search endpoint with gpt-oss:120b planning
      console.log(`[Chat] Using AGENTIC search (non-streaming) for: "${query}"`)

      const agenticUrl = `${backendUrl}/api/agentic-search?` + new URLSearchParams({
        q: query,
        debug: "false"
      })

      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 120000) // 2 min for LLM planning

      try {
        const agenticResponse = await fetch(agenticUrl, {
          signal: controller.signal,
          headers: { 'Connection': 'keep-alive' }
        })
        clearTimeout(timeout)

        if (!agenticResponse.ok) {
          throw new Error(`Agentic endpoint error: ${agenticResponse.status}`)
        }

        const agenticData = await agenticResponse.json()

        // Map projects to frontend format
        const mappedResults: SearchResult[] = (agenticData.projects || []).map((result: any, idx: number) => ({
          id: result.chunk_id || result.project_id || `result-${idx}`,
          chunk_id: result.chunk_id,
          project_id: result.project_id,
          project_name: result.project_name,
          title: result.project_name || result.project_id,
          description: (result.content || "").substring(0, 300),
          content: result.content,
          relevance: result.score || 0.8,
          page: result.page,
          year: result.year,
          technology: result.technology,
          customer: result.customer,
          file_name: result.file_name,
          source: result.file_name,
          page_image: result.page_image,
          image_url: result.page_image
            ? `/api/image/${result.project_id}/${result.page_image}`
            : undefined,
          metadata: {
            technology: result.technology,
            year: result.year,
            customer: result.customer,
            page: result.page,
            project_id: result.project_id,
            project_name: result.project_name,
            file_name: result.file_name
          }
        }))

        return Response.json({
          query,
          answer: agenticData.answer || "No answer generated.",
          results: mappedResults,
          total_projects: agenticData.total_projects,
          query_type: agenticData.query_type,
          tools_used: agenticData.tools_used
        })
      } catch (error: any) {
        clearTimeout(timeout)
        throw error
      }
    }

  } catch (error: any) {
    console.error("Error in /api/chat:", error)

    if (error.name === 'AbortError' || error.message?.includes('timeout')) {
      return Response.json(
        {
          query,
          answer: "The request took too long. Try a simpler question or use streaming mode.",
          results: []
        },
        { status: 200 }
      )
    }

    return Response.json(
      { error: "Failed to process chat request. Please try again later." },
      { status: 500 }
    )
  }
}
