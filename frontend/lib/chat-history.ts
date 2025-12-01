/**
 * Chat history storage and management for the RAG chat interface
 */

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  createdAt: string
  query: string
  chunks?: Array<{
    id: string
    title?: string
    description?: string
    category?: string
    relevance?: number
    content?: string
    tags?: string[]
    metadata?: Record<string, unknown>
    source?: string
    createdAt?: string
  }>
}

interface ChatHistoryStore {
  getHistory(conversationId: string): Promise<ChatMessage[]>
  saveMessage(conversationId: string, message: ChatMessage): Promise<void>
  clearHistory(conversationId: string): Promise<void>
}

/**
 * In-memory chat history store with localStorage persistence
 */
class LocalStorageChatHistoryStore implements ChatHistoryStore {
  private storageKey = "chat-history"

  private getStorageKey(conversationId: string): string {
    return `${this.storageKey}-${conversationId}`
  }

  async getHistory(conversationId: string): Promise<ChatMessage[]> {
    if (typeof window === "undefined") return []

    try {
      const stored = localStorage.getItem(this.getStorageKey(conversationId))
      if (!stored) return []

      const messages = JSON.parse(stored) as ChatMessage[]
      return messages
    } catch (error) {
      console.error("Failed to load chat history:", error)
      return []
    }
  }

  async saveMessage(conversationId: string, message: ChatMessage): Promise<void> {
    if (typeof window === "undefined") return

    try {
      const history = await this.getHistory(conversationId)

      // Generate ID if not provided
      if (!message.id) {
        message.id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      }

      history.push(message)

      // Keep only last 100 messages to prevent storage overflow
      const trimmedHistory = history.slice(-100)

      localStorage.setItem(
        this.getStorageKey(conversationId),
        JSON.stringify(trimmedHistory)
      )
    } catch (error) {
      console.error("Failed to save chat message:", error)
    }
  }

  async clearHistory(conversationId: string): Promise<void> {
    if (typeof window === "undefined") return

    try {
      localStorage.removeItem(this.getStorageKey(conversationId))
    } catch (error) {
      console.error("Failed to clear chat history:", error)
    }
  }
}

// Default singleton instance
export const defaultChatHistoryStore: ChatHistoryStore = new LocalStorageChatHistoryStore()
