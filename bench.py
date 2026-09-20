"""Reproducible personal benchmark: python bench.py [--backend local].

No API calls by default. The context-only LLM stub is labelled explicitly;
retrieval evidence is not presented as a correct generated answer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

from src import Document, EmbeddingStore, FixedSizeChunker, KnowledgeBaseAgent
from src.chunking import ChunkingStrategyComparator, SentenceChunker, RecursiveChunker
from src.embeddings import MockEmbedder, LocalEmbedder

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "data/Chinh_sach_thuong_mai_dien_tu"
# Change only this line for the personal strategy; all other settings stay shared.
PERSONAL_CHUNKER = FixedSizeChunker(chunk_size=500, overlap=50)
# IDs refer to source article IDs, independent of local file names.
GOLD_ARTICLES = {1: {"188931", "77251"}, 2: {"79233"}, 3: {"79467"}, 4: {"189477"}, 5: {"79233"}}
# AND between groups, OR within a group. These are evidence checks, not an LLM judge.
EVIDENCE = {
    1: [["15 ngày"], ["24 giờ", "24h"]],
    2: [[f"Bước {i}:"] for i in range(1, 9)],
    3: [["liên tục"], ["không bị cắt ghép"], ["6 mặt"], ["mã vận đơn"], ["niêm phong"], ["100 MB", "100MB"], ["1 phút"], ["5MB", "5 MB"]],
    4: [["Miễn phí trả hàng"], ["thanh toán trước phí trả hàng"], ["Shopee sẽ hỗ trợ"]],
    5: [["3 - 5 ngày làm việc"], ["1 - 14 ngày làm việc"]],
}


def read_document(path: Path) -> tuple[dict, str]:
    """Read this corpus's flat string frontmatter (not a general YAML parser)."""
    raw = path.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError(f"Missing frontmatter: {path}")
    metadata = {}
    for line in parts[1].strip().splitlines():
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    # Ingestion follows CP5: propagate available frontmatter; missing optional
    # fields do not stop an unfiltered retrieval run. doc_id always denotes file.
    metadata["doc_id"] = path.stem
    return metadata, parts[2].strip()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text).casefold()).strip()


def evaluate(query: dict, results: list[dict]) -> dict:
    gold_results = [(i, result) for i, result in enumerate(results, 1)
                    if result['metadata'].get('source_url', '').rstrip('/').split('/')[-1] in GOLD_ARTICLES[query['id']]]
    rank = gold_results[0][0] if gold_results else None
    # Do not allow unrelated documents to supply coincidentally matching numbers.
    contents = [normalize(result['content']) for _, result in gold_results]
    groups = EVIDENCE[query['id']]
    found = [any(normalize(marker) in content for marker in group for content in contents) for group in groups]
    complete = all(found)
    return {"gold_document_rank": rank, "document_only_score": 2 if rank == 1 else 1 if rank else 0,
            "evidence_groups": groups, "evidence_found": found, "context_contains_answer_markers": complete,
            "content_score": (2 if rank == 1 else 1) if rank and complete else 0,
            "note": "Heuristic evidence score only; inspect meaning/conditions and agent answer manually."}


def context_only_llm(prompt: str) -> str:
    context = prompt.split("Ngữ cảnh:\n", 1)[1].split("\n\nCâu hỏi:", 1)[0]
    return "[MOCK LLM: chỉ hiển thị ngữ cảnh; chưa sinh/chấm câu trả lời]\n" + context


def queries_from_report() -> list[dict]:
    report = (ROOT / "report/REPORT_NHOM.md").read_text(encoding="utf-8")
    table = report.split("### Câu hỏi đánh giá & Câu trả lời chuẩn", 1)[1].split("### Tổng hợp", 1)[0]
    queries = []
    for line in table.splitlines():
        cells = [s.strip() for s in line.split("|")]
        if len(cells) == 6 and cells[1].isdigit():
            question = cells[2].split(" *(", 1)[0]
            queries.append({"id": int(cells[1]), "question": question, "gold_answer": cells[3], "gold_source": cells[4]})
    if len(queries) != 5:
        raise ValueError("Expected exactly five shared benchmark queries")
    return queries


