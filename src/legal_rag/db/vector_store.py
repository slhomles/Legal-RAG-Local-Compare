import os
from typing import List, Dict, Any
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma

# Import cáº¥u hÃ¬nh
from legal_rag.config import CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME

class VectorStoreManager:
    """
    Module quáº£n lÃ½ cÆ¡ sá»Ÿ dá»¯ liá»‡u Vector (ChromaDB) vÃ  Embeddings (BGE-M3)
    """
    
    def __init__(self):
        # 1. Khá»Ÿi táº¡o mÃ´ hÃ¬nh Embedding
        print(f"[*] Äang táº£i mÃ´ hÃ¬nh nhÃºng {EMBEDDING_MODEL_NAME}...")
        
        # Thiáº¿t láº­p mÃ´ hÃ¬nh BGE-M3 phÃ¹ há»£p cho tiáº¿ng Viá»‡t
        model_kwargs = {'device': 'cpu'} # Äá»•i thÃ nh 'cuda' náº¿u cÃ³ GPU Ä‘á»ƒ cháº¡y nhanh hÆ¡n
        encode_kwargs = {'normalize_embeddings': True} # Quan trá»ng Ä‘á»ƒ tÃ­nh toÃ¡n khoáº£ng cÃ¡ch vector chÃ­nh xÃ¡c
        
        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
        print("[+] Khá»Ÿi táº¡o Embedding Model thÃ nh cÃ´ng.")
        
        # 2. Khá»Ÿi táº¡o káº¿t ná»‘i Ä‘áº¿n ChromaDB (LÆ°u trá»¯ cá»¥c bá»™)
        print(f"[*] Káº¿t ná»‘i Ä‘áº¿n ChromaDB táº¡i: {CHROMA_DB_DIR}")
        self.vector_db = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=str(CHROMA_DB_DIR) # Ã‰p kiá»ƒu sang chuá»—i Ä‘á»ƒ trÃ¡nh lá»—i Ä‘Æ°á»ng dáº«n
        )
        print("[+] Káº¿t ná»‘i Vector DB thÃ nh cÃ´ng.")

    def add_documents(self, chunks: List[Dict[str, Any]]):
        """
        Nháº­n danh sÃ¡ch chunks, nhÃºng thÃ nh vector vÃ  lÆ°u vÃ o ChromaDB.
        """
        if not chunks:
            print("[!] KhÃ´ng cÃ³ dá»¯ liá»‡u Ä‘á»ƒ thÃªm vÃ o cÆ¡ sá»Ÿ dá»¯ liá»‡u.")
            return

        texts = []
        metadatas = []
        
        for chunk in chunks:
            if "content" in chunk and "metadata" in chunk:
                texts.append(chunk["content"])
                metadatas.append(chunk["metadata"])
                
        print(f"[*] Äang nhÃºng (embedding) vÃ  lÆ°u {len(texts)} Ä‘oáº¡n vÄƒn báº£n...")
        
        self.vector_db.add_texts(
            texts=texts,
            metadatas=metadatas
        )
        
        self.vector_db.persist()
        print(f"[+] ÄÃ£ lÆ°u dá»¯ liá»‡u vÃ o ChromaDB thÃ nh cÃ´ng.")

    def search_similar(self, query: str, k: int = 3, filter_dict: Dict = None) -> List[Any]:
        """
        TÃ¬m kiáº¿m cÃ¡c Ä‘oáº¡n vÄƒn báº£n liÃªn quan Ä‘áº¿n cÃ¢u truy váº¥n.
        """
        print(f"[*] Äang tÃ¬m kiáº¿m: '{query}'...")
        results = self.vector_db.similarity_search(
            query=query, 
            k=k,
            filter=filter_dict
        )
        return results

