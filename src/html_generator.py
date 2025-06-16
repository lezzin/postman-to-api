from typing import List, Dict
from html import escape
from datetime import datetime
from src.utils import get_file, format_title, get_method_icon


class HTMLGenerator:
    def generate_html_header(self, collection_name: str) -> List[str]:
        return [
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

    def generate_sidebar(self, toc_items: List[Dict[str, str]]) -> List[str]:
        html = ['<div class="sidebar" id="sidebar">']
        
        if toc_items:
            toc_html = self.generate_toc(toc_items)
            html.extend(toc_html)
        else:
            html.append('<div class="toc"><h2>📋 Índice</h2><p>Nenhum item encontrado.</p></div>')
        
        html.append('</div>')
        return html

    def generate_toc(self, toc_items: List[Dict[str, str]]) -> List[str]:
        if not toc_items:
            return []
        
        toc_html = []
        toc_html.append('<h2>📋 Índice</h2>')
        toc_html.append('<input id="search-input" placeholder="🔍 Pesquisar por item..." />')

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
        return toc_html

    def generate_main_content_header(self, collection_name: str) -> List[str]:
        return [
            '<div class="right-content">',
            f"""
            <header class="page-header">
                <h1>
                    <button class='sidebar-toggle' onclick='toggleSidebar()'>☰</button>
                    📚 {collection_name}
                </h1>
                <div>
                    <button onclick="toggleTheme()" class="send-back theme" title="Alternar tema">🌑 Escuro</button>
                    <a href="index.html" class="send-back" title="Voltar ao índice">🏠 Voltar</a>
                </div>
            </header>
            """,
            '<div class="right-content-data">'
        ]

    def generate_meta_info(self, collection_description: str = "", collection_version: str = "") -> List[str]:
        html = ['<div class="meta-info">']
        
        if collection_description:
            desc = collection_description
            if len(desc) > 500:
                desc = desc[:500] + "..."
            html.append(f'<p><strong>Descrição:</strong> {escape(desc)}</p>')
        
        if collection_version:
            html.append(f'<p><strong>Versão:</strong> {escape(collection_version)}</p>')
        
        html.append(f'<p><strong>Gerado em:</strong> {datetime.now().strftime("%d/%m/%Y às %H:%M")}</p>')
        html.append('</div>')
        
        return html

    def generate_html_footer(self) -> List[str]:
        return [
            '</div>',  
            '</div>', 
            '</div>',
            get_file("public/api.js", 'script'),
            "</body>",
            "</html>"
        ]