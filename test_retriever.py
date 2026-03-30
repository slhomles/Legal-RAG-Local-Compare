from legal_rag.retrieval.retriever import LegalRetriever


def main():
    retriever = LegalRetriever()

    query = "quy định về thanh toán"
    results = retriever.semantic_search(query=query, k=3)

    print("=" * 80)
    print(f"TRUY VAN: {query}")
    print("=" * 80)

    for i, doc in enumerate(results, 1):
        print(f"\n[KET QUA {i}]")
        print("METADATA:", doc.metadata)
        print("NOI DUNG:")
        print(doc.page_content[:800])


if __name__ == "__main__":
    main()