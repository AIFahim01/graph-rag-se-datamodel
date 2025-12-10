"use client"

import { useSearchParams, useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import type React from "react"
import { ResultsList } from "@/components/results-list"
import { Button } from "@/components/ui/button"
import { Loader, Search, ChevronLeft, ChevronRight, Sparkles, Database, Network, Zap } from "lucide-react"

interface SearchResult {
  id: string
  title: string
  description: string
  category: string
  relevance: number
  content: string
  tags: string[]
  metadata: Record<string, unknown>
  source?: string
  createdAt?: string
}

type SearchType = "vector" | "metadata" | "graph" | "multi-judge"

const SEARCH_TYPE_CONFIG: Record<SearchType, { label: string; icon: React.ReactNode; color: string }> = {
  "vector": { label: "Vector Search", icon: <Sparkles className="w-4 h-4" />, color: "text-blue-400" },
  "metadata": { label: "Metadata Search", icon: <Database className="w-4 h-4" />, color: "text-green-400" },
  "graph": { label: "Graph Search", icon: <Network className="w-4 h-4" />, color: "text-purple-400" },
  "multi-judge": { label: "Multi-Judge (AI)", icon: <Zap className="w-4 h-4" />, color: "text-amber-400" },
}

const RESULTS_PER_PAGE = 10

export default function ResultsPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const query = searchParams.get("q") || ""
  const searchType = (searchParams.get("type") as SearchType) || "vector"
  const pageParam = searchParams.get("page")

  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [searchInput, setSearchInput] = useState(query)
  const [extraData, setExtraData] = useState<Record<string, any>>({})

  // Restore page number from URL or sessionStorage
  useEffect(() => {
    if (pageParam) {
      setCurrentPage(parseInt(pageParam, 10))
    } else {
      const savedPage = sessionStorage.getItem("currentPage")
      if (savedPage) {
        setCurrentPage(parseInt(savedPage, 10))
      }
    }
  }, [pageParam])

  useEffect(() => {
    if (!query) return

    const fetchResults = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&type=${searchType}`)

        if (!response.ok) {
          throw new Error("Failed to fetch results")
        }

        const data = await response.json()
        setResults(data.results)
        setExtraData({
          super_judge_summary: data.super_judge_summary,
          judge_stats: data.judge_stats,
          graph_stats: data.graph_stats
        })

        // Store complete results in sessionStorage for details page to access
        sessionStorage.setItem("searchResults", JSON.stringify(data.results))
        sessionStorage.setItem("lastQuery", query)
        sessionStorage.setItem("lastSearchType", searchType)
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred")
        setResults([])
      } finally {
        setIsLoading(false)
      }
    }

    fetchResults()
    setSearchInput(query)
  }, [query, searchType])

  // Calculate pagination
  const totalPages = Math.ceil(results.length / RESULTS_PER_PAGE)
  const startIndex = (currentPage - 1) * RESULTS_PER_PAGE
  const endIndex = startIndex + RESULTS_PER_PAGE
  const paginatedResults = results.slice(startIndex, endIndex)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchInput.trim()) return

    setCurrentPage(1)
    sessionStorage.setItem("currentPage", "1")
    router.push(`/results?q=${encodeURIComponent(searchInput)}&type=${searchType}`)
  }

  const currentConfig = SEARCH_TYPE_CONFIG[searchType]

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    sessionStorage.setItem("currentPage", page.toString())
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Fixed Search Header - Google-like */}
      <div className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur-lg border-b border-slate-700/50 shadow-lg">
        <div className="max-w-6xl mx-auto px-4 py-3">
          <div className="flex items-center gap-4">
            {/* Logo/Home Link - preserves search type */}
            <a
              href={`/search?type=${searchType}`}
              className="text-xl font-bold text-blue-400 hover:text-blue-300 transition flex-shrink-0"
            >
              GC Data Grid
            </a>

            {/* Search Type Badge */}
            <div className={`flex items-center gap-1 px-2 py-1 rounded-full bg-slate-800 border border-slate-700 ${currentConfig.color}`}>
              {currentConfig.icon}
              <span className="text-xs font-medium">{currentConfig.label}</span>
            </div>

            {/* Search Bar */}
            <form onSubmit={handleSearch} className="flex-1 max-w-2xl">
              <div className="relative">
                <div className="flex items-center gap-2 px-4 py-2 bg-slate-800 rounded-full border border-slate-700 hover:border-slate-600 focus-within:border-blue-500 transition">
                  <Search className="w-4 h-4 text-slate-500 flex-shrink-0" />
                  <input
                    type="text"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    placeholder="Search..."
                    className="flex-1 bg-transparent text-white placeholder-slate-500 outline-none text-sm"
                    suppressHydrationWarning
                  />
                  {searchInput !== query && (
                    <Button
                      type="submit"
                      size="sm"
                      className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1 h-7 rounded-full"
                    >
                      Search
                    </Button>
                  )}
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Results Info */}
        <div className="mb-6">
          <p className="text-sm text-slate-400">
            {isLoading
              ? "Searching..."
              : `About ${results.length} results for "${query}"${totalPages > 1 ? ` (Page ${currentPage} of ${totalPages})` : ""}`}
          </p>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <div className="flex flex-col items-center gap-3">
              <Loader className={`w-8 h-8 animate-spin ${currentConfig.color}`} />
              <p className="text-slate-400">
                {searchType === "multi-judge" ? "Running 4-Judge analysis..." :
                 searchType === "graph" ? "Searching knowledge graph..." :
                 searchType === "metadata" ? "Extracting metadata filters..." :
                 "Searching vector database..."}
              </p>
            </div>
          </div>
        )}

        {error && <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 text-red-400">{error}</div>}

        {!isLoading && !error && (
          <>
            {/* Super Judge Summary for Multi-Judge */}
            {searchType === "multi-judge" && extraData.super_judge_summary && (
              <div className="mb-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-5 h-5 text-amber-400" />
                  <h3 className="font-semibold text-amber-400">Super Judge Summary</h3>
                </div>
                <p className="text-slate-300 text-sm">{extraData.super_judge_summary}</p>
              </div>
            )}

            {/* Graph Stats for Graph Search */}
            {searchType === "graph" && extraData.graph_stats && (
              <div className="mb-6 p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Network className="w-5 h-5 text-purple-400" />
                  <h3 className="font-semibold text-purple-400">Knowledge Graph Stats</h3>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-slate-400">Entities:</span>
                    <span className="ml-2 text-white">{extraData.graph_stats.entity_count?.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Relationships:</span>
                    <span className="ml-2 text-white">{extraData.graph_stats.relationship_count?.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            )}

            <ResultsList results={paginatedResults} />

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-8 flex items-center justify-center gap-2">
                {/* Previous Button */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="text-slate-300 border-slate-700 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" />
                  Previous
                </Button>

                {/* Page Numbers */}
                <div className="flex items-center gap-1">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                    // Show first page, last page, current page, and pages around current
                    const showPage =
                      page === 1 ||
                      page === totalPages ||
                      (page >= currentPage - 1 && page <= currentPage + 1)

                    // Show ellipsis
                    const showEllipsisBefore = page === currentPage - 2 && currentPage > 3
                    const showEllipsisAfter = page === currentPage + 2 && currentPage < totalPages - 2

                    if (showEllipsisBefore || showEllipsisAfter) {
                      return (
                        <span key={page} className="px-2 text-slate-500">
                          ...
                        </span>
                      )
                    }

                    if (!showPage) return null

                    return (
                      <Button
                        key={page}
                        variant={currentPage === page ? "default" : "outline"}
                        size="sm"
                        onClick={() => handlePageChange(page)}
                        className={
                          currentPage === page
                            ? "bg-blue-600 hover:bg-blue-700 text-white min-w-[2.5rem]"
                            : "text-slate-300 border-slate-700 hover:bg-slate-800 min-w-[2.5rem]"
                        }
                      >
                        {page}
                      </Button>
                    )
                  })}
                </div>

                {/* Next Button */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="text-slate-300 border-slate-700 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
