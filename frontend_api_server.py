#!/usr/bin/env python3
"""
ULTRATHINK - Frontend API Server
RESTful API for frontend integration with vector search
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from query_api import UltrathinkQueryAPI

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Initialize query API
print("Initializing ULTRATHINK Query API...")
api = UltrathinkQueryAPI()
print("API ready!")

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
    """
    Metadata-based search

    Request body:
    {
        "technology": "HVDC" or "SynCon" (optional),
        "year": "2025" (optional),
        "customer": "customer_name" (optional),
        "project_id": "GC21_001" (optional),
        "limit": 100 (optional, default 100)
    }
    """
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
    """
    Vector similarity search

    Request body:
    {
        "query": "power requirements for HVDC",
        "top_k": 10 (optional, default 10),
        "technology_filter": "HVDC" (optional),
        "year_filter": "2025" (optional),
        "customer_filter": "customer_name" (optional)
    }
    """
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
    """
    Natural language question answering

    Request body:
    {
        "question": "Which projects have HVDC in 2025?"
    }
    """
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
    """
    List all unique projects with their metadata
    """
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
    print("ULTRATHINK Frontend API Server")
    print("=" * 80)
    print()
    print("📡 Starting server on http://localhost:5000")
    print()
    print("Available endpoints:")
    print("  GET  /health                - Health check")
    print("  GET  /statistics            - Database statistics")
    print("  POST /search/metadata       - Search by metadata")
    print("  POST /search/vector         - Vector similarity search")
    print("  POST /answer               - Natural language Q&A")
    print("  GET  /projects/list        - List all projects")
    print("  GET  /projects/years       - Get available years")
    print("  GET  /projects/technologies - Get available technologies")
    print()
    print("=" * 80)

    # Run server
    app.run(host='0.0.0.0', port=5000, debug=True)