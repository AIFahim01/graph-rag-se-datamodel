export const dynamic = "force-dynamic"
export const maxDuration = 300  // 5 minutes timeout for iterative search

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
}

interface ChatRequestBody {
  query?: string
  topK?: number
  useStreaming?: boolean
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
      // Use Iterative Search Stream: Metadata + Graph + Vector + Answer
      console.log(`[Chat-Classic] Using ITERATIVE search stream for: "${query}"`)

      const streamUrl = `${backendUrl}/api/iterative-search-stream?` + new URLSearchParams({
        q: query,
        top_k: String(topK)
      })

      const encoder = new TextEncoder()

      const stream = new ReadableStream({
        async start(controller) {
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
              buffer = lines.pop() || ''

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  controller.enqueue(encoder.encode(line + '\n\n'))
                }
              }
            }

            // Process remaining buffer
            if (buffer.startsWith('data: ')) {
              controller.enqueue(encoder.encode(buffer + '\n\n'))
            }

            clearTimeout(timeout)
            controller.close()
          } catch (error: any) {
            clearTimeout(timeout)
            console.error('[Chat-Classic] Streaming error:', error)
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
      // Fall back to llm-search for non-streaming
      console.log(`[Chat-Classic] Using LLM search (non-streaming) for: "${query}"`)

      const llmSearchUrl = `${backendUrl}/api/llm-search?` + new URLSearchParams({
        q: query,
        use_llm: "true",
        debug: "false"
      })

      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 60000)

      try {
        const response = await fetch(llmSearchUrl, {
          signal: controller.signal,
          headers: { 'Connection': 'keep-alive' }
        })
        clearTimeout(timeout)

        if (!response.ok) {
          throw new Error(`LLM search error: ${response.status}`)
        }

        const data = await response.json()

        if (data.error) {
          return Response.json({
            query,
            answer: `Error: ${data.error}`,
            results: [],
            debug: data.debug
          })
        }

        const mappedResults: SearchResult[] = (data.results || []).map((result: any, idx: number) => ({
          id: result.chunk_id || result.project_id || `result-${idx}`,
          chunk_id: result.chunk_id,
          project_id: result.project_id,
          project_name: result.project_name || result.project_id,
          title: result.project_name || result.project_id || result.file_name,
          description: (result.text || result.content || "").substring(0, 300),
          content: result.text || result.content,
          relevance: result.relevance || result.score || 0.8,
          page: result.page,
          year: result.year,
          technology: result.technology,
          customer: result.customer,
          file_name: result.file_name,
          source: result.file_name,
          page_image: result.page_image_relative,
          image_url: result.page_image_relative
            ? `/api/image/${result.project_id}/${result.page_image_relative}`
            : undefined,
          metadata: {
            technology: result.technology,
            year: result.year,
            customer: result.customer,
            page: result.page,
            project_id: result.project_id,
            file_name: result.file_name
          }
        }))

        const totalResults = mappedResults.length
        const uniqueProjects = [...new Set(mappedResults.map(r => r.project_id))].filter(Boolean)

        let answer = `Found ${totalResults} results across ${uniqueProjects.length} projects.`
        if (uniqueProjects.length > 0 && uniqueProjects.length <= 10) {
          const projectList = uniqueProjects.map(p => `- ${p}`).join("\n")
          answer += `\n\nProjects:\n${projectList}`
        }

        return Response.json({
          query,
          answer,
          results: mappedResults,
          total_results: totalResults,
          query_type: data.query_type || "llm",
          search_mode: "classic-iterative"
        })

      } catch (error: any) {
        clearTimeout(timeout)
        throw error
      }
    }

  } catch (error: any) {
    console.error("Error in /api/chat-classic:", error)

    if (error.name === 'AbortError' || error.message?.includes('timeout')) {
      return Response.json(
        {
          query,
          answer: "The request took too long. Please try a simpler question.",
          results: [],
          search_mode: "classic"
        },
        { status: 200 }
      )
    }

    return Response.json(
      { error: "Failed to process search request. Please try again later." },
      { status: 500 }
    )
  }
}
