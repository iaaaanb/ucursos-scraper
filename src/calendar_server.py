#!/usr/bin/env python3
"""
Calendar Server module for serving U-Cursos calendar via HTTP.
Allows calendar apps like Thunderbird to subscribe to the calendar.
"""

import os
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))


class CalendarHTTPRequestHandler(SimpleHTTPRequestHandler):
    """
    Custom HTTP request handler for serving calendar files.
    Serves .ics files with correct MIME type and handles CORS.
    """

    def __init__(self, *args, calendar_path=None, **kwargs):
        self.calendar_path = calendar_path
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests for calendar file."""
        if self.path == '/calendar.ics' or self.path == '/':
            try:
                # Read calendar file
                if not self.calendar_path or not self.calendar_path.exists():
                    self.send_error(404, "Calendar file not found. Run scraper first to generate calendar.ics")
                    return

                # Send response headers
                self.send_response(200)
                self.send_header('Content-Type', 'text/calendar; charset=utf-8')
                self.send_header('Content-Disposition', 'inline; filename="ucursos_calendar.ics"')
                # Add CORS headers for cross-origin requests
                self.send_header('Access-Control-Allow-Origin', '*')
                # Add cache control to ensure fresh data
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()

                # Send calendar file content
                with open(self.calendar_path, 'rb') as f:
                    self.wfile.write(f.read())

            except Exception as e:
                self.send_error(500, f"Error serving calendar: {str(e)}")
        else:
            self.send_error(404, "Not found. Use /calendar.ics to access the calendar")

    def log_message(self, format, *args):
        """Override to provide cleaner log messages."""
        if '200' in str(args):
            print(f"📅 Calendar served to {self.client_address[0]}")
        else:
            print(f"⚠️  {self.client_address[0]} - {format % args}")


def serve_calendar(calendar_path, port=8000, host='localhost'):
    """
    Start HTTP server to serve calendar file.

    Args:
        calendar_path (str or Path): Path to calendar.ics file
        port (int): Port number for HTTP server (default: 8000)
        host (str): Host address to bind to (default: localhost)

    Returns:
        None (runs until interrupted)
    """
    calendar_path = Path(calendar_path)

    if not calendar_path.exists():
        print(f'❌ Calendar file not found: {calendar_path}')
        print(f'   Run the scraper first to generate the calendar:')
        print(f'   python src/main.py -c')
        sys.exit(1)

    # Create handler class with calendar path bound
    def handler(*args, **kwargs):
        CalendarHTTPRequestHandler(*args, calendar_path=calendar_path, **kwargs)

    try:
        # Create HTTP server
        with socketserver.TCPServer((host, port), handler) as httpd:
            print('━' * 70)
            print(f'📅 U-Cursos Calendar Server')
            print('━' * 70)
            print(f'🌐 Serving calendar at: http://{host}:{port}/calendar.ics')
            print(f'📁 Calendar file: {calendar_path.absolute()}')
            print()
            print('📋 To subscribe in calendar apps:')
            print()
            print('   Thunderbird:')
            print(f'   1. Right-click on calendar list → New Calendar')
            print(f'   2. Choose "On the Network"')
            print(f'   3. Enter URL: http://{host}:{port}/calendar.ics')
            print(f'   4. Set a name: "U-Cursos"')
            print()
            print('   Google Calendar:')
            print(f'   1. Settings → Add calendar → From URL')
            print(f'   2. Enter: http://{host}:{port}/calendar.ics')
            print()
            print('   Apple Calendar:')
            print(f'   1. File → New Calendar Subscription')
            print(f'   2. Enter: http://{host}:{port}/calendar.ics')
            print()
            print('💡 The calendar will auto-refresh when you re-run the scraper')
            print('🛑 Press Ctrl+C to stop the server')
            print('━' * 70)
            print()

            # Start serving
            httpd.serve_forever()

    except KeyboardInterrupt:
        print('\n\n🛑 Server stopped')
        sys.exit(0)
    except OSError as e:
        if 'Address already in use' in str(e):
            print(f'❌ Port {port} is already in use')
            print(f'   Try a different port: --port {port + 1}')
            print(f'   Or stop the process using port {port}')
        else:
            print(f'❌ Server error: {str(e)}')
        sys.exit(1)
    except Exception as e:
        print(f'❌ Error starting server: {str(e)}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    # Allow running as standalone script
    import argparse

    parser = argparse.ArgumentParser(description='Serve U-Cursos calendar via HTTP')
    parser.add_argument('calendar_path', help='Path to calendar.ics file')
    parser.add_argument('--port', type=int, default=8000, help='Port number (default: 8000)')
    parser.add_argument('--host', default='localhost', help='Host address (default: localhost)')

    args = parser.parse_args()
    serve_calendar(args.calendar_path, port=args.port, host=args.host)
