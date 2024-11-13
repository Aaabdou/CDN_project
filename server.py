# server.py
import http.server
import cgitb
import cgi
import os
import sys

# Enable debugging
cgitb.enable()

PORT = 8888

class CustomHandler(http.server.CGIHTTPRequestHandler):
    def do_POST(self):
        # Only handle requests to this script for image serving
        if self.path == "/server.py":
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
            image_name = form.getvalue("name")

            # Check if the image file exists in the current directory
            if image_name and os.path.isfile(image_name):
                # Serve the image if it exists
                self.send_response(200)
                self.send_header("Content-type", "image/jpeg")
                self.end_headers()
                with open(image_name, "rb") as image_file:
                    self.wfile.write(image_file.read())
            else:
                # Send 404 error if the image doesn't exist
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>404 Not Found</h1>")
                self.wfile.write(f"<p>L'image '{image_name}' n'existe pas sur le serveur.</p>".encode("utf-8"))
        else:
            # Handle other POST requests if needed
            super().do_POST()

# Set up the server to handle CGI scripts
server_address = ("", PORT)
handler = CustomHandler
handler.cgi_directories = ["/"]

print(f"Serveur actif sur le port : {PORT}")

httpd = http.server.HTTPServer(server_address, handler)
httpd.serve_forever()
