import http.server
import os
import requests
import json
from urllib.parse import parse_qs
import subprocess

subprocess.run(["ip","addr","add","194.0.7.1/24","dev","eth0"])
subprocess.run(["route","add","default","gw","194.0.7.3"])
subprocess.run(["ip","addr","add","194.0.6.2/24","dev","eth1"])
subprocess.run(["route","add","-net","194.0.5.0","netmask","255.255.255.0","gw","194.0.6.1","dev","eth1"])
subprocess.run(["route","add","-net","194.0.2.0","netmask","255.255.255.0","gw","194.0.6.1","dev","eth1"])
PORT = 8888
CENTRAL_SERVER_URL = "http://194.0.2.2:8889/get_image"
SERVER_1_URL = "http://194.0.5.2:8888/server.py"
SERVER_BASE_2 = "server_base_2"
DB_SIZE_2 = 3
CACHE_TABLE_2 = "cache_table_2.json"

os.makedirs(SERVER_BASE_2, exist_ok=True)

if not os.path.exists(CACHE_TABLE_2):
    with open(CACHE_TABLE_2, "w") as f:
        json.dump({}, f)

class CustomHandler(http.server.BaseHTTPRequestHandler):

    server_2_DB = os.listdir(SERVER_BASE_2)

    @classmethod
    def db_init(cls):
        """Initialise the server's database by emptying it if necessary."""
       
        while len(cls.server_2_DB) > 0: 
            file_to_delete = cls.server_2_DB.pop(0)
            os.remove(os.path.join(SERVER_BASE_2, file_to_delete))

        cls.update_cache_table(cls, table={})        
        print("Initial DB state:", cls.server_2_DB)

    def update_FIFO_file_list(self, image_name):
        """If the Database has reached the maximum number of files stored given by DB_SIZE_1, the oldest file 
        according to our strategy is deleted from the FIFO list and the server.
        Arguments : None
        Return : None
        """
        self.server_2_DB.insert(0, image_name)
        if len(self.server_2_DB) > DB_SIZE_2:
            file_to_delete = self.server_2_DB.pop(DB_SIZE_2) #Removes exceeding file name from list
            print("Deleting "+ str(file_to_delete)+"from Server 2 DataBase.")
            os.remove( os.path.join(SERVER_BASE_2, file_to_delete))
            self.notify_server_1(deleted=[file_to_delete])

        print("Updated FIFO list:", self.server_2_DB)

    def load_cache_table(self):
        with open(CACHE_TABLE_2, "r") as f:
            return json.load(f)

    def update_cache_table(self, table):
        with open(CACHE_TABLE_2, "w") as f:
            json.dump(table, f)

    def notify_server_1(self, added=None, deleted=None, init=False):
        update_data = {"added": added or [], "deleted": deleted or [], "init": init}
        try:
            response = requests.post(
                SERVER_1_URL.replace("/server.py", "") + "/storage_update",
                headers={"Content-Type": "application/json"},
                json=update_data
            )
            print(f"Notify Server 1: {update_data}, Response: {response.status_code}")
        except Exception as e:
            print(f"Error notifying Server 1: {e}")
    
    def do_GET(self):
        if self.path == "/client.py":  # Adjust the path to match your request
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            with open("client_2.py", "r", encoding="utf-8") as client_file:
                self.wfile.write(client_file.read().encode("utf-8"))
            
        elif self.path == "/server.py/ping":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Pong from server B")
            print(self.server_2_DB)
            #self.notify_server_1(added=self.server_2_DB, init=True)

        else:   
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found.")

    def do_POST(self):

        if self.path == "/server.py":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            form = parse_qs(post_data)

            image_name = form.get("name", [None])[0]
            if image_name:
                print(f"Request from {self.client_address[0]} for {image_name}")
                local_image_path = os.path.join(SERVER_BASE_2, image_name)
                #server_DB_2 = os.listdir(SERVER_BASE_2)

                if os.path.isfile(local_image_path):
                    print("\tImage ", image_name, " exists locally.")
                    self.send_response(200)
                    self.send_header("Content-type", "image/jpeg")
                    self.end_headers()
                    with open(local_image_path, "rb") as image_file:
                        self.wfile.write(image_file.read())
                    self.server_2_DB.insert(0, self.server_2_DB.pop(self.server_2_DB.index(image_name))) #updates FIFO list
                    print("\tFiles present in the caching server after serving the request:", self.server_2_DB)
                    print(f"\tServed image {image_name} from local storage.")
                    return

                cache_table = self.load_cache_table()
                if image_name in cache_table:
                    print(f"\tRequesting {image_name} from Server 1.")
                    response = requests.post(SERVER_1_URL, data={"name": image_name})
                    if response.status_code == 200:
                        with open(local_image_path, "wb") as local_image:
                            local_image.write(response.content)
                        self.send_response(200)
                        self.send_header("Content-type", "image/jpeg")
                        self.end_headers()
                        self.wfile.write(response.content)
                        print(f"\tRetrieved image {image_name} from Server 1.")

                        self.update_FIFO_file_list(image_name)
                        self.notify_server_1(added=[image_name])
                        return
                print(f"\tRequesting {image_name} from Central Server.")
                response = requests.get(CENTRAL_SERVER_URL, params={"name": image_name})
                if response.status_code == 200:
                    with open(local_image_path, "wb") as local_image:
                        local_image.write(response.content)
                    self.send_response(200)
                    self.send_header("Content-type", "image/jpeg")
                    self.end_headers()
                    self.wfile.write(response.content)
                    print(f"\tRetrieved image {image_name} from Central Server.")

                    self.update_FIFO_file_list(image_name)
                    self.notify_server_1(added=[image_name])
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Image not found.")
                    print(f"\tImage {image_name} could not be found in Central Server.")
            else:
                print(f"Bad request from {self.client_address[0]}")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Bad Request: No image name provided.")

        elif self.path == "/storage_update":
            content_length = int(self.headers.get('Content-Length', 0))
            update_data = self.rfile.read(content_length).decode('utf-8')
            try:
                print(f"Updating cache table from {self.client_address[0]}")
                update_data = json.loads(update_data)
                cache_table = self.load_cache_table()

                if update_data.get("init"):
                    cache_table.clear()
                for added in update_data.get("added", []):
                    cache_table[added] = "server_1"
                for deleted in update_data.get("deleted", []):
                    cache_table.pop(deleted, None)


                self.update_cache_table(cache_table)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Cache table updated.")
                print(f"\tCache table updated, {cache_table}")
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid JSON.")

server_address_2 = ("", PORT)
httpd = http.server.HTTPServer(server_address_2, CustomHandler)
print(f"Server 2 active on port {PORT}")
CustomHandler.db_init()
httpd.serve_forever()
