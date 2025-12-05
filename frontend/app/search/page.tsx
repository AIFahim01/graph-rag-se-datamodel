import { Suspense } from "react"
import { SearchInterface } from "@/components/search-interface"

function SearchLoading() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
      <div className="text-white">Loading...</div>
    </div>
  )
}

export default function SearchPage() {
  return (
    <Suspense fallback={<SearchLoading />}>
      <SearchInterface />
    </Suspense>
  )
}
