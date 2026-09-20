from src import Document, EmbeddingStore, KnowledgeBaseAgent
from bench import evaluate, read_document


def test_agent_uses_filtered_context_without_searching_again():
    store = EmbeddingStore(embedding_fn=lambda text: [1.0])
    store.add_documents([
        Document(id="seller", content="Seller-only deadline", metadata={"audience": "seller"}),
        Document(id="buyer", content="Buyer-only deadline", metadata={"audience": "buyer"}),
    ])
    results = store.search_with_filter("deadline", metadata_filter={"audience": "buyer"})
    captured = []
    agent = KnowledgeBaseAgent(store, lambda prompt: captured.append(prompt) or "answer")
    assert agent.answer_from_results("deadline", results) == "answer"
    assert "Buyer-only deadline" in captured[0]
    assert "Seller-only deadline" not in captured[0]
    assert "[1]" in captured[0]


def test_empty_selected_context_does_not_call_llm():
    def unexpected_call(prompt):
        raise AssertionError("LLM must not be called for empty retrieval")

    agent = KnowledgeBaseAgent(EmbeddingStore(), unexpected_call)
    assert "Không tìm thấy" in agent.answer_from_results("question", [])


def test_gold_document_without_answer_does_not_earn_content_points():
    result = {"metadata": {"source_url": "https://help.shopee.vn/portal/4/article/79233"},
              "content": "Hướng dẫn gửi yêu cầu nhưng không có thời hạn."}
    scores = evaluate({"id": 5}, [result])
    assert scores['document_only_score'] == 2
    assert scores['content_score'] == 0


def test_evidence_across_gold_chunks_is_counted_at_top_two():
    meta = {"source_url": "https://help.shopee.vn/portal/4/article/79233"}
    results = [{"metadata": {}, "content": "unrelated"},
               {"metadata": meta, "content": "3 - 5 ngày làm việc"},
               {"metadata": meta, "content": "1 - 14 ngày làm việc"}]
    assert evaluate({"id": 5}, results)['content_score'] == 1


def test_optional_metadata_does_not_block_ingestion(tmp_path):
    path = tmp_path / 'article.md'
    path.write_text('---\ntitle: "Example"\naudience: "buyer"\n---\nBody', encoding='utf-8')
    metadata, body = read_document(path)
    assert metadata == {'title': 'Example', 'audience': 'buyer', 'doc_id': 'article'}
    assert body == 'Body'
