"use client"

import { useEffect, useRef, useState } from "react"
import { Home, Link2, Loader2, MessageCircle, PanelRightClose, PanelRightOpen, Send } from "lucide-react"
import { useRouter } from "next/navigation"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { defaultChatHistoryStore, type ChatMessage } from "@/lib/chat-history"

interface ReferenceChunk {
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

interface ChatApiResponse {
  query: string
  answer: string
  results: ReferenceChunk[]
  error?: string
}

const CONVERSATION_ID = "default"

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [referenceChunks, setReferenceChunks] = useState<ReferenceChunk[]>([])
  const [showReferences, setShowReferences] = useState(true)
  const [selectedMessageKey, setSelectedMessageKey] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement | null>(null)
  const referencePanelRef = useRef<HTMLDivElement | null>(null)
  const router = useRouter()

  useEffect(() => {
    let active = true
    ;(async () => {
      const history = await defaultChatHistoryStore.getHistory(CONVERSATION_ID)
      if (active && history.length > 0) {
        setMessages(history)
      }
    })()
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages.length])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const query = input.trim()
    if (!query || isLoading) return

    setError(null)
    setIsLoading(true)

    const timestamp = new Date().toISOString()

    const userMessage: ChatMessage = {
      id: "",
      role: "user",
      content: query,
      createdAt: timestamp,
      query,
    }

    const assistantMessage: ChatMessage = {
      id: "",
      role: "assistant",
      content: "",
      createdAt: timestamp,
      query,
    }

    setMessages((prev) => [...prev, userMessage, assistantMessage])
    setInput("")

