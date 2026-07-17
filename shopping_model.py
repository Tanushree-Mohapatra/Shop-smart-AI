# ============================================================
# shopping_model.py – ShopSmart AI
# IBM watsonx.ai Granite Model Integration
#
# All AI agent responses are generated via this module.
# IBM Granite-13B-Chat or Granite-3-8B-Instruct is the
# primary LLM used throughout the application.
#
# IBM Langflow Integration:
#   This module is the 'IBM watsonx LLM' node in the Langflow
#   workflow. Every agent calls generate_response() after
#   receiving RAG-augmented context.
# ============================================================

import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# IBM watsonx.ai Credentials (from .env)
# ─────────────────────────────────────────────
WATSONX_API_KEY    = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

# IBM Granite model identifiers
# granite-13b-chat-v2 is the conversational model
# granite-3-8b-instruct is the instruct-tuned model
GRANITE_CHAT_MODEL    = "ibm/granite-13b-chat-v2"
GRANITE_INSTRUCT_MODEL = "ibm/granite-3-8b-instruct"

# Lazy-loaded watsonx client
_watsonx_model = None

# Token usage tracker
_token_stats = {"input_tokens": 0, "output_tokens": 0, "calls": 0}


def get_token_stats() -> dict:
    """Return cumulative token usage since app start."""
    return dict(_token_stats)


def _get_watsonx_model(model_id: str = GRANITE_INSTRUCT_MODEL):
    """
    Lazily initialise the IBM watsonx.ai ModelInference client.

    IBM Orchestrate Integration Point:
    In IBM Orchestrate, this function is wrapped as a Skill that can
    be invoked by any automation task requiring AI text generation.
    """
    global _watsonx_model
    if _watsonx_model is not None:
        return _watsonx_model

    if not WATSONX_API_KEY or not WATSONX_PROJECT_ID:
        logger.warning("IBM watsonx.ai credentials not configured. Using mock responses.")
        return None

    try:
        # ── IBM watsonx.ai SDK call ──────────────────────────────
        from ibm_watsonx_ai import APIClient, Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

        credentials = Credentials(
            url=WATSONX_URL,
            api_key=WATSONX_API_KEY,
        )
        parameters = {
            GenParams.MAX_NEW_TOKENS: 1024,
            GenParams.MIN_NEW_TOKENS: 50,
            GenParams.TEMPERATURE: 0.7,
            GenParams.TOP_P: 0.9,
            GenParams.TOP_K: 50,
            GenParams.REPETITION_PENALTY: 1.05,
        }
        _watsonx_model = ModelInference(
            model_id=model_id,
            credentials=credentials,
            project_id=WATSONX_PROJECT_ID,
            params=parameters,
        )
        logger.info("IBM watsonx.ai Granite model '%s' initialised.", model_id)
        return _watsonx_model
        # ── End IBM watsonx.ai SDK call ─────────────────────────

    except ImportError:
        logger.error("ibm-watsonx-ai package not installed. Run: pip install ibm-watsonx-ai")
        return None
    except Exception as e:
        logger.error("Failed to initialise IBM watsonx.ai: %s", e)
        return None


def generate_response(prompt: str, context: str = "", model_id: str = GRANITE_INSTRUCT_MODEL) -> str:
    """
    Core function: Send a prompt to IBM Granite and return the response.

    This is the central AI generation function used by ALL 8 agents.

    IBM Langflow Integration:
        This function maps to the 'IBM watsonx LLM' component in Langflow.
        The `context` parameter carries RAG-retrieved shopping knowledge.

    IBM Orchestrate Integration:
        IBM Orchestrate calls this as a registered Skill action for any
        task requiring natural-language generation.

    Args:
        prompt:   The task-specific prompt from an agent.
        context:  RAG-retrieved context to ground the response.
        model_id: IBM Granite model identifier.

    Returns:
        Generated text response.
    """
    # Build the full prompt with RAG context
    if context:
        full_prompt = (
            f"You are ShopSmart AI, an intelligent shopping assistant powered by IBM Granite.\n\n"
            f"Relevant Knowledge:\n{context}\n\n"
            f"Task: {prompt}\n\n"
            f"Response:"
        )
    else:
        full_prompt = (
            f"You are ShopSmart AI, an intelligent shopping assistant powered by IBM Granite.\n\n"
            f"Task: {prompt}\n\n"
            f"Response:"
        )

    # ── IBM Granite API Call ─────────────────────────────────
    model = _get_watsonx_model(model_id)
    if model:
        try:
            # Use generate() to get full response including token usage
            raw = model.generate(prompt=full_prompt)
            result_text = raw["results"][0]["generated_text"].strip()
            # ── Token usage logging ──────────────────────────
            usage = raw["results"][0]
            input_tokens  = usage.get("input_token_count", 0)
            output_tokens = usage.get("generated_token_count", 0)
            stop_reason   = usage.get("stop_reason", "?")
            # Accumulate totals
            _token_stats["input_tokens"]  += input_tokens
            _token_stats["output_tokens"] += output_tokens
            _token_stats["calls"]         += 1
            logger.info(
                "IBM Granite tokens — input: %s | output: %s | stop: %s | total_calls: %d",
                input_tokens, output_tokens, stop_reason, _token_stats["calls"]
            )
            # ── End token usage logging ──────────────────────
            return result_text
        except Exception as e:
            logger.error("IBM Granite generation error: %s", e)
            return _mock_response(prompt)
    # ── End IBM Granite API Call ─────────────────────────────

    # Fallback: mock responses for demo when credentials unavailable
    return _mock_response(prompt)


