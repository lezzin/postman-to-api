import json

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

def get_css_styles(file: str) -> str:
    with open(file, 'r', encoding='utf-8') as f:
        css_content = f.read()
    return f"<style>{css_content}</style>"

def format_json(json_data: str) -> str:
    try:
        parsed = json.loads(json_data)
        pretty_json = json.dumps(parsed, indent=2, ensure_ascii=False)
        return highlight(pretty_json, JsonLexer(), HtmlFormatter(nowrap=True))
    except json.JSONDecodeError:
        import html
        return html.escape(json_data)
    
def generate_item_id(name: str) -> str:
    return name.lower().replace(" ", "-").replace("/", "-")

def get_status_class(status_code: int) -> str:
    if 200 <= status_code < 300:
        return "success"
    elif 400 <= status_code < 500:
        return "warning"
    elif status_code >= 500:
        return "error"
    return ""

def get_method_icon(method: str) -> str:
    icons = {
        "GET": "🔍",
        "POST": "📝",
        "PUT": "✏️",
        "DELETE": "🗑️",
        "PATCH": "🔧",
        "HEAD": "👀",
        "OPTIONS": "⚙️"
    }

    return icons.get(method.upper(), "📡")