    try {
      await defaultChatHistoryStore.saveMessage(CONVERSATION_ID, userMessage)

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || "Chat API request failed")
      }

      const data = (await res.json()) as ChatApiResponse
      if (data.error) {
        throw new Error(data.error)
      }

      setReferenceChunks(data.results || [])

      const answerMessage: ChatMessage = {
        ...assistantMessage,
        content: data.answer,
        chunks: data.results || [],
      }

      setMessages((prev) => {
        const next = [...prev]
        const index = next.findIndex((m) => m === assistantMessage)
        if (index !== -1) {
          next[index] = { ...answerMessage }
        } else {
          next.push(answerMessage)
        }
        return next
      })

      await defaultChatHistoryStore.saveMessage(CONVERSATION_ID, answerMessage)
    } catch (err) {
      console.error("Chat error:", err)
      setError(err instanceof Error ? err.message : "An unexpected error occurred.")
      setMessages((prev) => prev.filter((m) => m !== assistantMessage))
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearHistory = async () => {
    setMessages([])
    setReferenceChunks([])
    setError(null)
    setSelectedMessageKey(null)
    await defaultChatHistoryStore.clearHistory(CONVERSATION_ID)
  }

  const getMessageKey = (message: ChatMessage) => message.id || message.createdAt

  const handleSelectAssistantMessage = (message: ChatMessage) => {
    if (message.role !== "assistant") return

    const key = getMessageKey(message)
    const maybeChunks = (message as any).chunks
    const hasRefs = Array.isArray(maybeChunks) && maybeChunks.length > 0

    setSelectedMessageKey((current) => (current === key ? null : key))
    if (hasRefs) {
      setShowReferences(true)
    }

    if (typeof window !== "undefined" && window.innerWidth < 768 && hasRefs) {
      setTimeout(() => {
        if (referencePanelRef.current) {
          referencePanelRef.current.scrollIntoView({ behavior: "smooth" })
        }
      }, 50)
    }
  }

  const selectedMessage =
    selectedMessageKey != null
      ? messages.find((m) => m.role === "assistant" && getMessageKey(m) === selectedMessageKey)
      : null

  const selectedChunks = (selectedMessage?.chunks as ReferenceChunk[] | undefined) ?? []
  const panelChunks = selectedMessage ? selectedChunks : referenceChunks
  const isShowingSelected = !!selectedMessage

  const selectedQuerySource = selectedMessage?.query || selectedMessage?.content || ""
  const truncatedQuery =
    selectedQuerySource.length > 80
      ? `${selectedQuerySource.slice(0, 80)}…`
      : selectedQuerySource

  return (
    <div className="h-screen bg-slate-950 text-slate-50 flex flex-col overflow-hidden">
      <header className="border-b border-slate-800 px-4 py-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-emerald-600/20 text-emerald-400">
            <MessageCircle className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white">Open Chat</h1>
            <p className="text-xs text-slate-400">
              Vector search + Ollama (gpt-oss:20b) with reference chunks on the right.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push("/")}
            className="border-slate-700 text-slate-200"
          >
            <Home className="h-4 w-4 mr-1" />
            <span className="hidden md:inline">Home</span>
            <span className="md:hidden">Back</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowReferences((prev) => !prev)}
            className="border-slate-700 text-slate-200"
          >
            {showReferences ? (
              <PanelRightClose className="h-4 w-4 mr-1" />
            ) : (
              <PanelRightOpen className="h-4 w-4 mr-1" />
            )}
            <span className="hidden md:inline">References</span>
            <span className="md:hidden">Refs</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleClearHistory}
            className="border-slate-700"
          >
            Clear
          </Button>
        </div>
      </header>

      <main className="flex-1 flex flex-col md:flex-row overflow-hidden">
        <section className="flex-1 flex flex-col px-4 py-4 gap-4 overflow-hidden">
          <div className="flex-1 rounded-lg border border-slate-800 bg-slate-900/60 p-4 overflow-y-auto">
            {messages.length === 0 ? (
              <div className="h-full flex items-center justify-center text-sm text-slate-400 text-center">
                <p>
                  Ask a question about your data to get started. We&apos;ll search the vector
                  database and generate an answer with citations.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) => {
                  const key = getMessageKey(message)
                  const isAssistant = message.role === "assistant"
                  const isSelected = isAssistant && selectedMessageKey === key
                  const hasRefs =
                    isAssistant &&
                    Array.isArray((message as any).chunks) &&
                    (message as any).chunks.length > 0

                  return (
                    <div
                      key={key}
                      className={cn(
                        "flex",
                        isAssistant ? "justify-start" : "justify-end",
                        isAssistant && "cursor-pointer",
                      )}
                      onClick={() => isAssistant && handleSelectAssistantMessage(message)}
                    >
                      <div
                        className={cn(
                          "max-w-[80%] rounded-2xl px-3 py-2 text-[13px] leading-relaxed",
                          isAssistant
                            ? "bg-slate-800 text-slate-100 border border-slate-700 hover:bg-slate-900/70 transition-colors"
                            : "bg-blue-600 text-white",
                          isSelected && "ring-1 ring-emerald-400/70",
                        )}
                      >
                        <div className="space-y-1">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              h1: ({ node, ...props }) => (
                                <h1
                                  className="text-[15px] font-semibold text-slate-50 mt-1 mb-1"
                                  {...props}
                                />
                              ),
                              h2: ({ node, ...props }) => (
                                <h2
                                  className="text-[14px] font-semibold text-slate-50 mt-1 mb-1"
                                  {...props}
                                />
                              ),
                              h3: ({ node, ...props }) => (
                                <h3
                                  className="text-[13px] font-semibold text-slate-50 mt-1 mb-1"
                                  {...props}
                                />
                              ),
                              p: ({ node, ...props }) => (
                                <p className="mb-1 last:mb-0 text-[13px] text-slate-100" {...props} />
                              ),
                              strong: ({ node, ...props }) => (
                                <strong className="font-semibold text-slate-50" {...props} />
                              ),
                              em: ({ node, ...props }) => <em className="italic" {...props} />,
                              a: ({ node, ...props }) => (
                                <a
                                  className="text-emerald-400 hover:text-emerald-300 underline underline-offset-2"
                                  target="_blank"
                                  rel="noreferrer"
                                  {...props}
                                />
                              ),
                              ul: ({ node, ...props }) => (
                                <ul className="list-disc pl-4 mb-1 space-y-1" {...props} />
                              ),
                              ol: ({ node, ...props }) => (
                                <ol className="list-decimal pl-4 mb-1 space-y-1" {...props} />
                              ),
                              li: ({ node, ...props }) => <li className="text-[13px]" {...props} />,
                              blockquote: ({ node, ...props }) => (
                                <blockquote
                                  className="border-l-2 border-slate-600 pl-2 ml-1 text-[12px] text-slate-300 italic"
                                  {...props}
                                />
                              ),
                              code: ({ node, inline, className, children, ...props }: any) => {
                                if (!inline) {
                                  return (
                                    <pre className="mt-2 mb-2 rounded-md bg-slate-950/80 border border-slate-800 px-3 py-2 text-[11px] overflow-x-auto">
                                      <code
                                        className={cn("font-mono text-emerald-200", className)}
                                        {...props}
                                      >
                                        {children}
                                      </code>
                                    </pre>
                                  )
                                }
                                return (
                                  <code
                                    className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700"
                                    {...props}
                                  >
                                    {children}
                                  </code>
                                )
                              },
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>

                        {hasRefs && (
                          <div className="mt-1 flex items-center gap-1 text-[10px] text-emerald-400">
                            <Link2 className="h-3 w-3" />
                            <span>References available</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
                <div ref={bottomRef} />
              </div>
            )}
          </div>

          {error && (
            <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/40 rounded-md px-3 py-2">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex items-center gap-3">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your documents..."
              disabled={isLoading}
              className="bg-slate-900 border-slate-800 text-sm"
            />
            <Button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Thinking...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" /> Send
                </>
              )}
            </Button>
          </form>
        </section>

        {showReferences && (
          <aside
            ref={referencePanelRef}
            className="w-full md:w-96 flex flex-col flex-1 md:flex-none border-t md:border-t-0 md:border-l border-slate-800 bg-slate-950/60 px-4 py-4 overflow-hidden"
          >
            <div className="flex items-start justify-between mb-2 gap-2">
              <div>
                <h2 className="text-xs font-semibold text-slate-300">
                  {isShowingSelected ? "References for this answer" : "Reference chunks (latest)"}
                </h2>
                <p className="text-[11px] text-slate-500">
                  {isShowingSelected
                    ? truncatedQuery
                      ? `“${truncatedQuery}”`
                      : "Selected assistant message"
                    : "Updated on each question from the vector search backend. Higher scores indicate closer semantic matches."}
                </p>
              </div>
              {isShowingSelected && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedMessageKey(null)}
                  className="border-slate-700 text-[11px] h-6 px-2"
                >
                  Show latest
                </Button>
              )}
            </div>
            <div className="flex-1 pr-2 overflow-y-auto">
              {panelChunks.length === 0 ? (
                <p className="text-xs text-slate-500">
                  {isShowingSelected
                    ? "No reference chunks were recorded for this message."
                    : "No reference chunks yet. Ask a question to see the most relevant passages."}
                </p>
              ) : (
                <div className="space-y-3">
                  {panelChunks.map((chunk, index) => (
                    <div
                      key={chunk.id ?? index}
                      className="rounded-lg border border-slate-800 bg-slate-900/70 p-3 text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[11px] font-semibold text-slate-300">
                          Chunk {index + 1}
                        </span>
                        {typeof chunk.relevance === "number" && (
                          <span className="text-[11px] text-slate-400">
                            {Math.round(chunk.relevance * 100)}% match
                          </span>
                        )}
                      </div>
                      {chunk.title && (
                        <p className="text-[11px] text-blue-300 font-medium line-clamp-1">
                          {chunk.title}
                        </p>
                      )}
                      <p className="text-[11px] text-slate-300 line-clamp-4">
                        {chunk.content || chunk.description}
                      </p>
                      <div className="flex items-center justify-between mt-1 text-[10px] text-slate-500">
                        {chunk.category && <span>{chunk.category}</span>}
                        {chunk.source && (
                          <span className="truncate">Source: {chunk.source}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </aside>
        )}
      </main>
    </div>
  )
}

