from flask import Flask, abort, render_template_string, request, redirect, url_for, jsonify
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
          <li class="mb-1 flex items-center gap-2">
            <a href="/view/{{ full_path }}" 
               class="text-blue-600 hover:underline font-mono text-sm">
              📄 {{ name }}
            </a>
            <a href="/edit/{{ full_path }}" 
               class="text-xs text-green-600 hover:text-green-800 hover:underline">
              ✏️ Edit
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
      <div class="flex gap-2">
        <a href="/edit/{{ filename }}" class="text-sm text-green-600 hover:text-green-800 hover:underline">✏️ Edit</a>
        <a href="/" class="text-sm text-blue-500 hover:underline">← Back</a>
      </div>
    </div>

    <div class="bg-gray-900 text-gray-100 rounded-xl p-4 overflow-x-auto text-sm font-mono whitespace-pre-wrap">
{{ content }}
    </div>

  </div>
  {% endif %}

  {% if edit_mode %}
  <div class="bg-white shadow rounded-2xl p-6 mt-6">
    
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold">Editing: {{ filename }}</h2>
      <div class="flex gap-2">
        <a href="/view/{{ filename }}" class="text-sm text-blue-500 hover:underline">👁️ View</a>
        <a href="/" class="text-sm text-gray-500 hover:underline">← Back</a>
      </div>
    </div>

    <form method="POST" action="/save/{{ filename }}">
      <div class="mb-4">
        <textarea name="content" 
                  class="w-full h-96 bg-gray-900 text-gray-100 rounded-xl p-4 text-sm font-mono border-0 resize-y focus:ring-2 focus:ring-blue-500"
                  placeholder="File content...">{{ content }}</textarea>
      </div>
      
      <div class="flex gap-2">
        <button type="submit" 
                class="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 focus:ring-2 focus:ring-green-500">
          💾 Save Changes
        </button>
        <a href="/view/{{ filename }}" 
           class="px-6 py-2 bg-gray-500 text-white rounded hover:bg-gray-600">
          Cancel
        </a>
      </div>
    </form>

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

@app.route("/edit/<path:filename>")
def edit_file(filename):
    full_path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(full_path):
        abort(404)

    # Security check: ensure the file is within DATA_DIR
    if not os.path.abspath(full_path).startswith(os.path.abspath(DATA_DIR)):
        abort(403)

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    return render_template_string(
        TEMPLATE,
        tree=None,
        content=content,
        filename=filename,
        edit_mode=True
    )

@app.route("/save/<path:filename>", methods=["POST"])
def save_file(filename):
    full_path = os.path.join(DATA_DIR, filename)

    # Security check: ensure the file is within DATA_DIR
    if not os.path.abspath(full_path).startswith(os.path.abspath(DATA_DIR)):
        abort(403)

    content = request.form.get("content", "")

    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        # In a real app, you'd want better error handling
        abort(500)

    return redirect(url_for("view_file", filename=filename))

@app.route("/api/save/<path:filename>", methods=["POST"])
def api_save_file(filename):
    full_path = os.path.join(DATA_DIR, filename)

    if not os.path.abspath(full_path).startswith(os.path.abspath(DATA_DIR)):
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json(silent=True)
    if data is not None:
        content = data.get("content", "")
    else:
        content = request.form.get("content", "")

    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"success": True, "filename": filename})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)