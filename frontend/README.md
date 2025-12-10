# Vector Database Viewer

A modern, high-performance web application for searching and viewing vector database retrieval results. Built with Next.js 16 and designed to provide an intuitive, Google-like search experience for exploring vector embeddings and similarity search results.

---

## 🔒 Repository Information

**Private Repository**  
Owner: **InfinitiBit**  
Repository: `https://github.com/InfinitiBit/se-vector-db-viewer.git`

---

## 📋 Overview

The Vector Database Viewer is a frontend application that demonstrates vector database search capabilities with support for both sentence-based and keyword-based queries. It provides a clean, responsive interface for searching, browsing paginated results, and viewing detailed information about each search result.

---

## ✨ Features

### 🔍 **Search Capabilities**
- **Sentence-based search** - Natural language queries for semantic search
- **Keyword-based search** - Traditional keyword matching
- **Real-time search** - Instant results as you search
- **Example queries** - Pre-populated suggestions to get started

### 📄 **Results Display**
- **Google-like interface** - Familiar, intuitive search results layout
- **Fixed search bar** - Sticky header that remains visible while scrolling
- **Pagination** - Display 10 results per page with smart pagination controls
- **Relevance scoring** - Results sorted by similarity/relevance scores
- **Rich metadata** - Category, author, views, ratings, and more

### 🎯 **Navigation & UX**
- **State preservation** - Maintains page number and scroll position
- **Smart back navigation** - Returns to results page (not home) from detail view
- **Responsive design** - Works seamlessly on desktop, tablet, and mobile
- **Dark theme** - Modern slate color palette optimized for readability

### ⚡ **Performance**
- **Single API call** - All data fetched at once, no separate detail page requests
- **Client-side caching** - Uses sessionStorage for instant navigation
- **Optimized rendering** - Server-side rendering with Next.js App Router
- **Fast page transitions** - Smooth navigation between pages

---

## 🛠️ Tech Stack

### **Core Framework**
- **Next.js 16.0.0** - React framework with App Router and Turbopack
- **React 19.2.0** - UI library with latest features
- **TypeScript 5** - Type-safe development

### **Styling**
- **Tailwind CSS 4.1.9** - Utility-first CSS framework
- **shadcn/ui** - High-quality, accessible component library
- **Lucide React** - Beautiful, consistent icon set
- **tailwindcss-animate** - Smooth animations and transitions

### **Additional Libraries**
- **class-variance-authority** - Component variant management
- **clsx & tailwind-merge** - Conditional className utilities
- **next-themes** - Dark/light theme support

---

## 📁 Project Structure

```
se-vector-db-viewer/
├── app/                          # Next.js App Router directory
│   ├── api/                      # API routes
│   │   └── search/              # Search endpoint
│   │       └── route.ts         # GET /api/search handler
│   ├── result/[id]/             # Dynamic result detail pages
│   │   └── page.tsx             # Detail page component
│   ├── results/                 # Search results page
│   │   ├── page.tsx             # Results list component
│   │   └── loading.tsx          # Loading state
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Home/search page
│   ├── loading.tsx              # Global loading state
│   └── globals.css              # Global styles
├── components/                   # Reusable React components
│   ├── ui/                      # shadcn/ui components
│   ├── results-list.tsx         # Results list component
│   ├── search-interface.tsx     # Main search interface
│   └── theme-provider.tsx       # Theme context provider
├── lib/                         # Utility functions
│   └── utils.ts                 # Helper utilities
├── hooks/                       # Custom React hooks
│   ├── use-mobile.ts            # Mobile detection hook
│   └── use-toast.ts             # Toast notification hook
├── public/                      # Static assets
├── styles/                      # Additional stylesheets
└── package.json                 # Project dependencies
```

---

## 🚀 Getting Started

### **Prerequisites**

Before you begin, ensure you have the following installed:

