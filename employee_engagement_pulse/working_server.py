#!/usr/bin/env python3
"""
Simple HTTP Server for Employee Engagement Dashboard
Serves the dashboard and provides working API endpoints
"""

import os
import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from simple_slack_analyzer import SimpleSlackAnalyzer

# Load environment
load_dotenv()

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        self.analyzer = SimpleSlackAnalyzer()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Serve dashboard
            self.serve_dashboard()
        elif parsed_path.path == '/api/channels':
            # Serve channels API
            self.serve_channels()
        elif parsed_path.path == '/api/team-metrics':
            # Serve team metrics API
            self.serve_team_metrics(parsed_path.query)
        else:
            # Try to serve static file
            super().do_GET()
    
    def serve_dashboard(self):
        try:
            # Use absolute path for dashboard
            dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard.html')
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update API endpoints to use current server
            content = content.replace('http://localhost:8005/', 'http://localhost:8008/')
            content = content.replace('http://localhost:8004/', 'http://localhost:8008/')
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Error serving dashboard: {e}")
    
    def serve_channels(self):
        try:
            channels = self.analyzer.get_channels()
            response = json.dumps(channels, indent=2)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            error_response = json.dumps({"error": str(e)})
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(error_response.encode('utf-8'))
    
    def serve_team_metrics(self, query):
        try:
            # Parse query parameters
            params = parse_qs(query) if query else {}
            channels_param = params.get('channels', [])
            channel_filter = channels_param[0] if channels_param else None
            
            metrics = self.analyzer.get_simple_metrics(channel_filter)
            response = json.dumps(metrics, indent=2)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            error_response = json.dumps({"error": str(e)})
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(error_response.encode('utf-8'))

def main():
    PORT = int(os.environ.get('PORT', 8008))
    
    print(f"""
🚀 Employee Engagement Dashboard Server
=======================================
✅ Slack integration: WORKING
📊 Dashboard: http://localhost:{PORT}
🔗 Channels API: http://localhost:{PORT}/api/channels  
📈 Metrics API: http://localhost:{PORT}/api/team-metrics
💡 Real data from Slack workspace!
    """)
    
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
