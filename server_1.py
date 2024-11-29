import http.server
import os
import requests
import json
from urllib.parse import parse_qs

PORT = 8888
CENTRAL_SERVER_URL = "http://localhost:8889/get_image"
SERVER_2_URL = "http://localhost:8887/server_2.py"
SERVER_BASE_1 = "server_base_1"
DB_SIZE_1 = 5
CACHE_TABLE_1 = "cache_table_1.json"

os.makedirs(SERVER_BASE_1, exist_ok=True)

if not os.path.exists(CACHE_TABLE_1):
    with open(CACHE_TABLE_1, "w") as f:
        json.dump({}, f)

class CustomHandler(http.server.BaseHTTPRequestHandler):

    def load_cache_table(self):
        with open(CACHE_TABLE_1, "r") as f:
            return json.load(f)

    def update_cache_table(self, table):
        with open(CACHE_TABLE_1, "w") as f:
            json.dump(table, f)

    def notify_server_2(self, added=None, deleted=None):
        update_data = {"added": added or [], "deleted": deleted or []}
        try:
            response = requests.post(
                SERVER_2_URL.replace("/server_2.py", "") + "/storage_update",
                headers={"Content-Type": "application/json"},
                json=update_data
            )
            print(f"Notify Server 2: {update_data}, Response: {response.status_code}")
        except Exception as e:
            print(f"Error notifying Server 2: {e}")

    def do_POST(self):
        if self.path == "/server_1.py":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            form = parse_qs(post_data)

            image_name = form.get("name", [None])[0]
            if image_name:
                local_image_path = os.path.join(SERVER_BASE_1, image_name)
                server_DB_1 = os.listdir(SERVER_BASE_1)

                if os.path.isfile(local_image_path):
                    self.send_response(200)
                    self.send_header("Content-type", "image/jpeg")
                    self.end_headers()
                    with open(local_image_path, "rb") as image_file:
                        self.wfile.write(image_file.read())
                    print(f"Served image {image_name} from local storage.")
                    return

                cache_table = self.load_cache_table()
                if image_name in cache_table:
                    response = requests.post(SERVER_2_URL, data={"name": image_name})
                    if response.status_code == 200:
                        with open(local_image_path, "wb") as local_image:
                            local_image.write(response.content)
                        self.send_response(200)
                        self.send_header("Content-type", "image/jpeg")
                        self.end_headers()
                        self.wfile.write(response.content)
                        print(f"Retrieved image {image_name} from Server 2.")

                        server_DB_1.append(image_name)
                        if len(server_DB_1) > DB_SIZE_1:
                            file_to_delete = server_DB_1.pop(0)
                            os.remove(os.path.join(SERVER_BASE_1, file_to_delete))
                            self.notify_server_2(deleted=[file_to_delete])
                        self.notify_server_2(added=[image_name])
                        return

                response = requests.get(CENTRAL_SERVER_URL, params={"name": image_name})
                if response.status_code == 200:
                    with open(local_image_path, "wb") as local_image:
                        local_image.write(response.content)
                    self.send_response(200)
                    self.send_header("Content-type", "image/jpeg")
                    self.end_headers()
                    self.wfile.write(response.content)
                    print(f"Retrieved image {image_name} from Central Server.")

                    server_DB_1.append(image_name)
                    if len(server_DB_1) > DB_SIZE_1:
                        file_to_delete = server_DB_1.pop(0)
                        os.remove(os.path.join(SERVER_BASE_1, file_to_delete))
                        self.notify_server_2(deleted=[file_to_delete])
                    self.notify_server_2(added=[image_name])
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Image not found.")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Bad Request: No image name provided.")
        elif self.path == "/storage_update":
            content_length = int(self.headers.get('Content-Length', 0))
            update_data = self.rfile.read(content_length).decode('utf-8')
            try:
                update_data = json.loads(update_data)
                cache_table = self.load_cache_table()

                for added in update_data.get("added", []):
                    cache_table[added] = "server_2"
                for deleted in update_data.get("deleted", []):
                    cache_table.pop(deleted, None)

                self.update_cache_table(cache_table)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Cache table updated.")
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid JSON.")

server_address_1 = ("", PORT)
httpd = http.server.HTTPServer(server_address_1, CustomHandler)
print(f"Server 1 active on port {PORT}")
httpd.serve_forever()
