# src/services/embeddings_service.py
import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import numpy as np
import faiss
from src.config.config import get_settings

class EmbeddingsService:
    def __init__(self):
        self.settings = get_settings()
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.index_path = Path("faiss_index")
        self.iso_path = Path("ISO")

    def load_or_create_embeddings(self):
        """Load existing embeddings or create new ones"""
        try:
            # Check if index already exists
            if self.index_path.exists():
                print("Loading existing embeddings...")
                return FAISS.load_local(
                    folder_path=str(self.index_path),
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True  # We trust our own saved embeddings
                )
            
            print("Creating new embeddings...")
            if not self.iso_path.exists():
                raise FileNotFoundError(f"ISO directory not found at {self.iso_path}")
                
            loader = PyPDFDirectoryLoader(str(self.iso_path))
            docs = loader.load()
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            
            documents = text_splitter.split_documents(docs)
            vectors = FAISS.from_documents(documents, self.embeddings)
            
            # Save the vectors to disk
            print(f"Saving embeddings to {self.index_path}...")
            vectors.save_local(str(self.index_path))
            
            return vectors
            
        except Exception as e:
            print(f"Error in embeddings service: {str(e)}")
            raise

    def recreate_embeddings(self, force: bool = False):
        """Force recreation of embeddings"""
        try:
            if self.index_path.exists():
                if not force:
                    raise ValueError("Index already exists. Use force=True to overwrite.")
                import shutil
                shutil.rmtree(self.index_path)
            
            return self.load_or_create_embeddings()
            
        except Exception as e:
            print(f"Error recreating embeddings: {str(e)}")
            raise

