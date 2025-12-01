export const dynamic = "force-dynamic"
// Increase the route segment config timeout
export const maxDuration = 60 // Maximum allowed duration in seconds

interface SearchResult {
  id: string
  title?: string
  description?: string
  category?: string
  relevance?: number
  content?: string
  tags?: string[]
  metadata?: Record<string, unknown>
  source?: string
  createdAt?: string
}

interface SearchApiResponse {
  results: SearchResult[]
  query: string
  count: number
}

interface ChatMessage {
  role: "user" | "assistant"
  content: string
}

interface ChatRequestBody {
  query?: string
  topK?: number
  history?: ChatMessage[]
}

interface DatabaseStats {
  total_projects?: number
  hvdc_count?: number
  syncon_count?: number
  hvdc_projects?: string[]
  syncon_projects?: string[]
}

interface ChatResponseBody {
  query: string
  answer: string
  results: SearchResult[]
}

// Custom fetch with proper timeout and retry logic
async function fetchWithTimeout(url: string, options: RequestInit = {}, timeoutMs: number = 30000): Promise<Response> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      // Add keep-alive to prevent connection timeouts
      headers: {
        ...options.headers,
        'Connection': 'keep-alive'
      }
    })
    clearTimeout(timeout)
    return response
  } catch (error: any) {
    clearTimeout(timeout)

    // Check if it's a timeout error
    if (error.name === 'AbortError' || error.code === 'UND_ERR_CONNECT_TIMEOUT') {
      console.error(`Request timeout after ${timeoutMs}ms for URL: ${url}`)
      throw new Error(`Request timeout after ${timeoutMs}ms`)
    }

    // Log other errors for debugging
    console.error(`Fetch error for URL ${url}:`, error)
    throw error
  }
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

  const topK = body.topK && body.topK > 0 ? Math.min(body.topK, 20) : 5
  const history = body.history || []

  try {
    const url = new URL(req.url)
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"

    // Let the LLM handle ALL query interpretation - no hardcoded patterns
    let dbStats: DatabaseStats | null = null

    // Use the new LLM-powered search endpoint with increased timeout
    let searchResponse: Response
    try {
      searchResponse = await fetchWithTimeout(
        `${backendUrl}/api/llm-search?q=${encodeURIComponent(query)}`,
        {},
        45000 // 45 second timeout for LLM search
      )
    } catch (timeoutError) {
      // If LLM search times out, try falling back to regular search
      console.error("LLM search timed out, trying regular search:", timeoutError)
      searchResponse = await fetchWithTimeout(
        `${backendUrl}/api/search?q=${encodeURIComponent(query)}`,
        {},
        20000 // 20 second timeout for regular search
      )
    }

    if (!searchResponse.ok) {
      // Handle specific error codes
      if (searchResponse.status === 500) {
        console.error(`Backend error for query "${query}": ${searchResponse.status}`)
        // Try to get error details
        let errorDetails = ""
        try {
          const errorData = await searchResponse.json()
          errorDetails = errorData.detail || errorData.error || ""
        } catch {
          errorDetails = "Unknown backend error"
        }

        // Return a more informative error to the user
        return Response.json({
          query,
          answer: `I encountered an error processing your query. ${errorDetails ? `Details: ${errorDetails}` : 'Please try rephrasing your question or try again later.'}`,
          results: []
        })
      }

      throw new Error(`Search API error: ${searchResponse.status}`)
    }

    const searchData = (await searchResponse.json()) as SearchApiResponse
    const allResults = Array.isArray(searchData.results) ? searchData.results : []

    // Map the text field to content for frontend compatibility
    const mappedResults = allResults.map((result: any) => ({
      ...result,
      id: result.chunk_id || result.id || `chunk-${Math.random()}`,  // Map chunk_id to id
      content: result.text || result.content || result.description || "",
      description: result.text || result.description || "",
      source: result.file_name || result.source,
      image_url: result.page_image_relative ? `/api/image/${result.project_id}/${result.page_image_relative}` : result.image_url,
      metadata: result.metadata || {
        technology: result.technology,
        year: result.year,
        customer: result.customer,
        page: result.page,
        project_id: result.project_id,
        file_name: result.file_name
      }
    }))

    const selected = mappedResults.slice(0, topK)

    // Check if this is a count query result (NOT vector search results)
    const isCountResult = selected.length > 0 &&
      (selected[0].hasOwnProperty('project_count') ||
       selected[0].hasOwnProperty('total_projects') ||
       selected[0].hasOwnProperty('c.project_id'))  // Removed 'year' check as vector results also have year

    // For count queries, enhance the results with descriptive content
    if (isCountResult) {
      selected.forEach(item => {
        if (item.project_count !== undefined) {
          item.content = `Found ${item.project_count} project(s)${item.year ? ` in year ${item.year}` : ''}`
          item.description = item.content
          // Add metadata for proper display in right panel
          if (item.year) {
            item.metadata = {
              year: item.year,
              type: 'count_result'
            }
          }
        } else if (item['c.project_id']) {
          item.content = `Project: ${item['c.project_id']} - ${item['c.project_name'] || 'N/A'}`
          item.description = `Customer: ${item['c.customer'] || 'N/A'}, Year: ${item['c.year'] || 'N/A'}`
          // Add metadata for proper display
          item.metadata = {
            project_id: item['c.project_id'],
            project_name: item['c.project_name'],
            customer: item['c.customer'],
            year: item['c.year'],
            technology: item['c.technology']
          }
        }
      })
    }

    const relevanceThreshold = 0.2
    const hasUsefulChunks =
      selected.length > 0 &&
      (isCountResult || selected.some((r) => typeof r.relevance === "number" && r.relevance >= relevanceThreshold))

    let context = ""

    if (isCountResult) {
      // Handle count/list query results
      if (selected[0].hasOwnProperty('project_count')) {
        context = `Query Result:\n- Project Count: ${selected[0].project_count}`
        if (selected[0].hasOwnProperty('year')) {
          context = `Query Results by Year:\n${selected.map(r => `- ${r.year}: ${r.project_count} projects`).join('\n')}`
        }
      } else if (selected[0].hasOwnProperty('c.project_id')) {
        // List of projects
        context = `Project List (${selected.length} projects):\n${selected.map((r, i) =>
          `${i+1}. ${r['c.project_id']} - ${r['c.project_name']} (${r['c.customer']}, ${r['c.year']})`
        ).join('\n')}`
      }
    } else {
      // Handle regular search results

      // Check if this is a location query
      const locationPattern = /(germany|france|uk|united kingdom|netherlands|china|india|usa)/i
      const locationMatch = query.match(locationPattern)

      if (locationMatch) {
        const location = locationMatch[1].toUpperCase()

        // Extract unique project IDs and years for summary
        const projectsByYear = new Map<number, Set<string>>()
        selected.forEach(r => {
          if (r.project_id && r.year) {
            if (!projectsByYear.has(r.year)) {
              projectsByYear.set(r.year, new Set())
            }
            projectsByYear.get(r.year)?.add(r.project_id)
          }
        })

        context = `\n*** LOCATION QUERY RESULTS FOR: ${location} ***\n`
        context += `These chunks are ALL from ${location}-related projects (vector search already filtered for ${location}):\n`

        // Add summary of projects by year
        if (projectsByYear.size > 0) {
          context += `\nSUMMARY OF UNIQUE PROJECTS BY YEAR:\n`
          for (const [year, projects] of Array.from(projectsByYear).sort((a, b) => a[0] - b[0])) {
            context += `- ${year}: ${projects.size} project(s) - ${Array.from(projects).sort().join(', ')}\n`
          }
        }
        context += `\nDETAILED CHUNKS:\n\n`
      } else {
        context = ""
      }

      context += selected
        .map((r, index) => {
          const score = typeof r.relevance === "number" ? Math.round(r.relevance * 100) : null
          const header =
            score !== null
              ? `Chunk ${index + 1} (relevance: ${score}%)`
              : `Chunk ${index + 1}`

          // Include metadata for project counting - MAKE IT PROMINENT
          const projectInfo = r.project_id ? `\n[PROJECT: ${r.project_id}]` : ""
          const yearInfo = r.year ? ` [YEAR: ${r.year}]` : ""
          const customerInfo = r.customer ? ` [CUSTOMER: ${r.customer}]` : ""
          const techInfo = r.technology ? ` [TECHNOLOGY: ${r.technology}]` : ""

          const metadata = `${projectInfo}${yearInfo}${customerInfo}${techInfo}`

          const source = r.source ? `\nSource: ${r.source}` : ""
          const imageUrl = r.image_url ? `\nImage: ${r.image_url}` : ""
          return `${header}${metadata}\nContent: ${r.content || r.description || ""}${source}${imageUrl}`
        })
        .join("\n\n")
    }

    const ollamaUrl = process.env.OLLAMA_URL || "http://localhost:11434"
    // Use gpt-oss:20b - tested to work well with Germany counting
    const model = process.env.OLLAMA_MODEL || "gpt-oss:20b"

    // Debug: Log context length
    console.log(`Context for Ollama (${context.length} chars):`, context.substring(0, 500))

    const noContextDisclaimer =
      "Note: No relevant reference chunks were found in the database for this query. The following answer is based on general knowledge:"

    // Build conversation history context
    let conversationContext = ""
    if (history.length > 0) {
      const recentHistory = history.slice(-6) // Last 3 exchanges
      conversationContext = "Previous conversation:\n" +
        recentHistory.map(msg => `${msg.role === "user" ? "User" : "Assistant"}: ${msg.content}`).join("\n") +
        "\n\n"
    }

    // Build database stats context for aggregate queries
    let statsContext = ""
    if (dbStats) {
      statsContext = `Database Statistics:
- Total projects: ${dbStats.total_projects || "unknown"}
- HVDC projects: ${dbStats.hvdc_count || "unknown"}
- SynCon projects: ${dbStats.syncon_count || "unknown"}
${dbStats.hvdc_projects ? `- HVDC project list: ${dbStats.hvdc_projects.join(", ")}` : ""}
${dbStats.syncon_projects ? `- SynCon project list: ${dbStats.syncon_projects.join(", ")}` : ""}

`
    }

    let prompt: string

    if (hasUsefulChunks || dbStats) {
      const isDirectAnswer = isCountResult && context.includes("Query Result")
      prompt = `You are a helpful assistant answering questions using the provided reference chunks from a document database.

${conversationContext}${statsContext}User question:
${query}

${hasUsefulChunks ? `${isDirectAnswer ? 'Database Query Results' : 'Reference chunks (numbered)'}:
${context}

` : ""}Instructions for your answer:
${isDirectAnswer ?
`- The database has returned EXACT COUNT results above. Use these numbers directly.
- State the count clearly: "There are X [technology] projects in [year]" or similar.
- Do NOT say "no relevant chunks found" - the count IS the relevant data from the database.
- Be direct and specific with the numbers provided in the Query Result section above.
- If it shows 0 projects, explicitly state there are no projects for that criteria.` :
`IMPORTANT: For location queries (Germany, France, UK, etc.):
- The vector search has ALREADY filtered for location relevance
- ALL chunks shown below ARE from that location's projects - trust this completely!
- Simply count the unique project IDs that match the year

COUNTING INSTRUCTIONS:
- Each chunk has [PROJECT: GC22_XXX] [YEAR: 2022] format
- If you see [PROJECT: GC22_046] [YEAR: 2022], this IS a Germany project from 2022
- Count EVERY unique project ID, don't look for "Germany" in text - the search already did that
- Example answer: "Based on the provided chunks, there are 4 Germany projects from 2022: GC22_046, GC22_070, GC22_085, GC22_045"
- If chunks mention specific locations (Germany, UK, etc.), companies (TenneT, Amprion, etc.), or regions, extract and count the related project IDs.
- Prefer information from the chunks/stats over your general knowledge; do NOT contradict them.
- At the beginning of your answer, explicitly cite your sources (e.g., "Based on the provided chunks" or "Based on analysis of the documents").
- When counting projects, list the unique project IDs you found as evidence.
- If the answer is uncertain or not supported by either the data or your general knowledge, say so explicitly.`}
- For follow-up questions like "are you sure", refer to the previous conversation context.`
    } else {
      prompt = `You are a helpful assistant that must answer using your general knowledge because no relevant reference chunks were found in the database.

${conversationContext}User question:
${query}

Instructions for your answer:
- You do NOT have any useful database context for this query.
- Answer using your general knowledge instead.
- At the very beginning of your answer, include exactly this line:
"${noContextDisclaimer}"
- After that line, provide your best answer.
- Be explicit if you are uncertain or if information might be incomplete.
- For follow-up questions, refer to the previous conversation context.`
    }

    // Call Ollama with proper timeout
    const llmResponse = await fetchWithTimeout(
      `${ollamaUrl}/api/generate`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model,
          prompt,
          stream: false,
        })
      },
      60000 // 60 second timeout for LLM generation
    )

    if (!llmResponse.ok) {
      throw new Error(`Ollama error: ${llmResponse.status}`)
    }

    const llmData = (await llmResponse.json()) as { response?: string }
    let answer = (llmData.response || "").trim() || "No response was generated by the model."

    // Fallback counting logic for location queries
    const locationPattern = /(germany|france|uk|united kingdom|netherlands|china|india|usa)/i
    const yearPattern = /\b(20\d{2})\b/
    const locationMatch = query.match(locationPattern)
    const yearMatch = query.match(yearPattern)

    if (locationMatch && selected.length > 0) {
      // Check if Ollama incorrectly says "0 projects" or says it doesn't have chunks
      const noDataPattern = /(?:don't have|can't determine|no.*reference chunks|cannot.*count|0|zero|no)\s+(?:.*)?(?:projects|chunks)/i

      if (noDataPattern.test(answer)) {
        // Extract unique project IDs from results
        const uniqueProjects = new Set<string>()
        const targetYear = yearMatch ? parseInt(yearMatch[1]) : null

        selected.forEach(r => {
          if (r.project_id) {
            if (!targetYear || r.year === targetYear) {
              uniqueProjects.add(r.project_id)
            }
          }
        })

        if (uniqueProjects.size > 0) {
          const location = locationMatch[1]
          const yearText = targetYear ? ` from ${targetYear}` : ""
          const projectList = Array.from(uniqueProjects).sort().join(", ")

          // Prepend correct count to answer
          answer = `**Correction: Based on the search results, there are ${uniqueProjects.size} ${location} projects${yearText}: ${projectList}**\n\n${answer}`
        }
      }
    }

    if (!hasUsefulChunks && answer) {
      if (!answer.startsWith(noContextDisclaimer)) {
        answer = `${noContextDisclaimer}\n\n${answer}`
      }
    }

    const payload: ChatResponseBody = {
      query,
      answer,
      results: selected,
    }

    return Response.json(payload)
  } catch (error: any) {
    console.error("Error in /api/chat:", error)

    // Provide more specific error messages
    if (error.message?.includes('timeout')) {
      return Response.json(
        {
          query,
          answer: "The request took too long to complete. This might be because the system is processing a complex query. Please try again with a simpler question or wait a moment and retry.",
          results: []
        },
        { status: 200 } // Return 200 to show the message in the chat
      )
    }

    return Response.json(
      { error: "Failed to process chat request. Please try again later." },
      { status: 500 }
    )
  }
}
