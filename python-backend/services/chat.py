"""
Chat service — LangChain LLM integration.

Builds a prompt from retrieved context + chat history,
sends to the LLM, and returns the response.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided context.
Use the context below to answer the user's question. If the context doesn't contain
relevant information, say so honestly. Be concise and accurate."""


class ChatService:
    """LangChain-powered chat with context from hybrid search."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self._llm = ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=model,
            temperature=0.7,
        )


    def generate_response(self, message: str, history: list[dict], sources: list[dict]) -> str:
        """
        Generate an LLM response using retrieved context and chat history.

        Args:
            message: The user's current message.
            history: Previous chat messages [{"role": "user"|"assistant", "content": "..."}].
            sources: Retrieved documents from hybrid search.

        Returns:
            The LLM's response text.
        """

        # Build context block from sources
        context_parts = []
        for src in sources:
            context_parts.append(f"[{src['title']}]: {src['content']}")
        context_block = "\n\n".join(context_parts) if context_parts else "No relevant context found."


        # Build message list starting with the system prompt and context
        messages = [
            SystemMessage(content=f"{SYSTEM_PROMPT}\n\n--- Context ---\n{context_block}\n--- End Context ---"),
        ]


        # Add chat history, mapping roles to LangChain message types
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))


        # Append the current user message and invoke the LLM
        messages.append(HumanMessage(content=message))

        response = self._llm.invoke(messages)

        return response.content
