'''
RAG systems have two broad modes
---------------------------------
1) Retrieval‑only (no LLM involved)
2) Retrieval‑augmented generation (retrieval + LLM)

------------------------------------------------------------
1) Retrieval without LLM: This is pure information retrieval
-------------------------------------------------------------
> You query a vector store or keyword index.
> You get back the top‑k documents or chunks.
> No LLM interprets, rewrites, summarizes, or reasons.
> Output = raw retrieved text.
> This is essentially a search engine workflow.
> Useful for:
    * filtering
    * classification
    * rule‑based pipelines
    * deterministic workflows

2) Classic RAG pipeline.
-----------------------
> Retrieve relevant chunks
> Feed them into an LLM
> LLM synthesizes an answer using the retrieved context
> Output = LLM‑generated answer grounded in retrieved data.
> Useful for:
    * question answering
    * summarization
    * reasoning over documents
    * chatbots
'''

# 1) Import libraries
# ------------------------
import os
from llama_index.core import ( Settings, StorageContext, VectorStoreIndex, load_index_from_storage,)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.readers.file import PDFReader
import pandas as pd

'''
Other Chunking types supported in LlamaIndex
--------------------------------------------
1. Sentence-based Chunking: Splits text by sentences, then groups them into chunks of a target size.
Best for: natural language documents, articles, reports.

2. Token-based Chunking: Uses tokenizer boundaries (e.g., OpenAI, HuggingFace) to create chunks of a fixed token size.
Best for: LLM‑optimized pipelines where token limits matter.

3. Character-based Chunking: Splits text purely by character count.
Best for: simple, deterministic chunking; raw text without structure.

4. Semantic Chunking: Uses embeddings to detect semantic boundaries and split text where topic shifts occur.
Best for: long, unstructured documents with multiple themes.

5. Markdown Chunking: Understands Markdown structure:
Headings / Lists / Code blocks / Sections
Best for: technical docs, READMEs, wikis.

6. HTML Chunking: Parses HTML DOM and chunks based on tags like:
<p> / <div> / <section> / <article>
Best for: web pages, blogs, scraped content.

7. JSON Chunking: Splits JSON documents by keys, arrays, or nested objects.
Best for: structured data, logs, API responses.

9. Table Chunking: Splits tabular data (CSV, Excel, HTML tables) into row‑ or column‑based chunks.
Best for: analytics, financial data, logs.
'''

# -------------------------------------------------------------
# 2) Environment Variables
# ---------------------------------------------------------
BASE_DIR = os.getcwd()
print(BASE_DIR)
PDF_PATH = BASE_DIR + "\\usecase\\small_inventory.pdf"
PERSIST_DIR = BASE_DIR + "\\persistentdir\\storage_pdf_llamaindex"
print(PERSIST_DIR)
CHUNKSIZE=700
OVERLAP=0.1

