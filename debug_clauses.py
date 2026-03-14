#!/usr/bin/env python
"""Debug: List all clause_ids in ChromaDB"""
import sys
sys.path.insert(0, 'src')

from legal_rag.db.vector_store import VectorStoreManager

print("[*] Initializing...")
vm = VectorStoreManager()

print("[*] Getting all chunks...")
all_results = vm.search_similar('test', k=100)
print(f"[+] Total chunks: {len(all_results)}")

print("\n[*] Full metadata for first 5 chunks:")
for i, doc in enumerate(all_results[:5]):
    print(f"\n  Chunk {i+1}:")
    print(f"    clause_id: {doc.metadata.get('clause_id', 'N/A')}")
    print(f"    version: {doc.metadata.get('version', 'N/A')}")
    print(f"    document_id: {doc.metadata.get('document_id', 'N/A')}")
    print(f"    heading: {doc.metadata.get('chunk_heading', 'N/A')}")

print("\n[*] Counting clause_ids by version:")
clause_versions = {}
for doc in all_results:
    cid = doc.metadata.get('clause_id', 'NONE')
    version = doc.metadata.get('version', 'NO_VERSION')
    key = f"{cid}/{version}"
    if key not in clause_versions:
        clause_versions[key] = 0
    clause_versions[key] += 1

for key in sorted(clause_versions.keys()):
    print(f"  {key}: {clause_versions[key]} chunks")

print("\n[+] Done!")
