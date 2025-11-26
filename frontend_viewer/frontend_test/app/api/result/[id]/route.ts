export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params

  if (!id) {
    return Response.json({ error: "ID parameter is required" }, { status: 400 })
  }

  try {
    // Call Python FastAPI backend
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

    // Decode ID first (it comes URL-encoded from the route), then re-encode properly
    const decodedId = decodeURIComponent(id)
    console.log(`Fetching result: ${backendUrl}/api/result/${decodedId}`)

    const response = await fetch(`${backendUrl}/api/result/${encodeURIComponent(decodedId)}`)

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }

    const data = await response.json()

    if (data.error) {
      throw new Error(data.error)
    }

    return Response.json(data)

  } catch (error) {
    console.error('Error calling backend API:', error)
    return Response.json(
      { error: error instanceof Error ? error.message : "Failed to fetch result" },
      { status: 500 }
    )
  }
}
