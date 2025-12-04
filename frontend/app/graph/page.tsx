"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import dynamic from "next/dynamic"
import Link from "next/link"
import { Home, Search, Network, RefreshCw, ZoomIn, ZoomOut } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

// Dynamically import ForceGraph2D to avoid SSR issues
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="text-slate-400">Loading graph...</div>
    </div>
  ),
})

interface GraphNode {
  id: string
  name: string
  group: string
  size: number
  x?: number
  y?: number
}

interface GraphLink {
  source: string | GraphNode
  target: string | GraphNode
}

interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
  stats?: {
    node_count: number
    link_count: number
  }
}

interface GraphStats {
  entities: number
  relationships: number
  top_entities: Array<{ name: string; connections: number }>
}

const GROUP_COLORS: Record<string, string> = {
  center: "#10b981",  // emerald
  hub: "#8b5cf6",     // purple
  match: "#3b82f6",   // blue
  neighbor: "#6b7280", // gray
}

export default function GraphPage() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] })
  const [stats, setStats] = useState<GraphStats | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedEntity, setSelectedEntity] = useState("")
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
  const graphRef = useRef<any>(null)

  // Fetch graph stats on mount
  useEffect(() => {
    fetch("http://localhost:8001/api/graph-stats")
      .then((res) => res.json())
      .then((data) => setStats(data))
      .catch(console.error)

    // Load default graph
    loadGraph()
  }, [])

  const loadGraph = useCallback(async (query = "", entity = "") => {
    setIsLoading(true)
    try {
      const params = new URLSearchParams()
      if (query) params.set("q", query)
      if (entity) params.set("entity", entity)

      const res = await fetch(`http://localhost:8001/api/graph-viz?${params}`)
      const data = await res.json()
      setGraphData(data)
    } catch (error) {
      console.error("Failed to load graph:", error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      loadGraph(searchQuery, "")
      setSelectedEntity("")
    }
  }

  const handleEntityClick = useCallback((node: GraphNode) => {
    setSelectedEntity(node.name)
    setSearchQuery(node.name)
    loadGraph("", node.name)
  }, [loadGraph])

  // Fetch suggestions as user types
  useEffect(() => {
    if (searchQuery.length < 2) {
      setSuggestions([])
      return
    }

    const timeout = setTimeout(async () => {
      try {
        const res = await fetch(
          `http://localhost:8001/api/entity-search?q=${encodeURIComponent(searchQuery)}`
        )
        const data = await res.json()
        setSuggestions(data.entities || [])
      } catch (error) {
        console.error("Failed to fetch suggestions:", error)
      }
    }, 300)

    return () => clearTimeout(timeout)
  }, [searchQuery])

  const handleZoomIn = () => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() * 1.5, 400)
    }
  }

  const handleZoomOut = () => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() / 1.5, 400)
    }
  }

  const handleReset = () => {
    setSearchQuery("")
    setSelectedEntity("")
    loadGraph()
    if (graphRef.current) {
      graphRef.current.zoomToFit(400)
    }
  }

  return (
    <div className="h-screen bg-slate-950 text-slate-50 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="border-b border-slate-800 px-4 py-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-purple-600/20 text-purple-400">
            <Network className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white">Knowledge Graph</h1>
            <p className="text-xs text-slate-400">
              {stats
                ? `${stats.entities.toLocaleString()} entities, ${stats.relationships.toLocaleString()} relationships`
                : "Loading stats..."}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/">
            <Button variant="outline" size="sm" className="border-slate-700 text-slate-200">
              <Home className="h-4 w-4 mr-1" />
              <span className="hidden md:inline">Home</span>
            </Button>
          </Link>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside className="w-72 border-r border-slate-800 p-4 flex flex-col gap-4 overflow-y-auto">
          {/* Search */}
          <form onSubmit={handleSearch} className="space-y-2">
            <div className="relative">
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search entities..."
                className="bg-slate-900 border-slate-700 text-sm pr-10"
              />
              <button
                type="submit"
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                <Search className="h-4 w-4" />
              </button>
            </div>

            {/* Suggestions dropdown */}
            {suggestions.length > 0 && (
              <div className="bg-slate-900 border border-slate-700 rounded-md max-h-48 overflow-y-auto">
                {suggestions.map((entity) => (
                  <button
                    key={entity}
                    type="button"
                    onClick={() => {
                      setSearchQuery(entity)
                      setSelectedEntity(entity)
                      loadGraph("", entity)
                      setSuggestions([])
                    }}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-slate-800 text-slate-300 truncate"
                  >
                    {entity}
                  </button>
                ))}
              </div>
            )}
          </form>

          {/* Controls */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleZoomIn}
              className="flex-1 border-slate-700"
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleZoomOut}
              className="flex-1 border-slate-700"
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              className="flex-1 border-slate-700"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>

          {/* Stats */}
          <div className="bg-slate-900/50 rounded-lg p-3 space-y-2">
            <h3 className="text-xs font-semibold text-slate-400 uppercase">Current View</h3>
            <div className="text-sm">
              <span className="text-emerald-400">{graphData.nodes.length}</span>
              <span className="text-slate-500"> nodes, </span>
              <span className="text-blue-400">{graphData.links.length}</span>
              <span className="text-slate-500"> links</span>
            </div>
          </div>

          {/* Top Entities */}
          {stats && stats.top_entities && (
            <div className="bg-slate-900/50 rounded-lg p-3 space-y-2">
              <h3 className="text-xs font-semibold text-slate-400 uppercase">Top Entities</h3>
              <div className="space-y-1">
                {stats.top_entities.slice(0, 8).map((entity) => (
                  <button
                    key={entity.name}
                    onClick={() => {
                      setSearchQuery(entity.name)
                      setSelectedEntity(entity.name)
                      loadGraph("", entity.name)
                    }}
                    className="w-full text-left text-xs px-2 py-1 rounded hover:bg-slate-800 flex justify-between items-center"
                  >
                    <span className="truncate text-slate-300">{entity.name}</span>
                    <span className="text-slate-500 ml-2">{entity.connections}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Legend */}
          <div className="bg-slate-900/50 rounded-lg p-3 space-y-2">
            <h3 className="text-xs font-semibold text-slate-400 uppercase">Legend</h3>
            <div className="space-y-1 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                <span className="text-slate-300">Selected entity</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                <span className="text-slate-300">Hub (highly connected)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <span className="text-slate-300">Search match</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-gray-500"></div>
                <span className="text-slate-300">Related entity</span>
              </div>
            </div>
          </div>

          {/* Hovered Node Info */}
          {hoveredNode && (
            <div className="bg-slate-800 rounded-lg p-3 space-y-1">
              <h3 className="text-xs font-semibold text-slate-400 uppercase">Hovered</h3>
              <p className="text-sm text-white font-medium break-words">{hoveredNode.name}</p>
              <p className="text-xs text-slate-400">Type: {hoveredNode.group}</p>
            </div>
          )}
        </aside>

        {/* Graph Canvas */}
        <div className="flex-1 bg-slate-900/30 relative">
          {isLoading && (
            <div className="absolute inset-0 bg-slate-950/50 flex items-center justify-center z-10">
              <div className="text-slate-400">Loading graph...</div>
            </div>
          )}

          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            nodeLabel=""
            nodeColor={(node: any) => GROUP_COLORS[node.group] || "#6b7280"}
            nodeRelSize={6}
            nodeVal={(node: any) => node.size || 5}
            linkColor={() => "#334155"}
            linkWidth={1}
            linkDirectionalArrowLength={3}
            linkDirectionalArrowRelPos={1}
            onNodeClick={(node: any) => handleEntityClick(node)}
            onNodeHover={(node: any) => setHoveredNode(node)}
            backgroundColor="#0f172a"
            width={typeof window !== "undefined" ? window.innerWidth - 288 : 800}
            height={typeof window !== "undefined" ? window.innerHeight - 60 : 600}
            nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
              const label = node.name || node.id
              const fontSize = Math.max(12 / globalScale, 3)
              const nodeSize = node.size || 5

              // Draw node circle
              ctx.beginPath()
              ctx.arc(node.x, node.y, nodeSize, 0, 2 * Math.PI)
              ctx.fillStyle = GROUP_COLORS[node.group] || "#6b7280"
              ctx.fill()

              // Draw border for center/selected nodes
              if (node.group === "center" || node.group === "hub") {
                ctx.strokeStyle = "#ffffff"
                ctx.lineWidth = 1.5 / globalScale
                ctx.stroke()
              }

              // Draw label
              ctx.font = `${fontSize}px Sans-Serif`
              ctx.textAlign = "center"
              ctx.textBaseline = "middle"

              // Truncate long labels
              let displayLabel = label
              if (label.length > 20) {
                displayLabel = label.substring(0, 18) + "..."
              }

              // Draw text background for readability
              const textWidth = ctx.measureText(displayLabel).width
              ctx.fillStyle = "rgba(15, 23, 42, 0.8)"
              ctx.fillRect(
                node.x - textWidth / 2 - 2,
                node.y + nodeSize + 2,
                textWidth + 4,
                fontSize + 2
              )

              // Draw text
              ctx.fillStyle = "#e2e8f0"
              ctx.fillText(displayLabel, node.x, node.y + nodeSize + fontSize / 2 + 4)
            }}
            nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
              const nodeSize = node.size || 5
              ctx.beginPath()
              ctx.arc(node.x, node.y, nodeSize + 5, 0, 2 * Math.PI)
              ctx.fillStyle = color
              ctx.fill()
            }}
          />
        </div>
      </main>
    </div>
  )
}
