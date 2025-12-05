"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Search, Sparkles, Home } from "lucide-react"
import Link from "next/link"

export function SearchInterface() {
  const [query, setQuery] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()
  const inputRef = useRef<HTMLInputElement>(null)

  // Handle autofocus on client-side only to avoid hydration mismatch
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }, [])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsLoading(true)
    router.push(`/results?q=${encodeURIComponent(query)}&type=vector`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Sparkles className="w-8 h-8 text-blue-400" />
            <h1 className="text-4xl md:text-5xl font-bold text-white">Vector Search</h1>
          </div>
          <p className="text-lg text-slate-400">Semantic similarity search using embeddings</p>
        </div>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="relative group">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg blur opacity-75 group-hover:opacity-100 transition duration-300 -z-10"></div>
            <div className="relative bg-slate-900 rounded-lg p-1">
              <div className="flex items-center gap-3 px-4 py-3 bg-slate-900 rounded-lg border border-slate-700">
                <Search className="w-5 h-5 text-slate-500" />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search documents semantically..."
                  className="flex-1 bg-transparent text-white placeholder-slate-500 outline-none text-lg"
                  suppressHydrationWarning
                />
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <Link href="/" className="flex items-center gap-2 px-4 py-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition">
              <Home className="w-4 h-4" />
              <span>Home</span>
            </Link>
            <Button
              type="submit"
              disabled={!query.trim() || isLoading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition"
            >
              {isLoading ? "Searching..." : "Search"}
            </Button>
          </div>
        </form>

        {/* Example Queries */}
        <div className="mt-12 pt-12 border-t border-slate-700">
          <p className="text-sm text-slate-400 mb-4">Try searching for:</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              "HVDC transmission systems",
              "SynCon projects",
              "Grid forming converters",
              "Wind power integration",
            ].map((example) => (
              <button
                key={example}
                onClick={() => setQuery(example)}
                className="text-left px-4 py-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition text-sm border border-slate-700"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
