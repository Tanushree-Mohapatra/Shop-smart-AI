# ============================================================
# rag.py – ShopSmart AI
# Retrieval-Augmented Generation using ChromaDB
# Stores shopping knowledge embeddings and retrieves context
# before every IBM Granite call.
# ============================================================

import os
import logging

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    logger.warning("chromadb not installed – RAG disabled. Run: pip install chromadb sentence-transformers")
    CHROMADB_AVAILABLE = False

CHROMA_DIR = os.path.join("instance", "chroma_store")
COLLECTION_NAME = "shopsmart_knowledge"

# ─────────────────────────────────────────────
# Knowledge Base Documents
# ─────────────────────────────────────────────

KNOWLEDGE_DOCUMENTS = [
    # Product Buying Guides
    {
        "id": "laptop_guide_1",
        "text": "When buying a laptop for programming, prioritise: at least 16GB RAM, fast SSD storage (512GB+), good processor (Intel Core i5/i7 or AMD Ryzen 5/7), comfortable keyboard, and at least 8-hour battery life. MacBook Air M2 and ThinkPad X1 Carbon are excellent choices.",
        "metadata": {"category": "Laptops", "type": "buying_guide"}
    },
    {
        "id": "laptop_guide_2",
        "text": "Gaming laptops require: dedicated GPU (Nvidia RTX 3060 or higher), high refresh rate display (144Hz+), fast processor, adequate cooling, and at least 16GB RAM. Asus ROG, MSI, and HP Omen/Pavilion are popular gaming laptop brands.",
        "metadata": {"category": "Laptops", "type": "buying_guide"}
    },
    {
        "id": "smartphone_guide_1",
        "text": "When buying a smartphone, consider: processor performance (Snapdragon 8 Gen series or Apple A-series), camera quality (MP count alone is misleading, sensor size matters), battery capacity (4500mAh+), display type (AMOLED > IPS for colours), and software update commitment.",
        "metadata": {"category": "Smartphones", "type": "buying_guide"}
    },
    {
        "id": "headphone_guide_1",
        "text": "Choosing headphones: Over-ear for best audio quality and ANC. In-ear TWS for portability. Check impedance for audiophiles. ANC quality varies — Sony WH-1000XM5 and Apple AirPods Pro lead the market. Look for LDAC or aptX codec for high-quality Bluetooth audio.",
        "metadata": {"category": "Headphones", "type": "buying_guide"}
    },
    {
        "id": "smartwatch_guide_1",
        "text": "Smartwatch buying guide: Consider compatibility (Apple Watch only works with iPhone). Health sensors (ECG, SpO2 are important). Battery life varies from 1 day (Apple Watch) to 2 weeks (budget watches). Consider watch face size and band comfort.",
        "metadata": {"category": "Smartwatches", "type": "buying_guide"}
    },
    # Technology Explanations
    {
        "id": "tech_oled_amoled",
        "text": "OLED vs AMOLED: Both are self-emissive display technologies offering deep blacks and vibrant colours. AMOLED (Active Matrix OLED) uses an active matrix to control pixels, offering faster refresh rates and lower power consumption. Samsung typically uses AMOLED while others may use standard OLED. Both are superior to IPS LCD for contrast ratios.",
        "metadata": {"category": "Technology", "type": "explanation"}
    },
    {
        "id": "tech_ssd_hdd",
        "text": "SSD vs HDD: SSDs (Solid State Drives) are faster (500MB/s to 7000MB/s), silent, consume less power, and are more durable. HDDs (Hard Disk Drives) offer more storage per rupee but are slower (80-160MB/s). For OS and applications, SSD is strongly recommended. For bulk storage, HDD is cost-effective.",
        "metadata": {"category": "Technology", "type": "explanation"}
    },
    {
        "id": "tech_5g",
        "text": "5G smartphones: 5G offers significantly faster data speeds (up to 10Gbps theoretical) and lower latency vs 4G LTE. In India, 5G coverage is expanding rapidly. If you plan to use the phone for 3+ years, buying a 5G phone is recommended even if your area doesn't yet have 5G coverage.",
        "metadata": {"category": "Technology", "type": "explanation"}
    },
    # Shopping Tips
    {
        "id": "shopping_tip_1",
        "text": "Best time to buy electronics in India: Big Billion Days (Flipkart, October), Amazon Great Indian Festival (October), Republic Day Sale (January 26), Independence Day Sale (August 15), and End of Financial Year sales (March). Prices can drop by 10-40% during these events.",
        "metadata": {"category": "Shopping", "type": "tip"}
    },
    {
        "id": "shopping_tip_2",
        "text": "How to detect fake reviews: Look for overly generic praise, sudden spike in reviews, reviewer with only one review, identical language across multiple reviews, all 5-star reviews without any criticism, and reviews posted on the same date. Tools like Fakespot can help analyse review authenticity.",
        "metadata": {"category": "Shopping", "type": "tip"}
    },
    {
        "id": "shopping_tip_3",
        "text": "Price comparison tips: Always compare prices across Amazon, Flipkart, Croma, Reliance Digital, and brand's own website. Use tools like PriceDekho, SmartPrix, or 91mobiles for price tracking. Consider EMI options carefully — zero-cost EMI may include processing fees.",
        "metadata": {"category": "Shopping", "type": "tip"}
    },
    # Eco / Sustainability
    {
        "id": "eco_guide_1",
        "text": "Green electronics: Look for Energy Star certification, EPEAT registration, and RoHS compliance. Apple, HP, and Dell have strong environmental commitments. Eco score considers: recyclable materials, energy efficiency, packaging, repairability, and longevity. Buying fewer, higher-quality products is more sustainable.",
        "metadata": {"category": "Sustainability", "type": "eco_guide"}
    },
    {
        "id": "eco_guide_2",
        "text": "E-waste: India is the 3rd largest e-waste generator. Proper disposal of electronics is crucial. Brands like Apple, Samsung, and Dell offer take-back programmes. Look for products with modular design and easy repairability. Fairphone leads in sustainable smartphone design.",
        "metadata": {"category": "Sustainability", "type": "eco_guide"}
    },
    # Consumer Rights
    {
        "id": "consumer_rights_1",
        "text": "India consumer rights for electronics: You are entitled to replacement or full refund if a product has a manufacturing defect within the warranty period. Under the Consumer Protection Act 2019, you can file complaints at consumerhelpline.gov.in. Online purchases have a return window of typically 7-30 days.",
        "metadata": {"category": "Consumer Rights", "type": "legal"}
    },
    {
        "id": "warranty_guide_1",
        "text": "Warranty vs Extended Warranty: Standard manufacturer warranty covers manufacturing defects. Extended warranty covers accidental damage or post-warranty repairs. For flagship phones and laptops, extended warranty is often worth the cost. Always register your product online to activate warranty.",
        "metadata": {"category": "Warranty", "type": "guide"}
    },
    # FAQs
    {
        "id": "faq_refurbished",
        "text": "Should I buy refurbished electronics? Certified refurbished products from brands like Apple Certified Refurbished or Amazon Renewed are generally reliable. They are tested, repaired, and come with a warranty. You can save 20-40% vs new. Avoid unverified third-party refurbished products.",
        "metadata": {"category": "FAQ", "type": "faq"}
    },
    {
        "id": "faq_budget_phone",
        "text": "Best budget smartphones under ₹15000 in 2024: Redmi Note 13, Realme Narzo 60, Samsung Galaxy M34, Motorola G54. Key considerations: battery life, camera quality, processor speed, and software updates. Avoid phones with less than 2 years of software update commitment.",
        "metadata": {"category": "Smartphones", "type": "recommendation"}
    },
    {
        "id": "faq_headphone_budget",
        "text": "Best headphones under ₹2000: Boat Rockerz 550, JBL Tune 520BT, Realme Buds Wireless. For ₹3000-₹5000 range: JBL Tune 770NC, Boat Nirvana Ion. At ₹10000+: Sony WH-CH720N offers ANC at a reasonable price.",
        "metadata": {"category": "Headphones", "type": "recommendation"}
    },
]


