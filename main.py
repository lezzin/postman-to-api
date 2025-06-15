import json, logging, os, re, markdown

from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from html import escape
from typing import Dict, List, Any
from datetime import datetime
from src.utils import *

load_dotenv(find_dotenv(), override=True)   

class PostmanDocGenerator:
    def __init__(self, output_file: str = "docs.html"):
        self.output_file = output_file
        self.html_output: List[str] = []
        self._setup_logging()
        
        self.max_responses = int(os.getenv("MAX_RESPONSES", "2"))
        self.max_json_length = int(os.getenv("MAX_JSON_LENGTH", "5000"))

        self.json_start_pattern = re.compile(r'^\s*[{\[]')
    
    def _setup_logging(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _process_content_for_display(self, content: Any, parent_key: str = '') -> Any:
        if isinstance(content, dict):
            return {
                k: self._process_content_for_display(v, k) 
                for k, v in content.items()
            }
        
        elif isinstance(content, list):
            return [
                self._process_content_for_display(item, parent_key) 
                for item in content
            ]
        
        elif isinstance(content, str):
            if is_sensitive_key(parent_key) or is_base64(content) or len(content) > 800:
                return "..."
            return content
        return content

    def _render_json_block(self, content: Any, type: str, max_length: int = None):
        if not max_length:
            max_length = self.max_json_length
            
        if not content:
            self.html_output.append('<div class="headers">')
            self.html_output.append(f'<h4>{type.capitalize()} body:</h4>')
            self.html_output.append('<ul><li>Nenhum conteúdo no corpo da requisição/resposta.</li></ul>')
            self.html_output.append('</div>')
            return
        
        try:
            processed_content = self._process_content_for_display(content)
            processed_content = truncate_large_content(processed_content)
            
            if isinstance(content, str):
                content_str = content.strip()
                
                if self.json_start_pattern.match(content_str):
                    try:
                        parsed_json = json.loads(content_str)
                        processed_json = self._process_content_for_display(parsed_json)
                        processed_json = truncate_large_content(processed_json)
                        formatted = format_json(json.dumps(processed_json, indent=2, ensure_ascii=False))
                    except json.JSONDecodeError:
                        
                        if is_base64(content_str):
                            formatted = "..."
                        else:
                            formatted = escape(content_str[:max_length] + ("..." if len(content_str) > max_length else ""))
                else:
                    if content_str.startswith('PK'):
                        formatted = escape('Arquivo ZIP com vários CSVs')
                    elif is_base64(content_str):
                        formatted = "..."
                    else:
                        formatted = escape(content_str[:max_length] + ("..." if len(content_str) > max_length else ""))
            
            elif isinstance(content, (dict, list)):
                formatted = format_json(json.dumps(processed_content, indent=2, ensure_ascii=False))
            
            else:
                content_str = str(content)
                formatted = escape(content_str[:max_length] + ("..." if len(content_str) > max_length else ""))

            self.html_output.append('<div class="body">')
            self.html_output.append(f'<h4>{type.capitalize()} body:</h4>')
            self.html_output.append(f'<pre class="json-highlight">{formatted}</pre>')
            self.html_output.append('</div>')
            
        except Exception as e:
            self.logger.warning(f"Error processing {type} content: {e}")
            self.html_output.append('<div class="body">')
            self.html_output.append(f'<h4>{type.capitalize()} body:</h4>')
            self.html_output.append('<p class="error">Error processing content</p>')
            self.html_output.append('</div>')

    def _parse_item(self, item: Dict[str, Any]) -> None:
        try:
            query_params = ""
            request = item.get("request", {}) 
            method = request.get("method", "GET")
            url_data = request.get("url", {})

            if isinstance(url_data, str):
                if not url_data: return     
                url_raw = url_data
            else:
                url_raw = url_data.get("raw", "") or ""
                if not url_raw: return

                query_params = url_data.get("query", [])
                for param in query_params: 
                    param.pop("value", None)

            headers = request.get("header", [])
            body_data = request.get("body", {})

            url_raw = url_raw if not query_params else url_raw.split("?")[0]

            body = ""
            if isinstance(body_data, dict):
                if "raw" in body_data:
                    body = body_data["raw"]
                elif "formdata" in body_data:
                    body = body_data["formdata"]
                elif "urlencoded" in body_data:
                    body = body_data["urlencoded"]
                    for param in body: 
                        param.pop("value", None)

            item_name = item.get("name", "Sem nome")
            item_id = generate_item_id(item_name)

            self.html_output.append(f'<h2 id="{item_id}">{escape(item_name)}</h2>')

            self.html_output.append(f'''
                <div class="method-div">
                    <span class="method {method}">{method}</span>
                    <span class="url">{escape(url_raw)}</span>
                </div>
            ''')

            description = item.get("request", {}).get("description", "")
            if description:
                html_description = markdown.markdown(description)
                self.html_output.append(f'<div class="description">{html_description}</div>')
            
            if headers:
                self.html_output.append('<div class="headers">')
                self.html_output.append('<h4>Headers:</h4>')
                self.html_output.append('<ul>')

                for header in headers:
                    key = escape(header.get("key", ""))
                    value = escape(header.get("value", ""))
                    disabled = " (desabilitado)" if header.get("disabled") else ""
                    
                    display_value = str(value).split(" ")[0]
                    if len(display_value) > 50:
                        display_value = display_value[:50] + "..."
                    self.html_output.append(f'<li><strong>{key}:</strong> {display_value}{disabled}</li>')

                self.html_output.append('</ul>')
                self.html_output.append('</div>')

            body = body if not query_params else query_params
            self._render_json_block(body, 'request')
            
            responses = item.get("response", [])
            if responses:
                limited_responses = responses[:self.max_responses]
                total_responses = len(responses)
                
                self.html_output.append('<h3>Respostas de Exemplo:</h3>')
                
                if total_responses > self.max_responses:
                    self.html_output.append(f'<p class="info">Mostrando {self.max_responses} de {total_responses} respostas disponíveis.</p>')
                
                for response in limited_responses:
                    status_code = response.get("code", 0)
                    status_text = response.get("status", "")
                    status_class = get_status_class(status_code)
                    
                    self.html_output.append(f'<h4 class="status-div"><span class="status {status_class}">{status_code}</span><span>{escape(status_text)}</span></h4>')
                    
                    response_headers_whitelist = [
                        h.strip().lower() 
                        for h in os.getenv("REQUEST_HEADERS_WHITELIST", "").split(",") 
                        if h.strip()
                    ]
                    response_headers = response.get("header", [])

                    if response_headers and response_headers_whitelist:
                        self.html_output.append('<div class="headers">')
                        self.html_output.append('<h4>Headers:</h4>')
                        self.html_output.append('<ul>')

                        for header in response_headers:
                            key = header.get("key", "")
                            if str(key).lower() in response_headers_whitelist:
                                key_escaped = escape(key)
                                value_escaped = escape(header.get("value", ""))
                                
                                if len(value_escaped) > 100:
                                    value_escaped = value_escaped[:100] + "..."
                                self.html_output.append(f'<li><strong>{key_escaped}:</strong> {value_escaped}</li>')

                        self.html_output.append('</ul>')
                        self.html_output.append('</div>')
                    
                    response_body = response.get("body", "")
                    if response_body:
                        self._render_json_block(response_body, 'response')
            
            self.html_output.append('<hr class="divider">')
            
        except Exception as e:
            self.logger.error(f"Erro ao processar item '{item.get('name', 'Desconhecido')}': {e}")
    
    def _process_items(self, collection: Dict[str, Any], items: List[Dict[str, Any]], level: int = 0) -> List[Dict[str, str]]:
        collection_items = collection.get("item", [])
        toc_items = []

        for item in items:
            try:
                has_children = "item" in item and isinstance(item["item"], list)
                folder_name = item.get("name", "Pasta")

                is_folder = any(ci.get("name") == folder_name for ci in collection_items)

                if is_folder:
                    folder_id = generate_item_id(folder_name)

                    toc_items.append({
                        "is_empty": False,
                        "name": folder_name,
                        "id": folder_id,
                        "level": level,
                        "type": "folder",
                        "method": item.get("request", {}).get("method", None)
                    })

                    if not item.get("request"):
                        self.html_output.append(
                            f'<h2 id="{folder_id}" class="folder-name">📁 {escape(folder_name)}</h2>'
                        )

                    folder_desc = item.get("description", "")
                    if folder_desc:
                        if len(folder_desc) > 500:
                            folder_desc = folder_desc[:500] + "..."
                        self.html_output.append(
                            f'<p>{escape(folder_desc)}</p>'
                        )

                    if has_children:
                        folder_toc = self._process_items(collection, item["item"], level + 1)
                        toc_items.extend(folder_toc)

                    if item.get("request"):
                        self._parse_item(item)

                else:
                    item_name = item.get("name", "Sem nome")
                    item_id = generate_item_id(item_name)
                    url_data = item.get("request", {}).get("url", {})

                    if isinstance(url_data, str):
                        is_empty = not url_data.strip()
                    else:
                        url_raw = url_data.get("raw", "") or ""
                        is_empty = not url_raw.strip()

                    toc_items.append({
                        "is_empty": is_empty,
                        "name": item_name,
                        "id": item_id,
                        "level": level,
                        "type": "item",
                        "method": item.get("request", {}).get("method", None)
                    })

                    self._parse_item(item)
                    
            except Exception as e:
                self.logger.error(f"Error processing item: {e}")
                continue

        return toc_items

    def _generate_toc(self, toc_items: List[Dict[str, str]]) -> List[str]:
        if not toc_items:
            return []
        
        toc_html = []
        toc_html.append('<div class="toc">')
        toc_html.append('<h2>📋 Índice</h2>')

        current_level = 0
        toc_html.append('<ul class="toc-list">') 

        for item in toc_items:
            level = item.get("level", 0)
            name = escape(item.get("name", ""))
            item_id = item.get("id", "")
            item_type = item.get("type", "item")
            method = item.get("method", "default") if item.get("method") is not None else "default"
            is_empty = item.get("is_empty")

            if is_empty: 
                continue

            while current_level < level:
                toc_html.append('  ' * current_level + '<ul>')
                current_level += 1

            while current_level > level:
                current_level -= 1
                toc_html.append('  ' * current_level + '</ul>')

            if item_type == "folder":
                toc_html.append('  ' * current_level + f'<li><a href="#{item_id}">📁 {format_title(name)}</a></li>')
            else:
                method_icon = get_method_icon(method)
                toc_html.append('  ' * current_level + f'<li class="item"><a href="#{item_id}">{method_icon} {format_title(name)}</a></li>')

        while current_level > 0:
            current_level -= 1
            toc_html.append('  ' * current_level + '</ul>')

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
        collection_name = str(escape(info.get("name", 'API'))).capitalize()
        collection_description = info.get("description", "")
        collection_version = info.get("version", "")
        
        self.html_output = [
            "<!DOCTYPE html>",
            "<html lang='pt-BR'>",
            "<head>",
            "<meta charset='utf-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            f"<title>Documentação das APIs - {collection_name}</title>",
            get_file('public/api.css', 'style'),
            "</head>",
            "<body>",
            "",
            "<div class='main-layout'>",
        ]
        
        items = collection.get("item", [])
        toc_items = []
        content_html = []
        
        if items:
            temp_html = []
            self.html_output = temp_html 
            
            toc_items = self._process_items(collection, items)
            content_html = self.html_output.copy()
            
            self.html_output = [
                "<!DOCTYPE html>",
                "<html lang='pt-BR'>",
                "<head>",
                "<meta charset='utf-8'>",
                "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
                f"<title>Documentação das APIs - {collection_name}</title>",
                get_file('public/api.css', 'style'),
                "</head>",
                "<body>",
                "<div class='main-layout'>",
            ]
        
        self.html_output.append('<div class="sidebar" id="sidebar">')
        if toc_items:
            toc_html = self._generate_toc(toc_items)
            self.html_output.extend(toc_html)
        else:
            self.html_output.append('<div class="toc"><h2>📋 Índice</h2><p>Nenhum item encontrado.</p></div>')
        self.html_output.append('</div>')
        
        self.html_output.append('<div class="right-content">')
        
        self.html_output.append(f"""
        <header class="page-header">
            <h1>
                <button class='sidebar-toggle' onclick='toggleSidebar()'>☰</button>
                📚 {collection_name}
            </h1>
            <div>
                <button onclick="toggleTheme(this)" class="send-back theme" title="Alternar tema">🌑 Escuro</button>
                <a href="index.html" class="send-back" title="Voltar ao índice">🏠 Voltar</a>
            </div>
        </header>
        """)

        self.html_output.append('<div class="right-content-data">')
        
        if collection_description or collection_version:
            self.html_output.append('<div class="meta-info">')
            if collection_description:
                
                desc = collection_description
                if len(desc) > 500:
                    desc = desc[:500] + "..."
                self.html_output.append(f'<p><strong>Descrição:</strong> {escape(desc)}</p>')
            if collection_version:
                self.html_output.append(f'<p><strong>Versão:</strong> {escape(collection_version)}</p>')
            self.html_output.append(f'<p><strong>Gerado em:</strong> {datetime.now().strftime("%d/%m/%Y às %H:%M")}</p>')
            self.html_output.append('</div>')
        
        
        if content_html:
            self.html_output.extend(content_html)
            endpoint_count = len([item for item in toc_items if item.get('type') == 'item'])
            self.logger.info(f"Processados {endpoint_count} endpoints")
        else:
            self.html_output.append("<p>⚠️ Nenhum item encontrado na coleção.</p>")
        
        self.html_output.append('</div>')  
        self.html_output.append('</div>')
        self.html_output.append('</div>')
        
        self.html_output.append(get_file("public/api.js", 'script'))
        
        self.html_output.extend([
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

        try:
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("<!DOCTYPE html>\n<html lang='pt-BR'>\n<head>\n")
                f.write("  <meta charset='UTF-8'>\n")
                f.write("  <meta name='viewport' content='width=device-width, initial-scale=1.0'>\n")
                f.write("  <title>Documentação das APIs - Índice</title>\n")
                f.write(get_file('public/index.css', 'style'))
                f.write(get_file("public/api.js", 'script'))
                f.write("</head>\n<body>\n")
                f.write("<div class='container'>\n")
                f.write("<h1>Documentação das APIs</h1>\n<ul>\n")

                for doc in generated_docs:
                    file = escape(doc["file"])
                    title = escape(doc["title"])
                    f.write(f"<li><a href='{file}' rel='noopener noreferrer'>📁 {title}</a></li>\n")

                f.write("</ul>\n</div>\n</body>\n</html>")

            print(f"✅ Índice gerado em: {index_path}")
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar índice: {e}")

def main():
    folder = os.getenv("POSTMAN_FOLDER", "postman")
    generated_docs = []

    if not os.path.exists(folder):
        print(f"❌ Pasta não encontrada: {folder}")
        return

    generator = PostmanDocGenerator()
    collection_files = [f for f in os.listdir(folder) if f.endswith(".postman_collection.json")]
    
    if not collection_files:
        print(f"❌ Nenhum arquivo de coleção encontrado em: {folder}")
        return

    print(f"📁 Processando {len(collection_files)} coleções...")

    for filename in collection_files:
        start_time = datetime.now()
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
            
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"✅ Gerado: {output_html} a partir de {filename} ({processing_time:.2f}s)")

        except FileNotFoundError as e:
            print(f"❌ Arquivo não encontrado: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ Erro no JSON do arquivo {filename}: {e}")
        except Exception as e:
            print(f"❌ Erro inesperado ao processar {filename}: {e}")

    if generated_docs:
        generator.generate_index(generated_docs)
        print(f"🎉 Processamento concluído! {len(generated_docs)} documentações geradas.")
    else:
        print("❌ Nenhuma documentação foi gerada.")

if __name__ == "__main__":
    main()