def run(backend: str, chunker=None, embedder=None) -> dict:
    chunker = PERSONAL_CHUNKER if chunker is None else chunker
    if embedder is None:
        embedder = MockEmbedder() if backend == "mock" else LocalEmbedder()
    store = EmbeddingStore(embedding_fn=embedder)
    documents = []
    inventory = []
    baseline = []
    warnings = []
    for path in sorted(CORPUS.glob("*.md")):
        metadata, body = read_document(path)
        if metadata.get('audience') not in {'buyer', 'seller', 'both'}:
            warnings.append(f"{path.name}: missing/invalid audience; buyer filter cannot include this document.")
        if not any(metadata.get(field) for field in ('category', 'language', 'product_type')):
            warnings.append(f"{path.name}: K4 requires at least one useful field besides audience.")
        chunks = chunker.chunk(body)
        inventory.append({**metadata, "file_path": path.relative_to(ROOT).as_posix(), "body_characters": len(body), "chunks": len(chunks), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        for i, chunk in enumerate(chunks):
            documents.append(Document(id=f"{metadata['doc_id']}#{i}", content=chunk, metadata={**metadata, "chunk_index": i}))
        if metadata.get('source_url', '').rstrip('/').split('/')[-1] in {'79233', '79467', '188931'}:
            stats = ChunkingStrategyComparator().compare(body, chunk_size=300)
            baseline.append({"doc_id": path.stem, "strategies": {k: {"count": v['count'], "avg_length": v['avg_length']} for k, v in stats.items()}})
    store.add_documents(documents)
    # The manifest is a submission artifact, not a dependency for reading .md.
    if not (CORPUS / 'sources.csv').exists():
        warnings.append('sources.csv absent (source.csv may exist); CP5 reads Markdown directly.')
    agent = KnowledgeBaseAgent(store, context_only_llm)
    runs = []
    for query in queries_from_report():
        filters = [None, {"audience": "buyer"}] if query["id"] == 5 else [None]
        for metadata_filter in filters:
            results = store.search_with_filter(query["question"], top_k=3, metadata_filter=metadata_filter)
            runs.append({**query, "metadata_filter": metadata_filter, "results": results,
                         "agent_answer": agent.answer_from_results(query['question'], results),
                         "evaluation": evaluate(query, results),
                         "rubric_score": None})
    return {"embedding_backend": embedder._backend_name, "llm_backend": "context-only mock; not an answer generator",
            "strategy": {"name": type(chunker).__name__, **vars(chunker)}, "warnings": warnings,
            "baseline_chunk_size": 300, "document_count": len(inventory), "chunk_count": len(documents),
            "inventory": inventory, "baseline": baseline, "runs": runs}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("mock", "local"), default="mock")
    args = parser.parse_args()
    embedder = MockEmbedder() if args.backend == "mock" else LocalEmbedder()
    result = run(args.backend, embedder=embedder)
    # Mandatory A/B on all three built-in strategies with the same corpus/query/backend.
    result['ab_comparison'] = []
    for chunker in (FixedSizeChunker(500, 50), SentenceChunker(3), RecursiveChunker(chunk_size=500)):
        measurement = result if result['strategy'] == {"name": type(chunker).__name__, **vars(chunker)} else run(args.backend, chunker, embedder)
        pair = [q for q in measurement['runs'] if q['id'] == 5]
        result['ab_comparison'].append({"strategy": measurement['strategy'], "chunk_count": measurement['chunk_count'],
                                        "runs": pair, "same_top3": [x['id'] for x in pair[0]['results']] == [x['id'] for x in pair[1]['results']]})
    output = ROOT / "ket_qua_benchmark.txt"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Backend: {result['embedding_backend']}; documents={result['document_count']}; chunks={result['chunk_count']}")
    for warning in result['warnings']:
        print('WARNING:', warning)
    for query in result['runs']:
        print_run(query)
    for comparison in result['ab_comparison']:
        print('\nA/B:', comparison['strategy']['name'], 'same_top3=', comparison['same_top3'])
        for query in comparison['runs']:
            print_run(query)
    print(f"Saved full top-3, metadata, source hashes, A/B and mock output: {output.name}")
    print("Rubric scores unset: manually inspect chunk evidence and evaluate real answers before assigning points.")


def print_run(query: dict) -> None:
    print(f"\nQ{query['id']}: {query['question']} | filter={query['metadata_filter']}")
    for i, hit in enumerate(query['results'], 1):
        print(f"  {i}. doc_id={hit['metadata']['doc_id']} chunk={hit['id']} score={hit['score']:.4f}")
        print('     ' + hit['content'].replace('\n', ' '))
    score = query['evaluation']
    print(f"  Document-only={score['document_only_score']}/2; content={score['content_score']}/2; evidence={score['evidence_found']}")


if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    main()
