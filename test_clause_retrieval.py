from legal_rag.retrieval.retriever import LegalRetriever


def main():
    retriever = LegalRetriever()
    result = retriever.retrieve_clause_pair("Hop_dong_A", "Dieu 3")

    print("=" * 80)
    print("BAN A")
    print("=" * 80)
    for doc in result["A"]:
        print(doc.metadata)
        print(doc.page_content)
        print()

    print("=" * 80)
    print("BAN B")
    print("=" * 80)
    for doc in result["B"]:
        print(doc.metadata)
        print(doc.page_content)
        print()


if __name__ == "__main__":
    main()