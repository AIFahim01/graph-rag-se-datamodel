"use client"

import { useParams, useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Loader, Copy, Check } from "lucide-react"

interface ResultDetail {
  id: string
  title: string
  description: string
  category: string
  content: string
  relevance: number
  metadata: Record<string, unknown>
  tags: string[]
  source?: string
  createdAt?: string
  image_url?: string
  page_image_relative?: string
  project_id?: string
}

export default function ResultDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string
  const [result, setResult] = useState<ResultDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const loadResult = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // First try to retrieve from sessionStorage
        const storedResults = sessionStorage.getItem("searchResults")

        if (storedResults) {
          const results: ResultDetail[] = JSON.parse(storedResults)
          // Try both exact match and decoded match
          const decodedId = decodeURIComponent(id)
          const foundResult = results.find((r) =>
            r.id === id || r.id === decodedId ||
            encodeURIComponent(r.id) === id
          )

          if (foundResult) {
            setResult(foundResult)
            setIsLoading(false)
            return
          }
        }

        // If not found in session storage, fetch from API
        const lastQuery = sessionStorage.getItem("lastQuery") || id
        const response = await fetch(`/api/search?q=${encodeURIComponent(lastQuery)}`)

        if (!response.ok) {
          throw new Error("Failed to fetch results from API")
        }

        const data = await response.json()
        if (data.results && Array.isArray(data.results)) {
          const decodedId = decodeURIComponent(id)
          const apiResult = data.results.find((r: ResultDetail) =>
            r.id === id || r.id === decodedId ||
            encodeURIComponent(r.id) === id
          )

          if (apiResult) {
            setResult(apiResult)
            // Store the fresh results
            sessionStorage.setItem("searchResults", JSON.stringify(data.results))
          } else {
            throw new Error("Result not found. The document may have been removed or the ID is incorrect.")
          }
        } else {
          throw new Error("No results found.")
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred")
      } finally {
        setIsLoading(false)
      }
    }

    loadResult()
  }, [id])

  const handleCopy = async () => {
    if (result) {
      await navigator.clipboard.writeText(result.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleBack = () => {
    const lastQuery = sessionStorage.getItem("lastQuery")
    const currentPage = sessionStorage.getItem("currentPage")
    const lastSearchType = sessionStorage.getItem("lastSearchType") || "vector"

    if (lastQuery) {
      // Navigate back to results page with the same query, page, and search type
      const url = `/results?q=${encodeURIComponent(lastQuery)}&type=${lastSearchType}${currentPage ? `&page=${currentPage}` : ""}`
      router.push(url)
    } else {
      // Fallback to home if no query found
      router.push("/")
    }
  }

  const imageUrl = result?.image_url ||
    (result?.page_image_relative && result?.project_id
      ? `/api/image/${result.project_id}/${result.page_image_relative}`
      : undefined)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-slate-900/50 backdrop-blur border-b border-slate-700">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleBack}
            className="text-slate-400 hover:text-white"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Results
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <div className="flex flex-col items-center gap-3">
              <Loader className="w-8 h-8 text-blue-400 animate-spin" />
              <p className="text-slate-400">Loading details...</p>
            </div>
          </div>
        )}

        {error && <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 text-red-400">{error}</div>}

        {!isLoading && result && (
          <div className="space-y-8">
            {/* Title Section */}
            <div>
              <div className="flex items-center gap-3 mb-4">
                <span className="inline-block px-3 py-1 text-sm font-semibold text-blue-400 bg-blue-500/10 rounded-full">
                  {result.category}
                </span>
                <span className="text-sm text-slate-500">{Math.round(result.relevance * 100)}% Relevance Match</span>
              </div>
              <h1 className="text-4xl font-bold text-white mb-4">{result.title}</h1>
              <p className="text-xl text-slate-400">{result.description}</p>
            </div>

            {/* Image Section */}
            {imageUrl && (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h2 className="text-lg font-semibold text-white mb-4">Document Image</h2>
                <div className="rounded overflow-hidden border border-slate-700">
                  <img
                    src={`http://localhost:8001${imageUrl}`}
                    alt={`Page from ${result.source || 'document'}`}
                    className="w-full h-auto"
                    loading="lazy"
                  />
                </div>
              </div>
            )}

            {/* Content Section */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-white">Content</h2>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm"
                >
                  {copied ? (
                    <>
                      <Check className="w-4 h-4" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      Copy
                    </>
                  )}
                </button>
              </div>
              <div className="prose prose-invert max-w-none">
                <p className="text-slate-300 whitespace-pre-wrap leading-relaxed">{result.content}</p>
              </div>
            </div>

            {/* Tags Section */}
            {result.tags && result.tags.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold text-white mb-4">Tags</h2>
                <div className="flex flex-wrap gap-2">
                  {result.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-full text-sm transition cursor-pointer"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Metadata Section */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-8">
              <h2 className="text-lg font-semibold text-white mb-6">Metadata</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {result.source && (
                  <div>
                    <p className="text-sm text-slate-500 uppercase tracking-wide mb-2">Source</p>
                    <p className="text-slate-200">{result.source}</p>
                  </div>
                )}
                {result.createdAt && (
                  <div>
                    <p className="text-sm text-slate-500 uppercase tracking-wide mb-2">Created At</p>
                    <p className="text-slate-200">
                      {new Date(result.createdAt).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })}
                    </p>
                  </div>
                )}
                {Object.entries(result.metadata).map(([key, value]) => (
                  <div key={key}>
                    <p className="text-sm text-slate-500 uppercase tracking-wide mb-2">{key.replace(/_/g, ' ')}</p>
                    <p className="text-slate-200">{String(value)}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}