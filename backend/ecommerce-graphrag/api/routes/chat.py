from fastapi import APIRouter, HTTPException
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from schemas.chat_schema import ChatRequest, ChatResponse
from services.retriever_service import hybrid_retriever_service
from core.llm import get_llm

import os
from langfuse import observe
from langfuse.langchain import CallbackHandler

router = APIRouter()

def build_qa_chain_and_retriever():
    llm = get_llm()
    retriever = hybrid_retriever_service.get_multi_hop_retriever()

    if not llm or not retriever:
        return None, None

    # ─────────────────────────────────────────────────────────────────
    # Step 1: Query Keyword Extractor / Translator
    # Nomic-embed-text is English-only, so CJK must be translated.
    # Additionally, we extract ONLY pure product keywords to prevent BM25
    # from matching stop words (like "highest", "orders", "zip codes") to random products.
    # ─────────────────────────────────────────────────────────────────
    translate_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "You are an e-commerce search query optimizer. "
                "Extract 2-4 core search keywords from the user's message in English. "
                "CRITICAL: Ignore conversational words and stop words. Focus on product names, categories, or the main subject of the query. "
                "If the query is a broad term (e.g., 'drink', 'food', 'clothing'), aggressively expand it to include 3-4 specific related examples (e.g., 'water soda juice beverage'). "
                "If the query is about reviews or customers, extract those keywords (e.g., 'customer review terrible'). "
                "Output ONLY the English keywords, nothing else. No punctuation."
            ),
        ),
        ("human", "{input}"),
    ])
    translate_chain = translate_prompt | llm | StrOutputParser()

    # ─────────────────────────────────────────────────────────────────
    # Step 2: Retrieval with optimized keywords
    # Returns raw docs for structured extraction + formatted context for LLM.
    # ─────────────────────────────────────────────────────────────────
    def retrieve_with_translation(original_input: str, config=None):
        search_query = translate_chain.invoke({"input": original_input}, config=config).strip()
        print(f"[Query Optimizer] '{original_input}' → '{search_query}'")

        # Guard against empty query causing Lucene ParseException
        if not search_query:
            print("[Warning] Query Optimizer returned empty string. Using fallback query.")
            search_query = "item"

        docs = retriever.invoke(search_query, config=config)
        print(f"[Retriever] {len(docs)} results for '{search_query}'")
        return docs

    # ─────────────────────────────────────────────────────────────────
    # Step 3: Synthesis using ORIGINAL user language (Traditional Chinese)
    # ─────────────────────────────────────────────────────────────────
    system_prompt = (
        "You are an expert E-Commerce Assistant for a large online department store.\n"
        "Use ONLY the following pieces of extracted graph knowledge to answer the user's question.\n"
        "If the user asks an out-of-domain question (e.g., zip codes, global sales statistics), honestly state that you don't have that data. "
        "HOWEVER, if the provided context contains products conceptually similar to their request (e.g., if they ask about 'gadget orders' and the context provides Laptops or Phones), "
        "you MUST warmly recommend those products anyway as alternatives.\n"
        "CRITICAL: DO NOT invent, hallucinate, or recommend any brands or products "
        "that are not explicitly listed in the Graph Context below.\n"
        "IMPORTANT: You MUST display ALL the products provided in the Graph Context below. "
        "Do not arbitrarily skip products or just pick one. Present the full list of retrieved products to give the user variety.\n"
        "ALWAYS answer in Traditional Chinese (繁體中文), maintaining a professional and enthusiastic tone.\n"
        "FORMATTING RULES:\n"
        "1. Maintain a brief, polite greeting (1 sentence max).\n"
        "2. For EACH recommended product, you MUST strictly use the following block format:\n\n"
        "- **產品名稱 (Product)**: [Name]\n"
        "- **特點描述 (Description)**: [Description]\n"
        "- **價格參考 (Price)**: $[Price]\n\n"
        "3. If an ImageURL is provided for the product, you MUST display it using standard Markdown image syntax immediately after the price:\n"
        "   ![[Name]]([ImageURL])\n"
        "   (If ImageURL is empty or undefined, you DO NOT need to write the Markdown image syntax.)\n\n"
        "4. Place the Markdown horizontal divider (`---`) exactly as shown between products.\n"
        "5. DO NOT write long paragraphs; stick exactly to the Key: Value structural format above.\n"
        "\n"
        "Graph Context (Including Associated Entities):\n"
        "{context}\n"
    )
    synthesis_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    synthesis_chain = synthesis_prompt | llm | StrOutputParser()

    return retrieve_with_translation, synthesis_chain


