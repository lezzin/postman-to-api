from typing import Any
from src.utils import is_sensitive_key, is_base64


class ContentProcessor:
    def __init__(self, max_json_length: int, json_start_pattern):
        self.max_json_length = max_json_length
        self.json_start_pattern = json_start_pattern

    def process_content_for_display(self, content: Any, parent_key: str = '') -> Any:
        if isinstance(content, dict):
            return {
                k: self.process_content_for_display(v, k) 
                for k, v in content.items()
            }
        
        elif isinstance(content, list):
            return [
                self.process_content_for_display(item, parent_key) 
                for item in content
            ]
        
        elif isinstance(content, str):
            if is_sensitive_key(parent_key) or is_base64(content) or len(content) > 800:
                return "..."
            return content
        return content