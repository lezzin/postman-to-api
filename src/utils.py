import json, base64, os, re

from dotenv import load_dotenv, find_dotenv
from typing import Any
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter
from html import escape

load_dotenv(find_dotenv(), override=True)   

max_key_length = int(os.getenv("MAX_KEY_LENGTH", "1000"))
max_array_items = int(os.getenv("MAX_ARRAY_ITEMS", "5"))

sensitive_keys = {
    key.strip().lower() 
    for key in os.getenv("SENSITIVE_KEYS", "password").split(",")
    if key.strip()
}

base64_pattern = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')

def get_file(file: str, tag: str) -> str:
    with open(file, 'r', encoding='utf-8') as f:
        file_content = f.read()
    return f"<{tag}>{file_content}</{tag}>"

def format_json(json_data: str) -> str:
    try:
        parsed = json.loads(json_data)
        pretty_json = json.dumps(parsed, indent=2, ensure_ascii=False)
        return highlight(pretty_json, JsonLexer(), HtmlFormatter(nowrap=True))
    except json.JSONDecodeError:
        return escape(json_data)
    
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

def is_base64(content: str) -> bool:
    if not isinstance(content, str) or len(content) < 4:
        return False
    
    content = content.strip()
    
    if len(content) % 4 != 0 or len(content) < 100:
        return False
    
    if not base64_pattern.match(content):
        return False
    
    try:
        base64.b64decode(content, validate=True)
        return True
    except:
        return False
        
def truncate_large_content(obj: Any, current_depth: int = 0, max_depth: int = 5) -> Any:
    if current_depth > max_depth:
        return "... (max depth reached)"
    
    if isinstance(obj, dict):
        if len(obj) > 20:  
            limited_obj = dict(list(obj.items())[:10])
            limited_obj["..."] = f"({len(obj) - 10} more items)"
            obj = limited_obj
        
        return {
            k: truncate_large_content(v, current_depth + 1, max_depth) 
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        if len(obj) > max_array_items:
            truncated = obj[:max_array_items]
            truncated.append(f"... ({len(obj) - max_array_items} more items)")
            obj = truncated
        
        return [
            truncate_large_content(item, current_depth + 1, max_depth) 
            for item in obj
        ]
    elif isinstance(obj, str):
        if len(obj) > max_key_length:
            return f"{obj[:100]}... (truncated, {len(obj)} chars total)"
        if is_base64(obj):
            return "..."
        return obj
    
    return obj

def format_title(text: str):
    return text.upper()

def is_sensitive_key(key: str) -> bool:
    key_lower = key.lower()
    return any(sensitive in key_lower for sensitive in sensitive_keys)