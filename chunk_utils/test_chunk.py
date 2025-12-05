from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text_for_embeddings(
    text: str,
    chunk_size: int = 100,
    chunk_overlap: int = 50
) -> list[str]:
    """
    Splits a long text into semantically meaningful chunks suitable for embeddings.
    
    Args:
        text (str): The raw text to split.
        chunk_size (int): Max size of each chunk (in characters).
        chunk_overlap (int): Overlap between chunks to preserve context.
    
    Returns:
        list[str]: A list of clean text chunks ready for embedding.
    """
    
    # Define a recursive splitter that respects sentence/paragraph boundaries
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", "?", "!"],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    # Split text into chunks
    chunks = splitter.split_text(text)
    
    
    return chunks


# === Example usage ===
if __name__ == "__main__":
    text = """
    LangChain is a modular framework designed to help developers build powerful applications powered by large language models.
    It provides tools for prompt management, chaining, and context handling.
    With LangChain, you can build autonomous systems that reason, retrieve, and generate data efficiently.
    """
    
    chunks = chunk_text_for_embeddings(text)
    
    print(f"{len(chunks)} chunks created:\n")
    for i, chunk in enumerate(chunks, 1):
        print(f"{i}. {chunk}\n")