# 3) Model settings
# ---------------------------------------------------------
llm = OpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),temperature=0)
embeddings = OpenAIEmbedding(model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"))
nodeparser = SentenceSplitter(chunk_size=CHUNKSIZE,chunk_overlap=int(CHUNKSIZE*OVERLAP))

# 4) Load and enrich PDF documents
# ---------------------------------------------------------
''' 
Description: Loads a PDF file from disk using LlamaIndex's `PDFReader` and enriches each page with custom 
metadata (source file path, page number, and document type). 
Each page in the PDF becomes a separate document object.

Parameters: pdf_path: Full file path to the PDF file to be loaded
Returns: A list of enriched LlamaIndex `Document` objects (one per PDF page), or a list containing error 
info if an exception occurs.
'''
def load_pdf_documents(pdf_path):
    try:
        reader = PDFReader()
        docs = reader.load_data(file=pdf_path)

        enriched_docs = []
        for i, doc in enumerate(docs, start=1):
            # metadata = dict(doc.metadata or {})
            metadata = {}
            metadata.update( { "source_file": pdf_path,
                               "page_number": i,
                               "document_type": "inventory_incident_notes",} )
            doc.metadata = metadata
            enriched_docs.append(doc)

    except Exception as e:
        enriched_docs.extend(["EXCEPTION","load_pdf_documents(). " + str(e)])

    return enriched_docs

# load the input PDF
docs = load_pdf_documents(PDF_PATH)
print(len(docs))

# Print the metadata info of each page
for i in range(len(docs)):
    print(docs[i].metadata)


# 5) Build or load index
# ---------------------------------------------------------
''' 
Description: Checks if a previously saved vector index exists in `PERSIST_DIR`. If it does, it loads it from disk (avoiding re-embedding). If not, it loads the PDF documents, builds a new `VectorStoreIndex` by embedding them, and saves it to disk for future reuse.
Parameters: None
Returns: A `VectorStoreIndex` object ready for querying, or an error string if an exception occurs.
'''
def build_or_load_index() -> VectorStoreIndex:
    try:
        if os.path.exists(PERSIST_DIR):
            storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
            index = load_index_from_storage(storage_context)
        else:
            documents = load_pdf_documents(PDF_PATH)
            index = VectorStoreIndex.from_documents(documents)
            index.storage_context.persist(persist_dir=str(PERSIST_DIR))

    except Exception as e:
        index = "EXCEPTION in build_or_load_index()." + str(e)

    return(index)

# Build the index
# --------------
print("Building/loading PDF index...")
_ = build_or_load_index()
print("Index ready.")

# from pathlib import Path
# print("Directory exists:", os.path.exists(PERSIST_DIR))
# print("Absolute path:", Path(PERSIST_DIR).resolve())
# BASE_DIR1 = Path.cwd()
# PERSIST_DIR1 = BASE_DIR1 / "storage"



# 6) Query helpers
# ---------------------------------------------------------
'''
<< CLASSICAL RAG >>

Constructs a full RAG (Retrieval-Augmented Generation) pipeline by wiring together three components: 
a) vector index (via `build_or_load_index`), 
b) A retriever that fetches the most relevant chunks, 
c) Response synthesizer that feeds those chunks to the LLM to generate a final answer.

Parameters: top_k: Number of most similar document chunks to retrieve from the index |
Returns: A `RetrieverQueryEngine` that can accept a query string and return a synthesized LLM answer.

Working methodology
--------------------
> Top‑k chunks are retrieved
> LLM synthesizes a single final answer using those chunks as context by reasoning over all of them together
'''
def build_query_engine(top_k: int = 5) -> RetrieverQueryEngine:
    index = build_or_load_index()

    # This creates a component responsible for generating the final answer from retrieved chunks.
    # retrieved chunks will be like CHUNK 1, CHUNK 2, CHUNK 3
    # Synthesizer controls the final display
    retriever = VectorIndexRetriever(index=index, similarity_top_k=top_k,)

    # Parameters for response_mode:
    #   * compact:          Produces a concise answer by merging all chunks into a single prompt before synthesis.
    #   * tree_summarize:   Hierarchical summarization (for large documents)
    #   * refine:           Iteratively improves answer, chunk by chunk
    #   * simple_summarize: Basic summarization by concatenation of all chunks
    #   * accumulate:       Returns raw or lightly processed chunk outputs without deep synthesis
    #   * structure_refine: Similar to refine but enforces structured output (JSON-like) while iteratively
    #                          improving the answer
    response_synthesizer = get_response_synthesizer(response_mode="compact")

    return RetrieverQueryEngine( retriever=retriever, response_synthesizer=response_synthesizer,)

# 7) ------------------------------------------
# ONLY retrieves relevant chunks from the index
# DOES NOT CALL the LLM for answer generation
# -------------------------------------------
'''
<< RETRIEVAL ONLY>>

> Performs retrieval only — fetches the most relevant document chunks from the index based on the query. 
> Does not call the LLM. 
> Useful for inspecting what the retriever finds before any answer generation. 

Returns: Results as a structured Pandas DataFrame with rank, similarity score, metadata, and chunk text.

Parameters: 
    query: The search query used to find relevant chunks
    top_k: Number of top matching chunks to retrieve

Returns: A `pd.DataFrame` with columns: `rank`, `score`, `metadata`, and `response` (chunk text).
'''
def retrieve_only(query: str, top_k: int = 5):
    """
    Returns retrieved chunks only, without synthesized final answer.
    """
    result = pd.DataFrame()

    index = build_or_load_index()
    retriever = VectorIndexRetriever(index=index, similarity_top_k=top_k)
    nodes = retriever.retrieve(query)

    # print(f"\nQUERY: {query}")
    # print(f"Retrieved {len(nodes)} chunks\n")

    # Node: <class 'llama_index.core.schema.NodeWithScore'>
    # A NodeWithScore is simply a retrieved chunk of text plus the relevance score assigned to it.

    for i, node in enumerate(nodes, start=1):
        rank = [i]
        # score = getattr(node,"score", None)
        score = node.score
        metadata = node.metadata
        response = node.text
        row = {"rank":rank, "score":score, "metadata":metadata, "response":response}
        result = result._append(row,ignore_index=True)

    return(result)

'''
The main end-to-end RAG function. 
It builds the query engine, retrieves relevant chunks, and sends them to the LLM to generate a grounded 
answer. 
Also prints the sources (chunk text + metadata + similarity score) used to form the answer — 
Useful for transparency and debugging.

Parameters:
    query: The natural language question to answer 
    top_k: Number of relevant chunks to retrieve and pass to the LLM

Returns: Nothing (prints the answer and sources to console).
'''
def classic_rag(query: str, top_k: int = 5):
    """
    Retrieves relevant chunks and generates a grounded answer.
    """
    # CLASSIC RAG
    query_engine = build_query_engine(top_k=top_k)
    response = query_engine.query(query)

    # Synthesized Response
    print(f"\nQUESTION: {query}")
    print("\nANSWER:")
    print(response)

    # Retrieved Chunks Data
    print("\nSOURCES:")
    for i, src in enumerate(response.source_nodes, start=1):
        # print("=" * 90)
        print(f"SOURCE {i} | score={src.score}")
        print(src.metadata)
        print(src.text[:700])
        print()


sample_queries = [
    "Which shipments mention barcode scan failures?",
    "Find notes about quantity mismatch or recount requests.",
    "What issues were reported in Bengaluru Distribution Hub?",
    "Which incidents mention transport delays and carton compression marks?",
    "Find notes related to Panasonic shipments."
]

# 1) Retrieval only
# ---------------
query = "barcode reading failures and physical inventory mismatch"
print("\n--- Retrieval only example ---")
answer = retrieve_only(query, top_k=4)
print(answer.columns)
print(answer)
answer['response'][0][:500]

answer = retrieve_only("barcode reading failures and physical inventory mismatch", top_k=4)
print(answer.response)

# 2) retrieval with formatting
# -------------------------
query = sample_queries[2]
classic_rag(query, top_k=4)