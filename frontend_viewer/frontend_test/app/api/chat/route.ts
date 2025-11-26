export const dynamic = "force-dynamic"

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

    // Check if this is an aggregate question (how many, count, list projects)
    const isAggregateQuery = /how many|count|list.*projects?|total.*projects?/i.test(query)
    let dbStats: DatabaseStats | null = null

    if (isAggregateQuery) {
      try {
        const statsResponse = await fetch(`${backendUrl}/api/stats`)
        if (statsResponse.ok) {
          dbStats = await statsResponse.json()
        }
      } catch (e) {
        console.error("Failed to fetch stats:", e)
      }
    }

    // Fetch search results from backend with configurable top_k
    const searchResponse = await fetch(`${backendUrl}/api/search?q=${encodeURIComponent(query)}&top_k=${topK}`)

    if (!searchResponse.ok) {
      throw new Error(`Search API error: ${searchResponse.status}`)
    }

    const searchData = (await searchResponse.json()) as SearchApiResponse
    const allResults = Array.isArray(searchData.results) ? searchData.results : []
    const selected = allResults.slice(0, topK)

    const relevanceThreshold = 0.2
    const hasUsefulChunks =
      selected.length > 0 &&
      selected.some((r) => typeof r.relevance === "number" && r.relevance >= relevanceThreshold)

    const context = selected
      .map((r, index) => {
        const score = typeof r.relevance === "number" ? Math.round(r.relevance * 100) : null
        const header =
          score !== null
            ? `Chunk ${index + 1} (relevance: ${score}%)`
            : `Chunk ${index + 1}`
        const source = r.source ? `\nSource: ${r.source}` : ""
        return `${header}\n${r.content || r.description || ""}${source}`
      })
      .join("\n\n")

    const ollamaUrl = process.env.OLLAMA_URL || "http://localhost:11434"
    const model = process.env.OLLAMA_MODEL || "gpt-oss:20b"

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
      prompt = `You are a helpful assistant answering questions using the provided reference chunks from a document database.

${conversationContext}${statsContext}User question:
${query}

${hasUsefulChunks ? `Reference chunks (numbered):
${context}

` : ""}Instructions for your answer:
- Treat the reference chunks and database statistics as your primary source of truth.
- Prefer information from the chunks/stats over your general knowledge; do NOT contradict them.
- At the beginning of your answer, explicitly cite your sources (e.g., "Based on database statistics" or "Based on chunks 1 and 3").
- When you supplement with your general knowledge, clearly mark those parts as coming from "general knowledge".
- If the answer is uncertain or not supported by either the data or your general knowledge, say so explicitly.
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

    const llmResponse = await fetch(`${ollamaUrl}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        prompt,
        stream: false,
      }),
    })

    if (!llmResponse.ok) {
      throw new Error(`Ollama error: ${llmResponse.status}`)
    }

    const llmData = (await llmResponse.json()) as { response?: string }
    let answer = (llmData.response || "").trim() || "No response was generated by the model."

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
  } catch (error) {
    console.error("Error in /api/chat:", error)
    return Response.json(
      { error: "Failed to process chat request. Please try again later." },
      { status: 500 },
    )
  }
}

