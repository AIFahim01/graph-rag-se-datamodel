#!/usr/bin/env python3
"""
ULTRATHINK - Frontend API Server with Swagger Documentation
RESTful API for frontend integration with vector search
"""

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
import json
from query_api import UltrathinkQueryAPI

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Initialize query API
print("Initializing ULTRATHINK Query API...")
api = UltrathinkQueryAPI()
print("API ready!")

# Swagger UI configuration
SWAGGER_URL = '/docs'
API_URL = '/api-spec'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "ULTRATHINK Query API",
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2
    }
)

app.register_blueprint(swaggerui_blueprint)

# Root redirect to docs
@app.route('/')
def index():
    """Redirect to API documentation"""
    return redirect('/docs')

@app.route('/api-spec')
def api_spec():
    """OpenAPI specification"""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "ULTRATHINK Query API",
            "version": "1.0.0",
            "description": "API for searching and querying HVDC/SynCon project documentation with vector embeddings"
        },
        "servers": [
            {"url": "http://localhost:5000", "description": "Local server"}
        ],
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health Check",
                    "description": "Check if the API service is running",
                    "tags": ["System"],
                    "responses": {
                        "200": {
                            "description": "Service is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "healthy"},
                                            "service": {"type": "string", "example": "ULTRATHINK Query API"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/statistics": {
                "get": {
                    "summary": "Database Statistics",
                    "description": "Get statistics about the document database",
                    "tags": ["Statistics"],
                    "responses": {
                        "200": {
                            "description": "Database statistics",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "total_documents": {"type": "integer", "example": 214426},
                                                    "by_technology": {
                                                        "type": "object",
                                                        "example": {"HVDC": 13470, "SynCon": 26958}
                                                    },
                                                    "by_year": {
                                                        "type": "object",
                                                        "example": {"2021": 25135, "2022": 100991}
                                                    },
                                                    "top_customers": {"type": "object"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/search/metadata": {
                "post": {
                    "summary": "Metadata Search",
                    "description": "Search documents by metadata fields",
                    "tags": ["Search"],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "technology": {
                                            "type": "string",
                                            "enum": ["HVDC", "SynCon"],
                                            "description": "Technology type filter"
                                        },
                                        "year": {
                                            "type": "string",
                                            "enum": ["2021", "2022", "2024", "2025"],
                                            "description": "Year filter"
                                        },
                                        "customer": {
                                            "type": "string",
                                            "description": "Customer name filter"
                                        },
                                        "project_id": {
                                            "type": "string",
                                            "description": "Specific project ID",
                                            "example": "GC21_001"
                                        },
                                        "limit": {
                                            "type": "integer",
                                            "default": 100,
                                            "description": "Maximum results to return"
                                        }
                                    }
                                },
                                "examples": {
                                    "hvdc_2025": {
                                        "summary": "HVDC projects in 2025",
                                        "value": {
                                            "technology": "HVDC",
                                            "year": "2025"
                                        }
                                    },
                                    "syncon_all": {
                                        "summary": "All SynCon projects",
                                        "value": {
                                            "technology": "SynCon",
                                            "limit": 500
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Search results grouped by project",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "total_chunks": {"type": "integer"},
                                            "total_projects": {"type": "integer"},
                                            "projects": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "project_id": {"type": "string"},
                                                        "project_name": {"type": "string"},
                                                        "customer": {"type": "string"},
                                                        "technology": {"type": "string"},
                                                        "year": {"type": "string"},
                                                        "pages": {"type": "array"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/search/vector": {
                "post": {
                    "summary": "Vector Similarity Search",
                    "description": "Semantic search using vector embeddings",
                    "tags": ["Search"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["query"],
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "Search query text",
                                            "example": "transformer protection systems"
                                        },
                                        "top_k": {
                                            "type": "integer",
                                            "default": 10,
                                            "description": "Number of results to return"
                                        },
                                        "technology_filter": {
                                            "type": "string",
                                            "enum": ["HVDC", "SynCon"],
                                            "description": "Filter by technology"
                                        },
                                        "year_filter": {
                                            "type": "string",
                                            "enum": ["2021", "2022", "2024", "2025"],
                                            "description": "Filter by year"
                                        },
                                        "customer_filter": {
                                            "type": "string",
                                            "description": "Filter by customer"
                                        }
                                    }
                                },
                                "examples": {
                                    "basic_search": {
                                        "summary": "Basic semantic search",
                                        "value": {
                                            "query": "power requirements",
                                            "top_k": 5
                                        }
                                    },
                                    "filtered_search": {
                                        "summary": "Search with filters",
                                        "value": {
                                            "query": "converter specifications",
                                            "technology_filter": "HVDC",
                                            "year_filter": "2024",
                                            "top_k": 10
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Semantically similar documents",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "query": {"type": "string"},
                                            "total_results": {"type": "integer"},
                                            "results": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "chunk_id": {"type": "string"},
                                                        "project_id": {"type": "string"},
                                                        "technology": {"type": "string"},
                                                        "year": {"type": "string"},
                                                        "customer": {"type": "string"},
                                                        "page": {"type": "integer"},
                                                        "text": {"type": "string"},
                                                        "score": {"type": "number"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/answer": {
                "post": {
                    "summary": "Natural Language Q&A",
                    "description": "Answer questions in natural language",
                    "tags": ["Q&A"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["question"],
                                    "properties": {
                                        "question": {
                                            "type": "string",
                                            "description": "Natural language question",
                                            "example": "Which projects have HVDC in 2025?"
                                        }
                                    }
                                },
                                "examples": {
                                    "count_question": {
                                        "summary": "Count question",
                                        "value": {
                                            "question": "How many HVDC documents are there?"
                                        }
                                    },
                                    "list_question": {
                                        "summary": "Listing question",
                                        "value": {
                                            "question": "Which projects have HVDC in 2024?"
                                        }
                                    },
                                    "semantic_question": {
                                        "summary": "Semantic question",
                                        "value": {
                                            "question": "What are the protection systems for transformers?"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Answer to the question",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "question": {"type": "string"},
                                            "answer": {
                                                "type": "object",
                                                "properties": {
                                                    "answer_type": {
                                                        "type": "string",
                                                        "enum": ["count", "list", "semantic_search"]
                                                    },
                                                    "count": {"type": "integer"},
                                                    "unique_projects": {"type": "integer"},
                                                    "projects": {"type": "array"},
                                                    "results": {"type": "array"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/projects/list": {
                "get": {
                    "summary": "List All Projects",
                    "description": "Get a list of all unique projects",
                    "tags": ["Projects"],
                    "responses": {
                        "200": {
                            "description": "List of all projects",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "total_projects": {"type": "integer"},
                                            "projects": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "project_id": {"type": "string"},
                                                        "project_name": {"type": "string"},
                                                        "customer": {"type": "string"},
                                                        "technology": {"type": "string"},
                                                        "year": {"type": "string"},
                                                        "total_pages": {"type": "integer"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/projects/years": {
                "get": {
                    "summary": "Get Available Years",
                    "description": "Get all years with document counts",
                    "tags": ["Projects"],
                    "responses": {
                        "200": {
                            "description": "Available years",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "years": {
                                                "type": "array",
                                                "items": {"type": "string"}
                                            },
                                            "counts": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/projects/technologies": {
                "get": {
                    "summary": "Get Available Technologies",
                    "description": "Get all technology types with document counts",
                    "tags": ["Projects"],
                    "responses": {
                        "200": {
                            "description": "Available technologies",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "technologies": {
                                                "type": "array",
                                                "items": {"type": "string"}
                                            },
                                            "counts": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "tags": [
            {"name": "System", "description": "System endpoints"},
            {"name": "Statistics", "description": "Database statistics"},
            {"name": "Search", "description": "Search operations"},
            {"name": "Q&A", "description": "Question answering"},
            {"name": "Projects", "description": "Project information"}
        ]
    }
    return jsonify(spec)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'ULTRATHINK Query API'})

@app.route('/statistics', methods=['GET'])
def get_statistics():
    """Get database statistics"""
    try:
        stats = api.get_statistics()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/search/metadata', methods=['POST'])
def metadata_search():
    """Metadata-based search"""
    try:
        data = request.json or {}

        results = api.metadata_search(
            technology=data.get('technology'),
            year=data.get('year'),
            customer=data.get('customer'),
            project_id=data.get('project_id'),
            limit=data.get('limit', 100)
        )

        # Group results by project for better frontend display
        projects = {}
        for r in results:
            pid = r['project_id']
            if pid not in projects:
                projects[pid] = {
                    'project_id': pid,
                    'project_name': r['project_name'],
                    'customer': r['customer'],
                    'technology': r['technology'],
                    'year': r['year'],
                    'file_name': r['file_name'],
                    'pages': []
                }
            projects[pid]['pages'].append({
                'chunk_id': r['chunk_id'],
                'page': r['page'],
                'text': r['text'][:200] + '...' if len(r['text']) > 200 else r['text']
            })

        return jsonify({
            'success': True,
            'total_chunks': len(results),
            'total_projects': len(projects),
            'projects': list(projects.values()),
            'filters_applied': {
                'technology': data.get('technology'),
                'year': data.get('year'),
                'customer': data.get('customer'),
                'project_id': data.get('project_id')
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/search/vector', methods=['POST'])
def vector_search():
    """Vector similarity search"""
    try:
        data = request.json or {}

        if 'query' not in data:
            return jsonify({'success': False, 'error': 'Query text is required'}), 400

        results = api.vector_search(
            query_text=data['query'],
            top_k=data.get('top_k', 10),
            technology_filter=data.get('technology_filter'),
            year_filter=data.get('year_filter'),
            customer_filter=data.get('customer_filter')
        )

        return jsonify({
            'success': True,
            'query': data['query'],
            'total_results': len(results),
            'results': results,
            'filters_applied': {
                'technology': data.get('technology_filter'),
                'year': data.get('year_filter'),
                'customer': data.get('customer_filter')
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/answer', methods=['POST'])
def answer_question():
    """Natural language question answering"""
    try:
        data = request.json or {}

        if 'question' not in data:
            return jsonify({'success': False, 'error': 'Question is required'}), 400

        answer = api.answer_query(data['question'])

        return jsonify({
            'success': True,
            'question': data['question'],
            'answer': answer
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/projects/list', methods=['GET'])
def list_projects():
    """List all unique projects with their metadata"""
    try:
        # Get unique projects
        results = api.metadata_search(limit=100000)

        projects = {}
        for r in results:
            pid = r['project_id']
            if pid not in projects:
                projects[pid] = {
                    'project_id': pid,
                    'project_name': r['project_name'],
                    'customer': r['customer'],
                    'technology': r['technology'],
                    'year': r['year'],
                    'total_pages': 0
                }
            projects[pid]['total_pages'] += 1

        # Sort by year and project ID
        project_list = sorted(
            projects.values(),
            key=lambda x: (x['year'], x['project_id'])
        )

        return jsonify({
            'success': True,
            'total_projects': len(project_list),
            'projects': project_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/projects/years', methods=['GET'])
def get_years():
    """Get all available years"""
    try:
        stats = api.get_statistics()
        years = list(stats['by_year'].keys())

        return jsonify({
            'success': True,
            'years': sorted(years),
            'counts': stats['by_year']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/projects/technologies', methods=['GET'])
def get_technologies():
    """Get all available technologies"""
    try:
        stats = api.get_statistics()

        return jsonify({
            'success': True,
            'technologies': list(stats['by_technology'].keys()),
            'counts': stats['by_technology']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 80)
    print("ULTRATHINK Frontend API Server with Swagger Docs")
    print("=" * 80)
    print()
    print("📡 Starting server on http://localhost:5000")
    print("📚 API Documentation: http://localhost:5000/docs")
    print()
    print("Available endpoints:")
    print("  GET  /                      - Redirect to /docs")
    print("  GET  /docs                  - Swagger UI Documentation")
    print("  GET  /api-spec              - OpenAPI Specification")
    print("  GET  /health                - Health check")
    print("  GET  /statistics            - Database statistics")
    print("  POST /search/metadata       - Search by metadata")
    print("  POST /search/vector         - Vector similarity search")
    print("  POST /answer                - Natural language Q&A")
    print("  GET  /projects/list         - List all projects")
    print("  GET  /projects/years        - Get available years")
    print("  GET  /projects/technologies - Get available technologies")
    print()
    print("=" * 80)

    # Run server
    app.run(host='0.0.0.0', port=5000, debug=True)