# Singleton: built once on startup
_result = build_qa_chain_and_retriever()
_retrieve_fn = _result[0] if _result else None
_synthesis_chain = _result[1] if _result else None


def _extract_product_context(docs) -> list:
    """Extract structured product data from retriever documents for the frontend panel."""
    products = []
    for doc in docs:
        meta = doc.metadata or {}
        # Parse product name & description from page_content
        content = doc.page_content or ""
        name = ""
        price = None
        image = ""
        description = ""
        category = ""

        import re
        for line in re.split(r'\n|\\n', content):
            line = line.strip()
            if line.startswith("Product:"):
                name = line[len("Product:"):].strip()
            elif line.startswith("Price: $"):
                try:
                    price = float(line[len("Price: $"):].strip())
                except ValueError:
                    pass
            elif line.startswith("ImageURL:"):
                image = line[len("ImageURL:"):].strip()
            elif line.startswith("Description:"):
                description = line[len("Description:"):].strip()
            elif line.startswith("Category:"):
                category = line[len("Category:"):].strip()

        # Also pull from metadata (may be more reliable)
        if meta.get("image"):
            image = meta["image"]
        if meta.get("price") is not None:
            price = meta["price"]

        # ─────────────────────────────────────────────────────────────────
        # Fallback for Missing or Broken Images (Mock Data)
        # Prevents ugly broken image icons in the frontend UI
        # ─────────────────────────────────────────────────────────────────
        if not image or len(image.strip()) < 5:
            import urllib.parse
            safe_name = urllib.parse.quote(name[:20] if name else "Product")
            # Create a premium-looking placeholder with dark styling
            image = f"https://placehold.co/600x400/0f172a/8b5cf6?text={safe_name}"

        products.append({
            "name": name,
            "description": description,
            "price": price,
            "image": image,
            "category": category,
            "knowledge": meta.get("associated_knowledge", []),
        })
    return products


@router.post("/chat", response_model=ChatResponse)
@observe(name="ecommerce_graphrag_chat")
def chat_endpoint(request: ChatRequest):
    if not _retrieve_fn or not _synthesis_chain:
        raise HTTPException(
            status_code=500,
            detail="Backend Hybrid RAG Chain failed to initialize. Check models or DB.",
        )

    try:
        # Initialize Langfuse CallbackHandler for LangChain
        langfuse_handler = CallbackHandler()
        config = {"callbacks": [langfuse_handler]}
        
        # Link trace to the thread_id for session tracking
        if request.thread_id:
            config["metadata"] = {"langfuse_session_id": request.thread_id}

        # Step 1: Retrieve raw docs (for both LLM context and frontend product panel)
        raw_docs = _retrieve_fn(request.message, config=config)

        # Deduplicate docs by ImageURL (base product) or Product Name
        docs = []
        seen_keys = set()
        import re
        for doc in raw_docs:
            # Limit to top 5 distinct products to prevent context window bloat and UI clutter
            if len(docs) >= 5:
                break

            content = doc.page_content or ""
            name = ""
            image = ""
            for line in re.split(r'\n|\\n', content):
                line = line.strip()
                if line.startswith("Product:"):
                    name = line[len("Product:"):].strip()
                elif line.startswith("ImageURL:"):
                    image = line[len("ImageURL:"):].strip()
            
            dedup_key = image if image else name
            if dedup_key and dedup_key in seen_keys:
                continue
            if dedup_key:
                seen_keys.add(dedup_key)
            docs.append(doc)

        # Step 2: Format context for LLM synthesis
        formatted = "\n\n".join(doc.page_content for doc in docs) if docs else "No relevant products found."
        print(f"\n[DEBUG] Context Sent to LLM:\n{formatted}\n")

        # Step 3: Generate LLM answer
        answer = _synthesis_chain.invoke({"context": formatted, "input": request.message}, config=config)

        # Step 4: Extract structured product data for the right panel
        # Only include products that the LLM explicitly mentioned in the answer
        filtered_docs = []
        for doc in docs:
            content = doc.page_content or ""
            name = ""
            for line in re.split(r'\n|\\n', content):
                line = line.strip()
                if line.startswith("Product:"):
                    name = line[len("Product:"):].strip()
                    break
            
            # If LLM didn't include the product name in its reply, it deemed it irrelevant.
            if name and name in answer:
                filtered_docs.append(doc)

        product_context = _extract_product_context(filtered_docs)

        return ChatResponse(reply=answer, context=product_context)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
