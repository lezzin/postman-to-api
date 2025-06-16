import os
import json
from datetime import datetime
from postman_doc_generator import PostmanDocGenerator

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