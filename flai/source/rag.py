# fleting/flai/utils/rag.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.chains import RetrievalQA
from pathlib import Path
import os

class ProjectRAG:
    def __init__(self, project_root: Path, model_name: str = "phi3:mini"):
        self.project_root = project_root
        self.model_name = model_name
        self.vectorstore = None
        self.qa_chain = None
        
    def load_documents(self):
        """Carrega e processa documentos do projeto"""
        from .scanner import scan_project
        
        documents = []
        files = scan_project(self.project_root)
        
        for file_info in files:
            try:
                with open(file_info["full_path"], 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Criar documento LangChain
                from langchain.docstore.document import Document
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": file_info["path"],
                        "file_type": file_info["extension"],
                        "size": file_info["size"]
                    }
                )
                documents.append(doc)
            except:
                continue
        
        return documents
    
    def create_vectorstore(self):
        """Cria vetorstore com embeddings do Ollama"""
        documents = self.load_documents()
        
        if not documents:
            return None
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        
        # Create embeddings
        embeddings = OllamaEmbeddings(model=self.model_name)
        
        # Create vectorstore
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=str(self.project_root / ".flai_cache")
        )
        
        return self.vectorstore
    
    def create_qa_chain(self):
        """Cria chain de Q&A com contexto do projeto"""
        from langchain_community.llms import Ollama
        from langchain.chains import RetrievalQA
        
        if not self.vectorstore:
            self.create_vectorstore()
        
        llm = Ollama(model=self.model_name, temperature=0.7)
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True
        )
        
        return self.qa_chain
    
    def query(self, question: str) -> dict:
        """Executa query com contexto do projeto"""
        if not self.qa_chain:
            self.create_qa_chain()
        
        # Adicionar contexto ao prompt
        enhanced_prompt = f"""
        Você é um assistente especializado no projeto {self.project_root.name}.
        
        Pergunta: {question}
        
        Baseie sua resposta APENAS nos documentos do projeto.
        Se não encontrar informações relevantes, diga: "Não encontrei informações sobre isso nos arquivos do projeto."
        
        Forneça referências aos arquivos específicos quando possível.
        """
        
        result = self.qa_chain({"query": enhanced_prompt})
        return result