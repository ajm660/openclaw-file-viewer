from flask import Flask, abort, render_template_string, request
import os

app = Flask(__name__)

DATA_DIR = os.environ.get("DATA_DIR", "/data")

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>OpenClaw Viewer</title>

  <script src="https://cdn.tailwindcss.com"></script>

  <script>
    function toggle(id) {
      const el = document.getElementById(id);
      el.classList.toggle("hidden");
    }
  </script>

</head>

<body class="bg-gray-100 text-gray-900">

<div class="max-w-6xl mx-auto p-6">

  <div class="mb-6">
    <h1 class="text-3xl font-bold">📁 OpenClaw File Viewer</h1>
    <p class="text-gray-600">{{ description }}</p>
    
    {% if tree %}
    <div class="mt-4 flex gap-2">
      <a href="/?show_all=false" 
         class="px-4 py-2 rounded {% if not show_all %}bg-blue-600 text-white{% else %}bg-gray-200 text-gray-800 hover:bg-gray-300{% endif %}">
        .md Files Only
      </a>
      <a href="/?show_all=true" 
         class="px-4 py-2 rounded {% if show_all %}bg-blue-600 text-white{% else %}bg-gray-200 text-gray-800 hover:bg-gray-300{% endif %}">
        All Files
      </a>
    </div>
    {% endif %}
  </div>

  {% macro render_tree(tree, path="") %}
    <ul class="ml-4 border-l pl-4">
      {% for name, node in tree.items() %}
        {% set full_path = path + "/" + name if path else name %}

        {% if node is mapping %}
          <li class="mb-2">
            <div onclick="toggle('{{ full_path|replace('/', '_') }}')" 
                 class="cursor-pointer font-semibold text-gray-700 hover:text-black">
              📂 {{ name }}
            </div>

            <div id="{{ full_path|replace('/', '_') }}" class="ml-2 mt-1 hidden">
              {{ render_tree(node, full_path) }}
            </div>
          </li>
        {% else %}
          <li class="mb-1">
            <a href="/view/{{ full_path }}" 
               class="text-blue-600 hover:underline font-mono text-sm">
              📄 {{ name }}
            </a>
          </li>
        {% endif %}
      {% endfor %}
    </ul>
  {% endmacro %}

  {% if tree %}
  <div class="bg-white shadow rounded-2xl p-4">
    <h2 class="text-xl font-semibold mb-4">Files</h2>
    {{ render_tree(tree) }}
  </div>
  {% endif %}

  {% if content %}
  <div class="bg-white shadow rounded-2xl p-6 mt-6">
    
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

def build_tree(base, md_only=True):
    tree = {}

    for root, dirs, files in os.walk(base):
        rel_path = os.path.relpath(root, base)
        parts = [] if rel_path == "." else rel_path.split(os.sep)

        current = tree
        for part in parts:
            current = current.setdefault(part, {})

        for file in files:
            if md_only:
                if file.endswith(".md"):
                    current[file] = None
            else:
                # Show all files, including hidden ones
                current[file] = None

    return tree

@app.route("/")
def index():
    show_all = request.args.get("show_all", "false").lower() == "true"
    md_only = not show_all
    tree = build_tree(DATA_DIR, md_only=md_only)
    
    description = "Browse all files in /data" if show_all else "Browse Markdown files in /data"
    
    return render_template_string(TEMPLATE, tree=tree, content=None, show_all=show_all, description=description)

@app.route("/view/<path:filename>")
def view_file(filename):
    full_path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(full_path):
        abort(404)

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    return render_template_string(
        TEMPLATE,
        tree=None,
        content=content,
        filename=filename
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)