# ─────────────────────────────────────────────
# RAG Manager
# ─────────────────────────────────────────────

class RAGManager:
    """
    Manages ChromaDB vector store for Retrieval-Augmented Generation.

    IBM Langflow Integration Point:
    In a Langflow workflow, this component acts as the 'Vector Store Retriever'
    node. The retrieve() method is called before every IBM Granite LLM call
    to inject relevant shopping context into the prompt.
    """

    def __init__(self):
        self._client = None
        self._collection = None
        self._embedding_fn = None

    def _get_embedding_fn(self):
        """Use sentence-transformers for local embeddings (no API key needed)."""
        if not CHROMADB_AVAILABLE:
            return None
        if self._embedding_fn is None:
            try:
                self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
                logger.info("Loaded sentence-transformer embedding function.")
            except Exception as e:
                logger.warning("sentence-transformers unavailable, using default: %s", e)
                self._embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        return self._embedding_fn

    def _get_collection(self):
        """Lazily initialise ChromaDB client and collection."""
        if not CHROMADB_AVAILABLE:
            return None
        if self._collection is None:
            os.makedirs(CHROMA_DIR, exist_ok=True)
            self._client = chromadb.PersistentClient(path=CHROMA_DIR)
            self._collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self._get_embedding_fn(),
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB collection '%s' loaded with %d docs.",
                        COLLECTION_NAME, self._collection.count())
        return self._collection

    def index_knowledge(self):
        """
        Index all knowledge documents into ChromaDB.
        Only adds documents not already present.
        """
        if not CHROMADB_AVAILABLE:
            return
        collection = self._get_collection()
        if collection is None:
            return
        existing_ids = set(collection.get()["ids"])
        new_docs = [d for d in KNOWLEDGE_DOCUMENTS if d["id"] not in existing_ids]
        if not new_docs:
            logger.info("All knowledge documents already indexed.")
            return
        collection.add(
            ids=[d["id"] for d in new_docs],
            documents=[d["text"] for d in new_docs],
            metadatas=[d["metadata"] for d in new_docs],
        )
        logger.info("Indexed %d new knowledge documents into ChromaDB.", len(new_docs))

    def retrieve(self, query: str, n_results: int = 3) -> str:
        """
        Retrieve the most relevant knowledge chunks for a query.

        This is the RAG retrieval step – called before every IBM Granite call
        to augment the prompt with grounded shopping knowledge.

        Returns:
            Concatenated context string to prepend to the LLM prompt.
        """
        if not CHROMADB_AVAILABLE:
            return ""
        try:
            collection = self._get_collection()
            if collection is None:
                return ""
            results = collection.query(
                query_texts=[query],
                n_results=min(n_results, collection.count()),
                include=["documents", "metadatas", "distances"],
            )
            docs = results.get("documents", [[]])[0]
            if not docs:
                return ""
            context_parts = []
            for i, doc in enumerate(docs, 1):
                context_parts.append(f"[Context {i}]: {doc}")
            return "\n".join(context_parts)
        except Exception as e:
            logger.error("RAG retrieval error: %s", e)
            return ""

    def add_product_knowledge(self, product_id: int, name: str, specs: dict, description: str):
        """Dynamically add a new product to the knowledge base."""
        try:
            collection = self._get_collection()
            doc_id = f"product_{product_id}"
            specs_str = ", ".join(f"{k}: {v}" for k, v in specs.items())
            text = f"{name} – {description}. Specifications: {specs_str}"
            collection.add(
                ids=[doc_id],
                documents=[text],
                metadatas=[{"category": "Product", "type": "product_data"}]
            )
        except Exception as e:
            logger.error("Failed to add product to ChromaDB: %s", e)


# Singleton instance
rag_manager = RAGManager()


def init_rag():
    """Initialise and index all knowledge documents."""
    try:
        rag_manager.index_knowledge()
        logger.info("RAG system initialised.")
    except Exception as e:
        logger.error("RAG init failed: %s", e)


def retrieve_context(query: str, n_results: int = 3) -> str:
    """Public helper – retrieve RAG context for a query."""
    return rag_manager.retrieve(query, n_results)
