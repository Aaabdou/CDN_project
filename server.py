# server.py
import http.server
import cgi
import os
import requests  # To request images from central_server.py
import cgitb
import sys

cgitb.enable()

PORT = 8888
CENTRAL_SERVER_URL = "http://localhost:8889/get_image"  # URL for the central server
SERVER_BASE = "server_base"  # Directory to store images locally
DB_SIZE = 5

# Ensure the server_base directory exists
os.makedirs(SERVER_BASE, exist_ok=True)

class CustomHandler(http.server.CGIHTTPRequestHandler):

    server_DB = os.listdir(SERVER_BASE)

    def do_POST(self):
        print("Fichiers présents dans le serveur replica avant requête:", self.server_DB)
        if self.path == "/server.py":
            # Handle form submission
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
            image_name = form.getvalue("name")
            
            if image_name:
                # Path to the local image in server_base
                local_image_path = os.path.join(SERVER_BASE, image_name)

                # Check if image exists locally
                if os.path.isfile(local_image_path):
                    # Serve the local image
                    self.send_response(200)
                    self.send_header("Content-type", "image/jpeg")
                    self.end_headers()
                    with open(local_image_path, "rb") as image_file:
                        self.wfile.write(image_file.read())
                    self.server_DB.insert(0, self.server_DB.pop(self.server_DB.index(image_name))) #updates list
                    print("Fichiers présents dans le serveur replica après requête:", self.server_DB)

                    
                else:
                    # Fetch image from central server
                    response = requests.get(CENTRAL_SERVER_URL, params={"name": image_name})
                    if response.status_code == 200:
                        # Save the image locally and send it to the client
                        with open(local_image_path, "wb") as local_image:
                            local_image.write(response.content)
                        self.send_response(200)
                        self.send_header("Content-type", "image/jpeg")
                        self.end_headers()
                        self.wfile.write(response.content)
                        #updates list and repertory
                        self.server_DB.insert(0, image_name)
                        try :
                            file_to_delete = self.server_DB.pop(DB_SIZE)
                            print("Deleting "+ str(file_to_delete))
                            print("Fichiers présents dans le serveur replica après requête:", self.server_DB)
                        except IndexError :
                            print("Moins de ", DB_SIZE," images dans la serveur replica")
                            return
                        os.remove( os.path.join(SERVER_BASE, file_to_delete))
                        

                    else:
                        # If central server also doesn't have the image
                        self.send_response(404)
                        self.send_header("Content-type", "text/html")
                        self.end_headers()
                        self.wfile.write(b"<h1>404 Not Found</h1>")
                        self.wfile.write(f"<p>The image '{image_name}' was not found locally or on the central server.</p>".encode("utf-8"))
            else:
                # No image name provided
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>400 Bad Request</h1>")
                self.wfile.write(b"<p>No image name was provided.</p>")
        else:
            super().do_POST()



# Start the server
server_address = ("", PORT)
handler = CustomHandler
handler.cgi_directories = ["/"]
httpd = http.server.HTTPServer(server_address, handler)
print(f"Server active on port {PORT}")
httpd.serve_forever()
