# client.py
# coding: utf-8

print("Content-type: text/html; charset=utf-8\n")

html = """<!DOCTYPE html>
<html>
<head>
    <title>Mon programme</title>
</head>
<body>
    <h1>Entrez le nom de l'image</h1>
    <form action="/server_2.py" method="post">
        <input type="text" name="name" placeholder="Entrez le nom de l'image (ex: image.jpg)" />
        <input type="submit" value="Afficher l'image">
    </form> 
</body>
</html>
"""
print(html)
