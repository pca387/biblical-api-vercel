"""
Vercel Serverless Function dla Biblical API
Plik: api/index.py
"""

from http.server import BaseHTTPRequestHandler
import json
import sqlite3
import os
from urllib.parse import urlparse, parse_qs

# Ścieżka do bazy - Vercel kopiuje pliki do /var/task/
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'biblical_index.db')

def get_db_connection():
    """Połączenie z bazą danych"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse URL
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        # CORS headers
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('X-Robots-Tag', 'all')
        self.end_headers()
        
        try:
            # Router
            if path == '/api' or path == '/api/':
                response = {
                    "name": "Biblical API",
                    "status": "online",
                    "endpoints": [
                        "/api/search?q=word",
                        "/api/documents",
                        "/api/document/1",
                        "/api/stats"
                    ],
                    "hosting": "Vercel",
                    "cors": "enabled",
                    "robots": "allowed"
                }
                
            elif path == '/api/search' or path.startswith('/api/search'):
                query = query_params.get('q', [''])[0]
                if not query:
                    response = {'error': 'Missing query parameter q'}
                else:
                    response = self.search(query)
                    
            elif path == '/api/documents' or path.startswith('/api/documents'):
                response = self.get_documents()
                
            elif path.startswith('/api/document/'):
                doc_id = path.split('/')[-1]
                try:
                    doc_id = int(doc_id)
                    response = self.get_document(doc_id)
                except ValueError:
                    response = {'error': 'Invalid document ID'}
                    
            elif path == '/api/stats' or path.startswith('/api/stats'):
                response = self.get_stats()
                
            else:
                response = {'error': 'Unknown endpoint', 'path': path}
                
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            
        except Exception as e:
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def search(self, query):
        """Wyszukiwanie w tekstach"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, filename, 
                       snippet(documents_fts, 0, '<mark>', '</mark>', '...', 50) as content,
                       rank as score
                FROM documents_fts
                WHERE documents_fts MATCH ?
                ORDER BY rank
                LIMIT 20
            """, (query,))
            
            results = []
            for row in cursor:
                results.append({
                    'id': row['id'],
                    'filename': row['filename'],
                    'content': row['content'],
                    'score': abs(row['score'])
                })
            
            conn.close()
            return {
                'query': query,
                'total_results': len(results),
                'results': results
            }
        except Exception as e:
            return {'error': f'Search error: {str(e)}'}
    
    def get_documents(self):
        """Lista wszystkich dokumentów"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, filename, length(content) as size
                FROM documents
                ORDER BY id
            """)
            
            documents = []
            for row in cursor:
                documents.append({
                    'id': row['id'],
                    'filename': row['filename'],
                    'size': row['size']
                })
            
            conn.close()
            return {
                'total': len(documents),
                'documents': documents
            }
        except Exception as e:
            return {'error': f'Documents error: {str(e)}'}
    
    def get_document(self, doc_id):
        """Pobierz konkretny dokument"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, filename, content
                FROM documents
                WHERE id = ?
            """, (doc_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return {'error': f'Document {doc_id} not found'}
            
            conn.close()
            return {
                'id': row['id'],
                'filename': row['filename'],
                'content': row['content']
            }
        except Exception as e:
            return {'error': f'Document error: {str(e)}'}
    
    def get_stats(self):
        """Statystyki bazy danych"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM documents")
            doc_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT SUM(length(content)) as total FROM documents")
            total_size = cursor.fetchone()['total']
            
            conn.close()
            return {
                'total_documents': doc_count,
                'total_size': total_size,
                'api_version': 'vercel-2.0',
                'cors_enabled': True,
                'robots_allowed': True,
                'hosting': 'Vercel Serverless'
            }
        except Exception as e:
            return {'error': f'Stats error: {str(e)}'}