def _mock_response(prompt: str) -> str:
    """
    Intelligent mock response for demos without IBM watsonx.ai credentials.
    Returns contextually relevant placeholder text based on prompt keywords.
    """
    prompt_lower = prompt.lower()

    if "compare" in prompt_lower or "comparison" in prompt_lower:
        return ("Based on my analysis, I've compared the products across key parameters including "
                "performance, value, build quality, and features. The premium option offers superior "
                "specs while the budget option provides excellent value. For most users, the mid-range "
                "option strikes the best balance. IBM Granite analysis complete. "
                "[Note: Configure WATSONX_API_KEY for live AI responses]")

    if "review" in prompt_lower or "sentiment" in prompt_lower:
        return ("Review Analysis: Overall sentiment is POSITIVE (78%). Customers appreciate the build "
                "quality and performance. Common praise: battery life, camera quality, value for money. "
                "Common complaints: accessories not included, slightly heavy. Fake review probability: "
                "12% (Low Risk). Customer satisfaction score: 8.2/10. "
                "[Note: Configure WATSONX_API_KEY for live AI responses]")

    if "predict" in prompt_lower or "price" in prompt_lower or "buy" in prompt_lower:
        return ("Price Prediction: Based on historical trends and seasonal patterns, this product is "
                "likely to see a 10-15% discount during the upcoming sale season. Current price is "
                "near average. Recommendation: WAIT — a better deal is expected within 2-3 weeks. "
                "Festival season sales (Diwali, Big Billion Days) historically offer the best discounts. "
                "[Note: Configure WATSONX_API_KEY for live AI responses]")

    if "recommend" in prompt_lower or "suggest" in prompt_lower:
        return ("Personalised Recommendations: Based on your preferences and budget, here are my top "
                "picks. For the best overall value, consider products in the mid-range segment. "
                "For premium quality, flagship options from Apple and Samsung lead the market. "
                "Budget-friendly alternatives from Xiaomi and Realme offer excellent specs/price ratio. "
                "[Note: Configure WATSONX_API_KEY for live AI responses]")

    if "eco" in prompt_lower or "sustain" in prompt_lower or "green" in prompt_lower:
        return ("Sustainability Analysis: This product has a moderate eco-score. Energy efficiency is "
                "above average. Packaging uses 60% recycled materials. Carbon footprint is estimated "
                "at 45 kg CO₂e (manufacturing). Better eco-friendly alternatives are available. "
                "Look for EPEAT Gold or Energy Star certified products for greener choices. "
                "[Note: Configure WATSONX_API_KEY for live AI responses]")

    # Generic shopping assistant response
    return ("As your ShopSmart AI assistant powered by IBM Granite, I've analysed your query. "
            "Based on current market data, user reviews, and price trends, I recommend carefully "
            "evaluating your specific needs before purchasing. Consider factors like warranty, "
            "after-sales service, and long-term value. Feel free to ask for a detailed comparison "
            "or personalised recommendation! "
            "[Note: Configure WATSONX_API_KEY for live IBM Granite responses]")


def is_watsonx_configured() -> bool:
    """Check if IBM watsonx.ai credentials are properly configured."""
    return bool(WATSONX_API_KEY and WATSONX_PROJECT_ID)
