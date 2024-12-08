
如何在这个项目中实现通过配置服务器目录， 识别目录中的文件，自动获取不同类型的文件，将文件的内容集成到本地向量数据， 在用户提问过程中，可以自动检索知识并列出引用的文件

我来帮你实现这个功能。主要需要实现以下几个部分:

1. 后端配置文件扫描目录
2. 文件监控和自动导入服务
3. 文件内容提取和向量化
4. 知识检索和引用展示

以下是具体实现方案:

1. 首先在配置文件中添加目录监控配置:

```python:backend/open_webui/config.py
# 添加文件监控配置
DOCUMENT_SCAN_DIRS = PersistentConfig(
    "DOCUMENT_SCAN_DIRS",
    "rag.document_scan_dirs",
    os.environ.get("DOCUMENT_SCAN_DIRS", "").split(","),
)

DOCUMENT_SCAN_INTERVAL = PersistentConfig(
    "DOCUMENT_SCAN_INTERVAL", 
    "rag.document_scan_interval",
    int(os.environ.get("DOCUMENT_SCAN_INTERVAL", "300"))  # 默认5分钟扫描一次
)

# 支持的文件类型配置
SUPPORTED_DOCUMENT_TYPES = {
    "text": [".txt", ".md", ".log"],
    "document": [".pdf", ".doc", ".docx"],
    "spreadsheet": [".xls", ".xlsx", ".csv"],
    "presentation": [".ppt", ".pptx"],
    "code": [".py", ".js", ".java", ".cpp", ".h", ".cs", ".php", ".rb", ".go"]
}
```

2. 创建文件监控服务:

```python:backend/open_webui/services/document_scanner.py
import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ..config import DOCUMENT_SCAN_DIRS, SUPPORTED_DOCUMENT_TYPES
from ..apps.retrieval.loaders.main import known_source_ext
from ..core.vector_store import VECTOR_DB_CLIENT

class DocumentScanner:
    def __init__(self):
        self.observer = Observer()
        self.watch_paths = [path.strip() for path in DOCUMENT_SCAN_DIRS if path.strip()]
        
    def start(self):
        for path in self.watch_paths:
            if os.path.exists(path):
                event_handler = DocumentEventHandler()
                self.observer.schedule(event_handler, path, recursive=True)
                
        self.observer.start()
        # 启动时执行一次完整扫描
        self.scan_all_documents()
        
    def scan_all_documents(self):
        for path in self.watch_paths:
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._is_supported_file(file_path):
                        self._process_document(file_path)
                        
    def _is_supported_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        return (ext in known_source_ext or 
                any(ext in types for types in SUPPORTED_DOCUMENT_TYPES.values()))
                
    def _process_document(self, file_path):
        try:
            # 提取文件内容
            content = self._extract_content(file_path)
            if content:
                # 向量化并存储
                self._vectorize_and_store(file_path, content)
        except Exception as e:
            logging.error(f"处理文件失败 {file_path}: {str(e)}")
            
    def _extract_content(self, file_path):
        # 根据文件类型选择合适的加载器
        loader = self._get_document_loader(file_path)
        if loader:
            docs = loader.load()
            return "\n".join([doc.page_content for doc in docs])
        return None
```

3. 添加文件内容提取和向量化处理:

```python:backend/open_webui/services/document_processor.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from ..core.vector_store import VECTOR_DB_CLIENT

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.embedding_model = OpenAIEmbeddings()
        
    def process_document(self, file_path: str, content: str):
        # 1. 文本分块
        chunks = self.text_splitter.split_text(content)
        
        # 2. 生成向量嵌入
        embeddings = self.embedding_model.embed_documents(chunks)
        
        # 3. 存储到向量数据库
        metadata = {
            "source": file_path,
            "file_name": os.path.basename(file_path),
            "file_type": os.path.splitext(file_path)[1],
            "created_at": time.time()
        }
        
        VECTOR_DB_CLIENT.add_embeddings(
            collection_name="document_store",
            texts=chunks,
            embeddings=embeddings,
            metadatas=[metadata] * len(chunks)
        )
```

4. 实现知识检索服务:

```python:backend/open_webui/services/knowledge_retrieval.py
class KnowledgeRetrieval:
    def __init__(self):
        self.vector_store = VECTOR_DB_CLIENT
        
    async def search_relevant_documents(self, query: str, top_k: int = 3):
        # 搜索相关文档片段
        results = self.vector_store.similarity_search(
            collection_name="document_store",
            query=query,
            k=top_k
        )
        
        # 格式化结果
        references = []
        for doc in results:
            references.append({
                "content": doc.page_content,
                "source": doc.metadata["source"],
                "file_name": doc.metadata["file_name"],
                "relevance_score": doc.metadata.get("score", 0)
            })
            
        return references
```

5. 在聊天接口中集成知识检索:

```python:backend/open_webui/apps/chat/services.py
class ChatService:
    def __init__(self):
        self.knowledge_retrieval = KnowledgeRetrieval()
        
    async def generate_response(self, query: str):
        # 1. 检索相关文档
        relevant_docs = await self.knowledge_retrieval.search_relevant_documents(query)
        
        # 2. 构建提示词
        context = "\n".join([
            f"Reference from {doc['file_name']}:\n{doc['content']}"
            for doc in relevant_docs
        ])
        
        prompt = f"""Based on the following references:
        {context}
        
        Question: {query}
        
        Please provide an answer with citations to the source documents."""
        
        # 3. 调用 LLM 生成回答
        response = await self.llm_service.generate(prompt)
        
        return {
            "answer": response,
            "references": relevant_docs
        }
```

6. 在前端展示引用来源:

```svelte:src/lib/components/chat/Message.svelte
<script>
  export let message;
  export let references = [];
</script>

<div class="message">
  <div class="content">
    {message}
  </div>
  
  {#if references?.length > 0}
    <div class="references">
      <h4>参考来源:</h4>
      {#each references as ref}
        <div class="reference-item">
          <div class="file-name">{ref.file_name}</div>
          <div class="content">{ref.content}</div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .references {
    margin-top: 1rem;
    padding: 1rem;
    background: rgba(0,0,0,0.05);
    border-radius: 0.5rem;
  }
  
  .reference-item {
    margin-top: 0.5rem;
    padding: 0.5rem;
    border-left: 2px solid #666;
  }
</style>
```

使用方法:

1. 配置环境变量:
```bash
DOCUMENT_SCAN_DIRS=/path/to/docs,/another/path
DOCUMENT_SCAN_INTERVAL=300
```

2. 启动文档扫描服务:
```python
# 在应用启动时初始化
document_scanner = DocumentScanner()
document_scanner.start()
```

这样系统就会:
1. 自动扫描配置的目录
2. 识别支持的文件类型
3. 提取文件内容并向量化存储
4. 在用户提问时自动检索相关内容
5. 在回答中展示引用来源

关键代码引用:

1. 文件加载器支持的文件类型:

```26:77:backend/open_webui/apps/retrieval/loaders/main.py
known_source_ext = [
    "go",
    "py",
    "java",
    "sh",
    "bat",
    "ps1",
    "cmd",
    "js",
    "ts",
    "css",
    "cpp",
    "hpp",
    "h",
    "c",
    "cs",
    "sql",
    "log",
    "ini",
    "pl",
    "pm",
    "r",
    "dart",
    "dockerfile",
    "env",
    "php",
    "hs",
    "hsc",
    "lua",
    "nginxconf",
    "conf",
    "m",
    "mm",
    "plsql",
    "perl",
    "rb",
    "rs",
    "db2",
    "scala",
    "bash",
    "swift",
    "vue",
    "svelte",
    "msg",
    "ex",
    "exs",
    "erl",
    "tsx",
    "jsx",
    "hs",
    "lhs",
]
```


2. 向量数据库配置:

```1104:1137:backend/open_webui/config.py
# Qdrant
QDRANT_URI = os.environ.get("QDRANT_URI", None)
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", None)

# OpenSearch
OPENSEARCH_URI = os.environ.get("OPENSEARCH_URI", "https://localhost:9200")
OPENSEARCH_SSL = os.environ.get("OPENSEARCH_SSL", True)
OPENSEARCH_CERT_VERIFY = os.environ.get("OPENSEARCH_CERT_VERIFY", False)
OPENSEARCH_USERNAME = os.environ.get("OPENSEARCH_USERNAME", None)
OPENSEARCH_PASSWORD = os.environ.get("OPENSEARCH_PASSWORD", None)

# Pgvector
PGVECTOR_DB_URL = os.environ.get("PGVECTOR_DB_URL", DATABASE_URL)
if VECTOR_DB == "pgvector" and not PGVECTOR_DB_URL.startswith("postgres"):
    raise ValueError(
        "Pgvector requires setting PGVECTOR_DB_URL or using Postgres with vector extension as the primary database."
    )

####################################
# Information Retrieval (RAG)
####################################

# RAG Content Extraction
CONTENT_EXTRACTION_ENGINE = PersistentConfig(
    "CONTENT_EXTRACTION_ENGINE",
    "rag.CONTENT_EXTRACTION_ENGINE",
    os.environ.get("CONTENT_EXTRACTION_ENGINE", "").lower(),
)

TIKA_SERVER_URL = PersistentConfig(
    "TIKA_SERVER_URL",
    "rag.tika_server_url",
    os.getenv("TIKA_SERVER_URL", "http://tika:9998"),  # Default for sidecar deployment
)
```


3. 文件处理流程:

```885:948:backend/open_webui/apps/retrieval/main.py
@app.post("/process/file")
def process_file(
    form_data: ProcessFileForm,
    user=Depends(get_verified_user),
):
    try:
        file = Files.get_file_by_id(form_data.file_id)

        collection_name = form_data.collection_name

        if collection_name is None:
            collection_name = f"file-{file.id}"

        if form_data.content:
            # Update the content in the file
            # Usage: /files/{file_id}/data/content/update

            VECTOR_DB_CLIENT.delete_collection(collection_name=f"file-{file.id}")

            docs = [
                Document(
                    page_content=form_data.content.replace("<br/>", "\n"),
                    metadata={
                        **file.meta,
                        "name": file.filename,
                        "created_by": file.user_id,
                        "file_id": file.id,
                        "source": file.filename,
                    },
                )
            ]

            text_content = form_data.content
        elif form_data.collection_name:
            # Check if the file has already been processed and save the content
            # Usage: /knowledge/{id}/file/add, /knowledge/{id}/file/update

            result = VECTOR_DB_CLIENT.query(
                collection_name=f"file-{file.id}", filter={"file_id": file.id}
            )

            if result is not None and len(result.ids[0]) > 0:
                docs = [
                    Document(
                        page_content=result.documents[0][idx],
                        metadata=result.metadatas[0][idx],
                    )
                    for idx, id in enumerate(result.ids[0])
                ]
            else:
                docs = [
                    Document(
                        page_content=file.data.get("content", ""),
                        metadata={
                            **file.meta,
                            "name": file.filename,
                            "created_by": file.user_id,
                            "file_id": file.id,
                            "source": file.filename,
                        },
                    )
                ]

            text_content = file.data.get("content", "")
```

