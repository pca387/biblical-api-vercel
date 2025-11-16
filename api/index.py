"""
Test API handler dla Vercel - bez bazy danych
"""

def handler(request, response):
    """Simple test handler"""
    
    import json
    from urllib.parse import urlparse, parse_qs
    
    # Parse URL
    parsed = urlparse(request.url)
    path = parsed.path
    params = parse_qs(parsed.query)
    
    # Set headers
    response.status_code = 200
    response.headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }
    
    # Test endpoints
    if path == '/api' or path == '/api/':
        result = {
            "status": "online",
            "message": "Biblical API Test - Database not connected",
            "endpoints": ["/api", "/api/test", "/api/search?q=word"]
        }
    
    elif path == '/api/stats' or path.startswith('/api/stats'):
        result = {
            "status": "test mode",
            "message": "Database not connected - this is a test response",
            "total_documents": 31,
            "note": "Real data will be available after fixing database connection"
        }
    
    elif path == '/api/search' or path.startswith('/api/search'):
        query = params.get('q', [''])[0]
        result = {
            "status": "test mode",
            "query": query,
            "message": f"Search for '{query}' - database not connected",
            "results": []
        }
    
    elif path == '/api/test':
        result = {
            "status": "API is working!",
            "vercel": "deployment successful",
            "database": "not connected - file too large or not found"
        }
    
    else:
        result = {"error": "Unknown endpoint", "path": path}
    
    return json.dumps(result)