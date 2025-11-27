"use client"

import { useParams, useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Loader, Copy, Check, ChevronDown, ChevronUp } from "lucide-react"

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
}

export default function ResultDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string
  const [result, setResult] = useState<ResultDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [showPictures, setShowPictures] = useState(true)  // Auto-expand pictures

  useEffect(() => {
    const loadResult = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Try sessionStorage first (stored by results page)
        const storedResults = sessionStorage.getItem("searchResults")

        if (storedResults) {
          const results: ResultDetail[] = JSON.parse(storedResults)
          const foundResult = results.find((r) => r.id === id)

          if (foundResult) {
            setResult(foundResult)
            setIsLoading(false)
            return
          }
        }

        // If not in sessionStorage, fetch from backend via Next.js API route
        // id is already URL-encoded from the route params, don't encode again
        const response = await fetch(`/api/result/${id}`)

        if (!response.ok) {
          throw new Error("Failed to fetch result from backend")
        }

        const data = await response.json()

        if (data.error) {
          throw new Error(data.error)
        }

        setResult(data)
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

    if (lastQuery) {
      // Navigate back to results page with the same query and page
      const url = `/results?q=${encodeURIComponent(lastQuery)}${currentPage ? `&page=${currentPage}` : ""}`
      router.push(url)
    } else {
      // Fallback to home if no query found
      router.push("/")
    }
  }

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

            {/* Page Image Section */}
            {result.metadata?.page_image_url && (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <h2 className="text-xl font-semibold text-white mb-4">
                  Page {result.metadata?.page || '?'}
                  {result.metadata?.total_pages && ` of ${result.metadata.total_pages}`}
                </h2>
                <div className="bg-slate-950 rounded border border-slate-700 overflow-hidden">
                  <img
                    src={`http://localhost:8001${result.metadata.page_image_url}`}
                    alt={`Page ${result.metadata?.page}`}
                    className="w-full h-auto object-contain"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = '/placeholder-image.png'
                    }}
                  />
                </div>
                <div className="mt-3 flex items-center gap-4 text-sm text-slate-400">
                  {typeof result.metadata?.total_images === 'number' && result.metadata.total_images > 0 && (
                    <span>🖼️ {result.metadata.total_images} images in document</span>
                  )}
                  {typeof result.metadata?.total_tables === 'number' && result.metadata.total_tables > 0 && (
                    <span>📊 {result.metadata.total_tables} tables in document</span>
                  )}
                </div>
              </div>
            )}

            {/* Extracted Pictures Gallery */}
            {result.metadata?.pictures && result.metadata.pictures.length > 0 && (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <button
                  onClick={() => setShowPictures(!showPictures)}
                  className="w-full flex items-center justify-between text-white hover:text-emerald-400 transition"
                >
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    🖼️ Pictures from this document ({result.metadata.pictures.length})
                  </h2>
                  {showPictures ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </button>

                {showPictures && (
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                    {result.metadata.pictures.map((picture: any) => (
                      <div key={picture.number} className="bg-slate-950 rounded border border-slate-700 overflow-hidden hover:border-emerald-500 transition">
                        <div
                          className="cursor-pointer"
                          onClick={() => window.open(`http://localhost:8001${picture.url}`, '_blank')}
                        >
                          <img
                            src={`http://localhost:8001${picture.url}`}
                            alt={`Picture ${picture.number}`}
                            className="w-full h-auto object-contain"
                          />
                        </div>
                        <div className="p-3 space-y-1">
                          <p className="text-xs font-semibold text-emerald-400">
                            Picture {picture.number}
                          </p>
                          {picture.description && (
                            <p className="text-xs text-slate-400 line-clamp-3">
                              {picture.description}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
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
                    <p className="text-sm text-slate-500 uppercase tracking-wide mb-2">{key}</p>
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
