import json, logging, os

from pathlib import Path
from html import escape
from typing import Dict, List, Any
from datetime import datetime

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

class PostmanDocGenerator:
    def __init__(self, output_file: str = "docs.html"):
        self.output_file = output_file
        self.html_output: List[str] = []
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self.logger = logging.getLogger(__name__)
    
    def _get_css_styles(self, file: str) -> str:
        with open(file, 'r', encoding='utf-8') as f:
            return f"<style>{f.read()}</style>"
    
    def _format_json(self, json_data: str) -> str:
        try:
            parsed = json.loads(json_data)
            pretty_json = json.dumps(parsed, indent=2, ensure_ascii=False)
            return highlight(pretty_json, JsonLexer(), HtmlFormatter(nowrap=True))
        except json.JSONDecodeError:
            import html
            return html.escape(json_data)
        
    def _get_status_class(self, status_code: int) -> str:
        if 200 <= status_code < 300:
            return "success"
        elif 400 <= status_code < 500:
            return "warning"
        elif status_code >= 500:
            return "error"
        return ""
    
    def _generate_item_id(self, name: str) -> str:
        return name.lower().replace(" ", "-").replace("/", "-")
    
    def _parse_item(self, item: Dict[str, Any]) -> None:
        try:
            request = item.get("request", {})
            method = request.get("method", "GET")
            url_data = request.get("url", {})
            
            if isinstance(url_data, str):
                url_raw = url_data
            else:
                url_raw = url_data.get("raw", "")
            
            headers = request.get("header", [])
            body_data = request.get("body", {})
            
            body = ""

            if isinstance(body_data, dict):
                if "raw" in body_data:
                    body = body_data["raw"]
                elif "formdata" in body_data:
                    body = body_data["formdata"]
                elif "urlencoded" in body_data:
                    body = body_data["urlencoded"]

            item_name = item.get("name", "Sem nome")
            item_id = self._generate_item_id(item_name)
            
            self.html_output.append(f'<h2 id="{item_id}">{escape(item_name)}</h2>')
            
            self.html_output.append(f'''
                <div class="method-div">
                    <span class="method {method}">{method}</span>
                    <span class="url">{escape(url_raw)}</span>
                </div>
            ''')
            
            description = item.get("request", {}).get("description", "")
            if description:
                self.html_output.append(f'<p><strong>Descrição:</strong> {escape(description)}</p>')
            
            if headers:
                self.html_output.append('<div class="headers">')
                self.html_output.append('<h4>Headers:</h4>')
                self.html_output.append('<ul>')

                for header in headers:
                    key = escape(header.get("key", ""))
                    value = escape(header.get("value", ""))
                    disabled = " (desabilitado)" if header.get("disabled") else ""
                    self.html_output.append(f'<li><strong>{key}:</strong> {value}{disabled}</li>')

                self.html_output.append('</ul>')
                self.html_output.append('</div>')
            
            if body:
                self.html_output.append('<div class="body">')
                self.html_output.append('<h4>Body:</h4>')

                if isinstance(body, str) and body.strip().startswith(('{', '[')):
                    formatted_body = self._format_json(body)
                elif isinstance(body, (dict, list)):
                    import json
                    formatted_body = self._format_json(json.dumps(body, indent=2, ensure_ascii=False))
                else:
                    import html
                    formatted_body = html.escape(str(body))

                self.html_output.append('<pre class="json-highlight">')
                self.html_output.append(formatted_body)  
                self.html_output.append('</pre>')
                self.html_output.append('</div>')
            
            responses = item.get("response", [])
            if responses:
                self.html_output.append('<h3>Respostas de Exemplo:</h3>')
                for response in responses:
                    status_code = response.get("code", 0)
                    status_text = response.get("status", "")
                    status_class = self._get_status_class(status_code)
                    
                    self.html_output.append(f'<h4><span class="status {status_class}">{status_code}</span><span>{escape(status_text)}</span></h4>')
                    
                    response_headers = response.get("header", [])
                    if response_headers:
                        self.html_output.append('<div class="headers">')
                        self.html_output.append('<h4>Headers:</h4>')
                        self.html_output.append('<ul>')
                        for header in response_headers:
                            key = escape(header.get("key", ""))
                            value = escape(header.get("value", ""))
                            self.html_output.append(f'<li><strong>{key}:</strong> {value}</li>')
                        self.html_output.append('</ul>')
                        self.html_output.append('</div>')
                    
                    response_body = response.get("body", "")

                    if response_body:
                        self.html_output.append('<div class="body">')
                        self.html_output.append('<h4>Body:</h4>')

                        if isinstance(response_body, str) and response_body.strip().startswith(('{', '[')):
                            formatted_response = self._format_json(response_body)
                        elif isinstance(response_body, (dict, list)):
                            import json
                            formatted_response = self._format_json(json.dumps(response_body, indent=2, ensure_ascii=False))
                        else:
                            import html
                            formatted_response = html.escape(str(response_body))

                        max_length = 5000
                        if len(response_body) > max_length:
                            formatted_response = formatted_response[:max_length] + "\n..."

                        self.html_output.append(f'<pre class="json-highlight">{formatted_response}</pre>')
                        self.html_output.append('</div>')
            
            self.html_output.append('<hr class="divider">')
            
        except Exception as e:
            self.logger.error(f"Erro ao processar item '{item.get('name', 'Desconhecido')}': {e}")
    
    def _process_items(self, items: List[Dict[str, Any]], level: int = 0) -> List[Dict[str, str]]:
        toc_items = []
        
        for item in items:
            if "item" in item:
                
                folder_name = item.get("name", "Pasta")
                folder_id = self._generate_item_id(folder_name)
                
                toc_items.append({
                    "name": folder_name, 
                    "id": folder_id, 
                    "level": level,
                    "type": "folder"
                })
                
                self.html_output.append(f'<h2 id="{folder_id}" style="margin-top: 40px; color: #2c3e50;">📁 {escape(folder_name)}</h2>')
                
                folder_desc = item.get("description", "")
                if folder_desc:
                    self.html_output.append(f'<p style="font-style: italic; color: #7f8c8d;">{escape(folder_desc)}</p>')
                
                folder_toc = self._process_items(item["item"], level + 1)
                toc_items.extend(folder_toc)
            else:
                item_name = item.get("name", "Sem nome")
                item_id = self._generate_item_id(item_name)
                toc_items.append({"name": item_name, "id": item_id, "level": level, "type": "item"})
                self._parse_item(item)
        
        return toc_items
    
    def _generate_toc(self, toc_items: List[Dict[str, str]]) -> List[str]:
        if not toc_items:
            return []
        
        toc_html = []
        toc_html.append('<div class="toc">')
        toc_html.append('<h2>📋 Índice</h2>')
        toc_html.append('<ul>')
        
        current_folder = None
        for item in toc_items:
            if item.get("type") == "folder":
                if current_folder:
                    toc_html.append('</ul>')
                toc_html.append(f'<li><strong>{escape(item["name"])}</strong></li>')
                toc_html.append('<ul>')
                current_folder = item["name"]
            else:
                indent = "  " * item["level"]
                toc_html.append(f'{indent}<li><a href="#{item["id"]}">{escape(item["name"])}</a></li>')
        
        if current_folder:
            toc_html.append('</ul>')
        
        toc_html.append('</ul>')
        toc_html.append('</div>')
        
        return toc_html
    
    def generate_documentation(self, json_file_path: str) -> None:
        json_path = Path(json_file_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not json_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {json_file_path}")
        
        self.logger.info(f"Carregando coleção: {json_file_path}")
        
        try:
            with open(json_path, "r", encoding="utf-8") as file:
                collection = json.load(file)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Erro ao decodificar JSON: {e}", e.doc, e.pos)
        
        info = collection.get("info", {})
        collection_name = info.get("name", "Documentação da API")
        collection_description = info.get("description", "")
        collection_version = info.get("version", "")
        
        self.html_output = [
            "<!DOCTYPE html>",
            "<html lang='pt-BR'>",
            "<head>",
            "<meta charset='utf-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            f"<title>{escape(collection_name)}</title>",
            self._get_css_styles('src/api.css'),
            "</head>",
            "<body>",
            "<div class='container'>",
            f"""
            <header class="page-header">
                <h1>📚 {escape(collection_name)}</h1>
                <a href="index.html" class="send-back" title="Voltar ao índice">🏠 Voltar</a>
            </header>
            """
        ]
        
        if collection_description or collection_version:
            self.html_output.append('<div class="meta-info">')
            if collection_description:
                self.html_output.append(f'<p><strong>Descrição:</strong> {escape(collection_description)}</p>')
            if collection_version:
                self.html_output.append(f'<p><strong>Versão:</strong> {escape(collection_version)}</p>')
            self.html_output.append(f'<p><strong>Gerado em:</strong> {datetime.now().strftime("%d/%m/%Y às %H:%M")}</p>')
            self.html_output.append('</div>')
        
        items = collection.get("item", [])
        if items:
            
            temp_html = self.html_output.copy()  
            self.html_output = []  
            
            toc_items = self._process_items(items)
            items_html = self.html_output.copy()  
            
            self.html_output = temp_html
            toc_html = self._generate_toc(toc_items)
            self.html_output.extend(toc_html)
            
            self.html_output.extend(items_html)
            
            self.logger.info(f"Processados {len([item for item in toc_items if item.get('type') == 'item'])} endpoints")
        else:
            self.html_output.append("<p>⚠️ Nenhum item encontrado na coleção.</p>")
        
        self.html_output.extend([
            "</div>",
            "</body>",
            "</html>"
        ])
        
        output_path = Path(f"output/{self.output_file}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as file:
            file.write("\n".join(self.html_output))
        
        self.logger.info(f"✅ Documentação gerada com sucesso: {output_path.absolute()}")

    def generate_index(self, generated_docs: list):
        index_path = Path("output/index.html")
        index_path.parent.mkdir(parents=True, exist_ok=True)

        with open(index_path, "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html>\n<html lang='pt-BR'>\n<head>\n")
            f.write("  <meta charset='UTF-8'>\n")
            f.write("  <meta name='viewport' content='width=device-width, initial-scale=1.0'>\n")
            f.write("  <title>Documentação das APIs - Índice</title>\n")
            f.write(self._get_css_styles('src/index.css'))
            f.write("</head>\n<body>\n")
            f.write("<div class='container'>\n")
            f.write("<h1>Documentação das APIs</h1>\n<ul>\n")

            for doc in generated_docs:
                file = escape(doc["file"])
                title = escape(doc["title"])
                f.write(f"<li><a href='{file}' rel='noopener noreferrer'>{title}</a></li>\n")

            f.write("</ul>\n</div>\n</body>\n</html>")

        print(f"✅ Índice gerado em: {index_path}")


def main():
    folder = "postman"
    generated_docs = []

    generator = PostmanDocGenerator()

    for filename in os.listdir(folder):
        if filename.endswith(".postman_collection.json"):
            name = filename.replace(".postman_collection.json", "")
            json_path = os.path.join(folder, filename)
            output_html = f"{name.lower()}.html"

            try:
                generator.output_file = output_html
                generator.generate_documentation(json_path)

                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    title = data.get("info", {}).get("name", name)
                
                generated_docs.append({"file": output_html, "title": title})

                print(f"✅ Gerado: {output_html} a partir de {filename}")

            except FileNotFoundError as e:
                print(f"❌ Arquivo não encontrado: {e}")
            except json.JSONDecodeError as e:
                print(f"❌ Erro no JSON do arquivo {filename}: {e}")
            except Exception as e:
                print(f"❌ Erro inesperado ao processar {filename}: {e}")

    if generated_docs:
        generator.generate_index(generated_docs)


if __name__ == "__main__":
    main()
