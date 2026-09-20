from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        return self.answer_from_results(question, results)

    def answer_from_results(self, question: str, results: list[dict]) -> str:
        """Answer using exactly the supplied retrieval results, including filters."""
        if not results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở tri thức."

        context_blocks = []
        for i, res in enumerate(results, 1):
            source = res.get("metadata", {}).get("doc_id", res.get("id", "tài liệu"))
            content = res.get("content", "").strip()
            context_blocks.append(f"[{i}] (Nguồn: {source}):\n{content}")

        context_text = "\n\n".join(context_blocks)
        prompt = (
            f"Bạn là trợ lý AI trả lời câu hỏi dựa trên tài liệu được cung cấp.\n\n"
            f"Ngữ cảnh:\n{context_text}\n\n"
            f"Câu hỏi: {question}\n\n"
            f"Hướng dẫn: Hãy trả lời câu hỏi một cách chính xác dựa trên ngữ cảnh được cung cấp. "
            f"Trích dẫn số thứ tự nguồn [1], [2] tương ứng. "
            f"Nếu ngữ cảnh không chứa thông tin để trả lời, hãy nói rõ là không tìm thấy thông tin."
        )

        return self.llm_fn(prompt)
