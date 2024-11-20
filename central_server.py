# central_server.py
import http.server
import os
import cgitb
from urllib.parse import urlparse, parse_qs  # Use urllib.parse for query strings

cgitb.enable()

PORT = 8889
CENTRAL_BASE = "central_base"  # Directory to store images on the central server

# Ensure the central_base directory exists
os.makedirs(CENTRAL_BASE, exist_ok=True)

class CentralHandler(http.server.CGIHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/get_image"):
            # Parse query parameters
            query = parse_qs(urlparse(self.path).query)
            image_name = query.get("name", [None])[0]

            # Path to the image in central_base
            central_image_path = os.path.join(CENTRAL_BASE, image_name) if image_name else None

            if image_name and os.path.isfile(central_image_path):
                # Serve the requested image
                self.send_response(200)
                self.send_header("Content-type", "image/jpeg")
                self.end_headers()
                with open(central_image_path, "rb") as image_file:
                    self.wfile.write(image_file.read())
            else:
                # Image not found on central server
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>404 Not Found</h1>")
                if image_name:
                    self.wfile.write(f"<p>The image '{image_name}' was not found on the central server.</p>".encode("utf-8"))
        else:
            # Handle other paths
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>404 Not Found</h1>")

# Start the central server
server_address = ("", PORT)
handler = CentralHandler
handler.cgi_directories = ["/"]
httpd = http.server.HTTPServer(server_address, handler)
print(f"Central server active on port {PORT}")
httpd.serve_forever()
