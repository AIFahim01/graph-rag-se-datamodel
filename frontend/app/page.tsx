import Link from "next/link"
import { MessageCircle, Search, Sparkles, Database, Network, Zap } from "lucide-react"

import { Button } from "@/components/ui/button"

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center px-4">
      <div className="max-w-2xl w-full space-y-8">
        <header className="text-center space-y-3">
          <p className="text-xs font-semibold text-blue-400 uppercase tracking-[0.25em]">
            GC DATA GRID
          </p>
          <h1 className="text-4xl md:text-5xl font-bold text-white">
            Historical Search
          </h1>
          <p className="text-slate-400 max-w-xl mx-auto">
            Search your knowledge base using our unified 4-step AI pipeline:
            Metadata Filter, Graph Context, Vector Search, and LLM Answer Generation.
          </p>
        </header>

        {/* Pipeline Steps Visualization */}
        <div className="flex items-center justify-center gap-2 py-4">
          <div className="flex items-center gap-1 text-xs">
            <div className="h-8 w-8 rounded-full bg-green-600/20 flex items-center justify-center">
              <Database className="h-4 w-4 text-green-400" />
            </div>
            <span className="text-slate-500">Metadata</span>
          </div>
          <div className="w-6 h-0.5 bg-slate-700"></div>
          <div className="flex items-center gap-1 text-xs">
            <div className="h-8 w-8 rounded-full bg-purple-600/20 flex items-center justify-center">
              <Network className="h-4 w-4 text-purple-400" />
            </div>
            <span className="text-slate-500">Graph</span>
          </div>
          <div className="w-6 h-0.5 bg-slate-700"></div>
          <div className="flex items-center gap-1 text-xs">
            <div className="h-8 w-8 rounded-full bg-blue-600/20 flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-blue-400" />
            </div>
            <span className="text-slate-500">Vector</span>
          </div>
          <div className="w-6 h-0.5 bg-slate-700"></div>
          <div className="flex items-center gap-1 text-xs">
            <div className="h-8 w-8 rounded-full bg-amber-600/20 flex items-center justify-center">
              <Zap className="h-4 w-4 text-amber-400" />
            </div>
            <span className="text-slate-500">Answer</span>
          </div>
        </div>

        {/* Main Chat Entry */}
        <div className="mt-6">
          <Link href="/chat" className="group block">
            <div className="bg-slate-900/80 border border-slate-800 group-hover:border-emerald-500/80 rounded-2xl p-8 shadow-lg shadow-slate-900/40 transition-all">
              <div className="flex flex-col items-center gap-4 text-center">
                <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-emerald-600/20 text-emerald-400">
                  <MessageCircle className="h-8 w-8" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-white">Start Searching</h2>
                  <p className="text-sm text-slate-400 mt-2">
                    Ask questions in natural language. Our AI will search across metadata,
                    knowledge graph, and vector embeddings to find the best answers.
                  </p>
                </div>
                <Button className="bg-emerald-600 hover:bg-emerald-700 text-white px-8 py-2 text-lg">
                  Open Chat
                </Button>
              </div>
            </div>
          </Link>
        </div>

        {/* Secondary Options */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
          <Link href="/search" className="group block">
            <div className="bg-slate-900/50 border border-slate-800 group-hover:border-blue-500/50 rounded-xl p-4 shadow-lg transition-all h-full">
              <div className="flex items-center gap-3">
                <div className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-blue-600/20 text-blue-400">
                  <Search className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-white">Vector Search</h3>
                  <p className="text-xs text-slate-400">
                    Direct semantic search
                  </p>
                </div>
              </div>
            </div>
          </Link>

          <Link href="/graph" className="group block">
            <div className="bg-slate-900/50 border border-slate-800 group-hover:border-purple-500/50 rounded-xl p-4 shadow-lg transition-all h-full">
              <div className="flex items-center gap-3">
                <div className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-purple-600/20 text-purple-400">
                  <Network className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-white">Graph Explorer</h3>
                  <p className="text-xs text-slate-400">
                    Visualize knowledge graph
                  </p>
                </div>
              </div>
            </div>
          </Link>
        </div>
      </div>
    </main>
  )
}
