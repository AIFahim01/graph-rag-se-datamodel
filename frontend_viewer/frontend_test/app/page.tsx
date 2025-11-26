import Link from "next/link"
import { MessageCircle, Search } from "lucide-react"

import { Button } from "@/components/ui/button"

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center px-4">
      <div className="max-w-3xl w-full space-y-10">
        <header className="text-center space-y-3">
          <p className="text-xs font-semibold text-blue-400 uppercase tracking-[0.25em]">
            GraphRAG Viewer
          </p>
          <h1 className="text-4xl md:text-5xl font-bold text-white">
            Choose how you want to explore your data
          </h1>
          <p className="text-slate-400 max-w-2xl mx-auto">
            Start with vector search to browse ranked chunks, or open chat for conversational
            exploration powered by your vector database and local LLM.
          </p>
        </header>

        <div className="grid gap-6 md:grid-cols-2">
          <Link href="/search" className="group">
            <div className="bg-slate-900/80 border border-slate-800 group-hover:border-blue-500/80 rounded-2xl p-6 md:p-7 shadow-lg shadow-slate-900/40 transition-all">
              <div className="flex items-center justify-between gap-4 mb-4">
                <div className="flex items-center gap-3">
                  <div className="inline-flex h-11 w-11 items-center justify-center rounded-full bg-blue-600/20 text-blue-400">
                    <Search className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-white">Vector Search</h2>
                    <p className="text-xs text-slate-400">Existing semantic search interface</p>
                  </div>
                </div>
              </div>
              <p className="text-sm text-slate-300 mb-4">
                Type a query and browse scored results from the vector database, with detailed views
                for each chunk.
              </p>
              <Button className="w-full justify-center bg-blue-600 hover:bg-blue-700 text-white">
                Open Vector Search
              </Button>
            </div>
          </Link>

          <Link href="/chat" className="group">
            <div className="bg-slate-900/80 border border-slate-800 group-hover:border-emerald-500/80 rounded-2xl p-6 md:p-7 shadow-lg shadow-slate-900/40 transition-all">
              <div className="flex items-center justify-between gap-4 mb-4">
                <div className="flex items-center gap-3">
                  <div className="inline-flex h-11 w-11 items-center justify-center rounded-full bg-emerald-600/20 text-emerald-400">
                    <MessageCircle className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-white">Open Chat</h2>
                    <p className="text-xs text-slate-400">Chat with your vector database</p>
                  </div>
                </div>
              </div>
              <p className="text-sm text-slate-300 mb-4">
                Ask questions in natural language. We run a vector search, send context to Ollama
                (gpt-oss:20b), and show answers with reference chunks.
              </p>
              <Button className="w-full justify-center bg-emerald-600 hover:bg-emerald-700 text-white">
                Start Chatting
              </Button>
            </div>
          </Link>
        </div>
      </div>
    </main>
  )
}
