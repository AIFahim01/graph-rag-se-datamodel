"use client"

import Link from "next/link"
import { ChevronRight } from "lucide-react"

interface Result {
  id: string
  title: string
  description: string
  category: string
  relevance: number
}

interface ResultsListProps {
  results: Result[]
}

export function ResultsList({ results }: ResultsListProps) {
  if (results.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400 text-lg">No results found. Try a different search.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {results.map((result) => (
        <Link key={result.id} href={`/result/${result.id}`} className="block group">
          <div className="bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-blue-500 rounded-lg p-6 transition-all duration-300 cursor-pointer">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <span className="inline-block px-2 py-1 text-xs font-semibold text-blue-400 bg-blue-500/10 rounded">
                    {result.category}
                  </span>
                  <span className="text-sm text-slate-500">{Math.round(result.relevance * 100)}% match</span>
                </div>
                <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition line-clamp-2">
                  {result.title}
                </h3>
                <p className="text-slate-400 text-sm mt-2 line-clamp-2">{result.description}</p>
              </div>
              <ChevronRight className="w-5 h-5 text-slate-500 group-hover:text-blue-400 transition flex-shrink-0 mt-1" />
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
}