- **Node.js** - Version 18.x or higher (recommended: 20.x LTS)
- **npm** or **pnpm** - Package manager (pnpm recommended for faster installs)
- **Git** - For cloning the repository

### **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/InfinitiBit/se-vector-db-viewer.git
   cd se-vector-db-viewer
   ```

2. **Install dependencies**

   Using npm:
   ```bash
   npm install
   ```

   Or using pnpm (recommended):
   ```bash
   pnpm install
   ```

3. **Verify installation**
   ```bash
   npm run dev
   # or
   pnpm dev
   ```

### **Development Server**

Start the development server with hot-reload:

```bash
npm run dev
# or
pnpm dev
```

The application will be available at:
- **Local**: `http://localhost:3000`
- **Network**: `http://[your-ip]:3000`

### **Build for Production**

Create an optimized production build:

```bash
npm run build
# or
pnpm build
```

### **Start Production Server**

After building, start the production server:

```bash
npm start
# or
pnpm start
```

### **Linting**

Run ESLint to check code quality:

```bash
npm run lint
# or
pnpm lint
```

---

## 📖 Usage

### **1. Search for Content**

1. Navigate to the home page (`http://localhost:3000`)
2. Enter a search query in the input field:
   - **Sentence-based**: "machine learning algorithms"
   - **Keyword-based**: "neural networks"
   - **Natural language**: "how to build a web application"
3. Click the **Search** button or press **Enter**

### **2. Browse Results**

- View search results displayed 10 per page
- See relevance scores, categories, and descriptions
- Use the **fixed search bar** at the top to perform new searches
- Navigate through pages using:
  - **Previous/Next** buttons
  - **Page numbers** (click to jump to specific page)

### **3. View Details**

1. Click on any search result to view full details
2. See complete content, tags, metadata, and source information
3. Use the **Copy** button to copy content to clipboard
4. Click **Back to Results** to return to your search results

### **4. Navigation Features**

- **State preservation**: Your page number is maintained when viewing details
- **Smart back button**: Returns to results page, not home page
- **Scroll position**: Automatically scrolls to top when changing pages

---

## 🔌 API Routes

### **GET /api/search**

Search endpoint that returns vector database results.

#### **Request**

```http
GET /api/search?q=machine+learning
```

**Query Parameters:**
- `q` (required) - Search query string

#### **Response**

```json
{
  "results": [
    {
      "id": "1",
      "title": "Understanding Machine Learning Fundamentals",
      "description": "A comprehensive guide to machine learning concepts...",
      "category": "Machine Learning",
      "relevance": 0.95,
      "content": "Full article content...",
      "tags": ["machine-learning", "ai", "algorithms"],
      "metadata": {
        "author": "Dr. Jane Smith",
        "views": 15420,
        "rating": 4.8,
        "difficulty": "Beginner",
        "duration": "2 hours"
      },
      "source": "ML Academy",
      "createdAt": "2024-01-15"
    }
  ],
  "query": "machine learning",
  "count": 15
}
```

#### **Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for the result |
| `title` | string | Result title |
| `description` | string | Brief description/summary |
| `category` | string | Content category |
| `relevance` | number | Similarity score (0-1) |
| `content` | string | Full content text |
| `tags` | string[] | Associated tags |
| `metadata` | object | Additional metadata (author, views, rating, etc.) |
| `source` | string | Content source |
| `createdAt` | string | Creation date (ISO format) |

#### **Notes**

- All detail information is included in the initial response
- No separate API call is needed for the detail page
- Results are sorted by relevance score (highest first)
- Currently uses mock data for demonstration purposes

---

## 🏗️ Architecture & Design Decisions

### **Single API Call Pattern**

The application fetches all data (including detail information) in a single API call to the search endpoint. This design:

- **Reduces server load** - Fewer API requests
- **Improves performance** - Instant detail page rendering
- **Simplifies caching** - All data stored in sessionStorage
- **Better UX** - No loading states when viewing details

### **State Management**

