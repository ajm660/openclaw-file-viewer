from flask import Flask, send_from_directory, abort, render_template_string
import os

app = Flask(__name__)

DATA_DIR = os.environ.get("DATA_DIR", "/data")

port = int(os.environ.get("PORT", 3000))
app.run(host="0.0.0.0", port=port)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>OpenClaw File Viewer</title>
  <style>
    body { font-family: Arial; padding: 20px; }
    a { text-decoration: none; color: blue; }
    pre { background: #f4f4f4; padding: 10px; overflow-x: auto; }
  </style>
</head>
<body>

<h1>📁 OpenClaw File Viewer</h1>

{% if files %}
<ul>
{% for f in files %}
  <li><a href="/view/{{ f }}">{{ f }}</a></li>
{% endfor %}
</ul>
{% endif %}

{% if content %}
<h2>{{ filename }}</h2>
<pre>{{ content }}</pre>
<a href="/">← Back</a>
{% endif %}

</body>
</html>
"""

def list_files(base):
    file_list = []
    for root, dirs, files in os.walk(base):
        for file in files:
            if file.endswith(".md"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base)
                file_list.append(rel_path)
    return sorted(file_list)

@app.route("/")
def index():
    files = list_files(DATA_DIR)
    return render_template_string(TEMPLATE, files=files, content=None)

@app.route("/view/<path:filename>")
def view_file(filename):
    full_path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(full_path):
        abort(404)

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    return render_template_string(
        TEMPLATE,
        files=None,
        content=content,
        filename=filename
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)