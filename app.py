from flask import Flask, abort, render_template_string
import os

app = Flask(__name__)

DATA_DIR = os.environ.get("DATA_DIR", "/data")

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>OpenClaw Viewer</title>

  <!-- Tailwind CDN -->
  <script src="https://cdn.tailwindcss.com"></script>

</head>

<body class="bg-gray-100 text-gray-900">

<div class="max-w-6xl mx-auto p-6">

  <!-- Header -->
  <div class="mb-6">
    <h1 class="text-3xl font-bold">📁 OpenClaw File Viewer</h1>
    <p class="text-gray-600 mt-1">Browse Markdown files in /data</p>
  </div>

  {% if files %}
  <!-- File List -->
  <div class="bg-white shadow rounded-2xl p-4">
    <h2 class="text-xl font-semibold mb-4">Files</h2>

    <ul class="divide-y">
      {% for f in files %}
      <li class="py-2">
        <a href="/view/{{ f }}" class="flex justify-between items-center hover:bg-gray-50 px-2 py-2 rounded-lg">
          <span class="font-mono text-sm text-blue-600">{{ f }}</span>
          <span class="text-xs text-gray-400">→</span>
        </a>
      </li>
      {% endfor %}
    </ul>
  </div>
  {% endif %}

  {% if content %}
  <!-- File Viewer -->
  <div class="bg-white shadow rounded-2xl p-6">
    
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold">{{ filename }}</h2>
      <a href="/" class="text-sm text-blue-500 hover:underline">← Back</a>
    </div>

    <div class="bg-gray-900 text-gray-100 rounded-xl p-4 overflow-x-auto text-sm font-mono whitespace-pre-wrap">
{{ content }}
    </div>

  </div>
  {% endif %}

</div>

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
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)