Uses browser `sessionStorage` for client-side state persistence:

```typescript
// Store complete results after search
sessionStorage.setItem("searchResults", JSON.stringify(results))
sessionStorage.setItem("lastQuery", query)
sessionStorage.setItem("currentPage", page.toString())
```

This approach:
- Persists data across page navigations
- Maintains state during browser session
- Enables smart back navigation
- No external state management library needed

### **Pagination Strategy**

Implements client-side pagination with smart controls:

- Shows 10 results per page
- Displays page numbers with ellipsis for large sets
- Highlights current page
- Disables Previous/Next at boundaries
- Stores page state in URL and sessionStorage

### **Hydration Optimization**

Prevents React hydration mismatches by:

- Using `useEffect` for client-side only operations (autofocus)
- Adding `suppressHydrationWarning` to inputs (handles browser extensions)
- Avoiding server/client rendering differences

---

## 🎨 Styling & Theming

### **Color Palette**

The application uses a dark theme with slate colors:

- **Background**: Gradient from slate-950 to slate-900
- **Primary**: Blue-600 (buttons, links, highlights)
- **Text**: White (primary), slate-400 (secondary)
- **Borders**: Slate-700
- **Hover states**: Slate-800

### **Component Library**

Built with **shadcn/ui** components:

- Fully accessible (ARIA compliant)
- Customizable with Tailwind CSS
- Consistent design system
- Dark theme optimized

### **Responsive Design**

Breakpoints:
- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

---

## 🔧 Configuration Files

### **next.config.mjs**

Next.js configuration with Turbopack enabled for faster builds.

### **tsconfig.json**

TypeScript configuration with strict mode and path aliases:

```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

### **tailwind.config.js**

Tailwind CSS configuration with custom theme and shadcn/ui integration.

### **components.json**

shadcn/ui configuration for component generation.

---

## 📝 Development Notes

### **Mock Data**

The application currently uses mock data in `/api/search/route.ts` with 15 sample results covering various topics:

- Machine Learning
- Deep Learning
- Natural Language Processing
- Computer Vision
- Reinforcement Learning
- Data Science
- Cloud Computing
- Web Development
- Cybersecurity
- Database Design
- Mobile Development
- DevOps
- Blockchain
- AI Ethics
- IoT

### **Future Enhancements**

Potential improvements for production deployment:

1. **Real Vector Database Integration**
   - Connect to actual vector database (Pinecone, Weaviate, Qdrant)
   - Implement real embedding generation
   - Add vector similarity search

2. **Advanced Features**
   - Filters (category, date, rating)
   - Sort options (relevance, date, popularity)
   - Search history
   - Bookmarks/favorites
   - Export results

3. **Performance Optimizations**
   - Implement virtual scrolling for large result sets
   - Add request caching with SWR or React Query
   - Optimize images with Next.js Image component

4. **Analytics**
   - Track search queries
   - Monitor user behavior
   - A/B testing for UI improvements

---

## 🤝 Contributing

This is a private repository owned by **InfinitiBit**. For contribution guidelines, please contact the repository administrators.

---

## 📄 License

This project is proprietary software owned by **InfinitiBit**. All rights reserved.

Unauthorized copying, distribution, or use of this software is strictly prohibited.

---

## 👥 Contact

For questions, issues, or access requests, please contact:

**InfinitiBit**
Repository: `https://github.com/InfinitiBit/se-vector-db-viewer.git`

---

## 🙏 Acknowledgments

Built with:
- [Next.js](https://nextjs.org/) - The React Framework
- [shadcn/ui](https://ui.shadcn.com/) - Component Library
- [Tailwind CSS](https://tailwindcss.com/) - Styling Framework
- [Lucide](https://lucide.dev/) - Icon Library
- [Vercel](https://vercel.com/) - Deployment Platform

---

**Last Updated**: 2025-11-12
**Version**: 0.1.0
**Status**: Active Development

