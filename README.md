# 📘 Postman para Docs da API

Gere automaticamente uma documentação HTML bonita e pesquisável a partir dos seus arquivos JSON de coleção do Postman exportados.

---

## ✨ Recursos

-   **Geração Sem Esforço**: Transforme suas coleções do Postman em documentação HTML limpa com um único comando.
-   **Índice Centralizado**: Um arquivo `index.html` fornece uma visão geral conveniente e links para toda a sua documentação de API gerada.
-   **Navegação Fácil**: Cada coleção do Postman recebe seu próprio arquivo HTML dedicado para uma navegação direta.
-   **Acesso Offline**: Visualize a documentação da sua API localmente sem a necessidade de conexão com a internet.

---

## 🚀 Primeiros Passos

Siga estas etapas simples para configurar e começar a gerar a documentação da sua API.

### Pré-requisitos

Antes de começar, certifique-se de ter:

-   **Python 3.8+**: Baixe e instale-o em [python.org](https://www.python.org/).
-   **Arquivos de Coleção do Postman**: Exporte suas coleções do Postman no formato `.postman_collection.json`.

### Instalação

1.  **Clone o Repositório** (se aplicável, caso contrário, assuma que o usuário já possui os arquivos do projeto):

    ```bash
    git clone https://github.com/lezzin/postman-to-api
    cd postman-to-api
    ```

2.  **Crie um Ambiente Virtual** (recomendado):

    ```bash
    python -m venv .venv
    ```

3.  **Ative o Ambiente Virtual**:

    -   **Windows**:
        ```bash
        .venv\Scripts\activate
        ```
    -   **Linux/macOS**:
        ```bash
        source .venv/bin/activate
        ```

4.  **Instale as Dependências**:
    ```bash
    pip install -r requirements.txt
    ```

---

## 📁 Estrutura do Projeto

Organize os arquivos do seu projeto da seguinte forma:

| Caminho            | Descrição                                                           |
| :----------------- | :------------------------------------------------------------------ |
| `main.py`          | O script principal responsável por gerar a documentação HTML.       |
| `postman/`         | **Coloque todos os seus arquivos `.postman_collection.json` aqui.** |
| `output/`          | Esta pasta conterá todos os arquivos de documentação HTML gerados.  |
| `requirements.txt` | Lista todas as dependências Python necessárias para o projeto.      |

---

## ⚙️ Uso

Uma vez instalado e suas coleções do Postman estiverem no diretório `postman/`, basta executar:

```bash
py main.py
```

Este comando realizará as seguintes ações:

-   Gerará um arquivo `output/index.html`, fornecendo um hub central com links para a documentação de cada uma das suas coleções do Postman.
-   Criará um arquivo `.html` separado para cada `.postman_collection.json` encontrado dentro do diretório `postman/`.

---

## 📝 Exemplo

Digamos que você tenha uma coleção do Postman chamada `minha_api.postman_collection.json` localizada na sua pasta `postman/`. Após executar `py main.py`:

```bash
output/
├── index.html
└── minha_api.html
```

Para visualizar sua documentação gerada, abra o arquivo `index.html` no seu navegador web preferido. Este arquivo fará o link para `minha_api.html` e qualquer outra documentação de coleção que você tenha gerado.
