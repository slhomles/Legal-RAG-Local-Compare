from legal_rag.retrieval.retriever import LegalRetriever


def main():
    retriever = LegalRetriever()
    result = retriever.build_paired_context("Hop_dong_A", "Dieu 3")

    print(result)


if __name__ == "__main__":
    main()