# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Quang Hữu\
**Nhóm:** Four bot\
**Ngày:** 20/9/2026\

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiến gần về 1.0) biểu thị góc giữa hai vector nhúng (embedding vectors) rất nhỏ, đồng nghĩa với việc hai đoạn văn bản có sự tương đồng lớn về mặt ngữ nghĩa và bối cảnh chủ đề, bất kể độ dài ngắn của chúng khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: *"Khách hàng có quyền gửi yêu cầu đổi trả và hoàn tiền trong vòng 15 ngày."*
- Câu B: *"Người mua được phép khiếu nại hoàn trả sản phẩm trong thời hạn khoảng hai tuần."*
- Tại sao tương đồng: Hai câu sử dụng các từ ngữ hoàn toàn khác nhau ("khách hàng" vs "người mua", "15 ngày" vs "hai tuần") nên có thể gần nhau về chủ đề; tuy nhiên 15 ngày khác 14 ngày (hai tuần), vì vậy không thể dùng độ tương tự cao để kết luận hai chính sách tương đương.

**Ví dụ có độ tương tự THẤP:**
- Câu A: *"Khách hàng có quyền gửi yêu cầu đổi trả và hoàn tiền trong vòng 15 ngày."*
- Câu B: *"Hôm nay thời tiết Hà Nội trời nhiều mây và có mưa rào bất chợt."*
- Tại sao khác: Hai câu thuộc hai lĩnh vực ngữ nghĩa hoàn toàn xa lạ nhau (chính sách thương mại điện tử vs hiện tượng thời tiết khí hậu).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine đo góc giữa hai vector và không phụ thuộc độ lớn của chúng. Độ dài văn bản không đồng nhất với độ lớn embedding, nên không thể kết luận hai câu dài/ngắn cùng nghĩa có khoảng cách Euclid lớn. Với vector chuẩn hóa có độ lớn bằng 1, khoảng cách Euclid và cosine cho cùng thứ tự xếp hạng: d² = 2 − 2cos(θ).

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> (10000-50)/(500-50) = 22.11
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi tăng overlap lên 100: $\lceil (10000 - 100) / (500 - 100) \rceil = \lceil 9900 / 400 \rceil = 25$ chunks (tăng thêm 2 chunks). Chúng ta muốn tăng độ chồng chéo để bảo tồn liên kết ngữ cảnh ở ranh giới giữa hai chunk kế tiếp, ngăn chặn việc các câu văn hoặc ý tưởng quan trọng bị cắt đôi khiến mô hình không hiểu trọn vẹn ngữ nghĩa.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi sử dụng biểu thức chính quy với kỹ thuật regex positive lookbehind `(?<=[.!?])\s+|(?<=\.)\n+` để tách câu tại các điểm kết thúc câu mà không làm mất dấu câu gốc. Sau khi làm sạch khoảng trắng thừa, tôi gom các câu thành từng nhóm tối đa `max_sentences_per_chunk` câu. Tôi xử lý edge case chuỗi rỗng bằng cách trả về ngay `[]`, và nhận thức được các trường hợp chữ viết tắt (`TS.`, `v.v.`) có thể bị hiểu nhầm là dấu ngắt câu. Số thập phân `3.5` không bị tách bởi regex này vì sau dấu chấm không có khoảng trắng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán hoạt động theo nguyên lý chia để trị hai chiều với danh sách dấu phân cách ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Trường hợp cơ sở (base case) xảy ra khi chuỗi hiện tại có độ dài $\le$ `chunk_size` hoặc khi danh sách dấu phân cách bị rỗng / chỉ còn chuỗi rỗng (sẽ fallback cắt theo lát cắt ký tự trực tiếp). Nếu mảnh tách ra vẫn quá lớn, hàm đệ quy xuống dấu phân cách con; sau đó gom (merge) các mảnh liền kề lại sao cho tổng kích thước tối ưu tiệm cận `chunk_size`.

**`compute_similarity`** — tính tích vô hướng chia cho tích hai chuẩn Euclid; trả `0.0` nếu vector rỗng hoặc có chuẩn bằng 0, chặn sai số số thực trong [-1, 1].

**`ChunkingStrategyComparator.compare`** — chạy ba chunker trên cùng văn bản, trả `count`, `avg_length`, `chunks` cho từng chiến lược; độ dài trung bình bằng 0 nếu không có chunk.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Tôi lưu trữ toàn bộ các record trong bộ nhớ (`self._store: list[dict]`), mỗi record gồm `id`, `content`, `metadata` (được copy an toàn và gắn sẵn `doc_id`) cùng vector nhúng chuẩn hóa. Trong hàm `search`, truy vấn được nhúng thành vector, sau đó tính tích vô hướng (dot product) với từng vector lưu trữ và sắp xếp giảm dần theo điểm tương đồng để trả về `top_k` kết quả có kèm trường `score`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Với `search_with_filter`, tôi thực hiện **lọc metadata trước (pre-filtering)** để chọn ra tập ứng viên thỏa mãn tất cả tiêu chí của `metadata_filter`, sau đó mới thực hiện tìm kiếm độ tương tự trên tập ứng viên này (tránh trường hợp lọc sau làm mất kết quả hợp lệ). Với `delete_document`, tôi duyệt lọc và loại bỏ mọi bản ghi có `metadata['doc_id'] == doc_id` hoặc `id == doc_id`, trả về `True` nếu có ít nhất một bản ghi bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Tôi xây dựng hàm `answer` theo mô hình RAG tiêu chuẩn: gọi `store.search` để lấy các chunk phù hợp nhất, ghép thành chuỗi ngữ cảnh được đánh số thứ tự rõ ràng `[1]`, `[2]` kèm tên tài liệu nguồn. Prompt gửi tới LLM được thiết kế nghiêm ngặt: yêu cầu chỉ trả lời dựa vào ngữ cảnh, trích dẫn số thứ tự nguồn và nói rõ nếu không tìm thấy dữ liệu, hỗ trợ truy vết nguồn và hạn chế bịa đặt; prompt không bảo đảm mô hình luôn tuân thủ. Benchmark dùng `answer_from_results` để đưa đúng top-3 đã lọc vào prompt, không truy xuất lại không lọc. LLM hiện là stub hiển thị ngữ cảnh, chưa phải mô hình sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.1.1, pluggy-1.6.0 -- D:\Python\python.exe
cachedir: .pytest_cache
rootdir: D:\VInCode\K4-DAY07-NguyenQuangHuu-2A202602756
plugins: anyio-4.15.1, langsmith-0.12.4, asyncio-1.4.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.06s ==============================
```

**Bộ test gốc:** **42 / 42**. Sau khi bổ sung 5 test kiểm tra ngữ cảnh đã lọc, trường hợp rỗng, chấm nội dung và metadata tùy chọn, chạy lại:

```text
python -B -m pytest tests/ -q -p no:cacheprovider
47 passed in 0.10s
```

Môi trường kiểm tra: Python 3.12.8; README chuẩn hóa 3.11, tài liệu lab cho phép tiếp tục với 3.10+.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (Mock) | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Khách hàng có thể trả lại hàng trong vòng 15 ngày. | Người mua được quyền gửi yêu cầu hoàn trả sản phẩm trong 2 tuần. | Cao | 0.1248 | Đúng phần nào |
| 2 | Shopee hỗ trợ miễn phí vận chuyển cho đơn hàng hoàn trả. | Người mua không phải thanh toán tiền ship khi trả lại hàng về bưu cục. | Cao | -0.1491 | Bất ngờ (Sai do Mock) |
| 3 | Người bán phải phản hồi khiếu nại trong vòng 48 giờ. | Hôm nay thời tiết Hà Nội trời mưa to và gió lạnh. | Thấp | 0.0352 | Đúng |
| 4 | Sản phẩm bị bể vỡ hoặc hư hại trong quá trình vận chuyển. | Kiện hàng còn nguyên tem mác và hoạt động bình thường. | Thấp | 0.2568 | Bất ngờ (Sai do Mock) |
| 5 | Quy trình đăng bán sản phẩm dành cho chủ shop. | Chính sách bảo mật thông tin tài khoản ngân hàng. | Thấp | 0.0644 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là ở Cặp 2 (hai câu đồng nghĩa lại có điểm cosine âm: -0.1491) và Cặp 4 (hai câu trái nghĩa lại có điểm tương đồng dương cao nhất: 0.2568). Điều này phản ánh rõ hạn chế của `MockEmbedder` (dựa trên thuật toán băm MD5): nó chỉ biến đổi ký tự giả ngẫu nhiên chứ không chứa bất kỳ tri thức ngữ nghĩa học nào. Để vector embedding thực sự biểu diễn đúng ý nghĩa, bắt buộc phải dùng các mô hình Neural Embeddings được huấn luyện trên ngữ liệu lớn (như Sentence-Transformers hoặc Gemini/OpenAI API).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Lệnh: `python bench.py`. Corpus mới có **8 tài liệu, 337 chunks** với `FixedSizeChunker(500, 50)`. Backend **MockEmbedder 64 chiều**, không mã hóa ngữ nghĩa. Frontmatter được tách khỏi content và trải vào mọi chunk. `doc_id` là tên file gốc (ví dụ `79233`); ID chunk là `79233#0`. Nhãn audience/category/language do nhóm gán theo bảng phân loại, không phải trường website tự cung cấp.

Đổi chiến lược cá nhân tại một dòng `PERSONAL_CHUNKER` trong `bench.py`. Chương trình in top-3, score, doc_id cho đủ 5 câu và lưu đầy đủ nội dung/metadata/hash nguồn vào [`ket_qua_benchmark.txt`](../ket_qua_benchmark.txt). A/B câu 5 chạy trên cả ba chunker cùng dữ liệu và backend.

Chấm hai mức: `document_only_score` chỉ xét thứ hạng tài liệu gold; `content_score` còn yêu cầu các chuỗi bằng chứng trong `EVIDENCE` xuất hiện trong những chunk gold đã lấy. Điểm nội dung là phép kiểm tra chuỗi hỗ trợ đối chiếu, không thay thế kiểm tra ý nghĩa, ngoại lệ hoặc chấm câu trả lời agent. LLM stub chỉ hiển thị ngữ cảnh; điểm câu trả lời cuối cùng để trống.

| Câu | Top-3 (score) | Điểm đúng tài liệu | Điểm nội dung |
|---|---|---|---|
| 1 | `77246#11` (0.3444)<br>`77245#119` (0.3209)<br>`77245#43` (0.2997) | 0/2 | 0/2 |
| 2 | `77245#27` (0.3630)<br>`77245#127` (0.2912)<br>`188931#2` (0.2804) | 0/2 | 0/2 |
| 3 | `77245#90` (0.3469)<br>`77245#56` (0.2828)<br>`77246#5` (0.2785) | 0/2 | 0/2 |
| 4 | `77245#146` (0.3717)<br>`77245#84` (0.3235)<br>`77245#24` (0.3051) | 0/2 | 0/2 |
| 5 | `189477#3` (0.2466)<br>`189477#5` (0.2282)<br>`79467#2` (0.1660) | 0/2 | 0/2 |

**Kết quả kiểm tra chuỗi: 0/5 câu có đủ bằng chứng đáp án.** Không dùng kết quả Mock để kết luận FixedSize kém hơn chunker khác.

### A/B câu 5 trên ba chiến lược

| Chiến lược | Filter | Top-3 (score) | Điểm nội dung |
|---|---|---|---|
| FixedSizeChunker | Không | `77245#69` (0.3689)<br>`77251#9` (0.3271)<br>`77246#15` (0.2861) | 0/2 |
| FixedSizeChunker | buyer | `189477#3` (0.2466)<br>`189477#5` (0.2282)<br>`79467#2` (0.1660) | 0/2 |
| SentenceChunker | Không | `77245#151` (0.3249)<br>`77245#68` (0.3152)<br>`77245#29` (0.2903) | 0/2 |
| SentenceChunker | buyer | `189477#2` (0.2289)<br>`79467#0` (0.2141)<br>`189477#8` (0.1799) | 0/2 |
| RecursiveChunker | Không | `77245#198` (0.3788)<br>`77245#162` (0.3245)<br>`77245#83` (0.3198) | 0/2 |
| RecursiveChunker | buyer | `189477#11` (0.2122)<br>`188931#0` (0.2077)<br>`79467#4` (0.1983) | 0/2 |

Filter thay đổi top-3 nhưng chưa chứng minh có filter thì trả lời đúng. So khớp `audience=buyer` cũng loại `both`, nên có thể làm mất tài liệu phù hợp. Không diễn giải khác biệt xếp hạng do Mock thành cải thiện ngữ nghĩa.

### Failure case và phân tích

Câu 1 hỏi thời hạn 15 ngày/24 giờ, nhưng top-1 `77246#11` nói về hình ảnh đăng bán. Nguyên nhân chính cần lưu ý là Mock sinh vector từ hash, không hiểu câu hỏi. Đề xuất thử embedding thật với cùng corpus/query/chunker (`python bench.py --backend local`, cần cài requirements-local.txt), rồi đánh giá lại; không chỉnh câu hỏi chỉ để tối ưu score Mock.

Trong thời gian dùng Mock, tập trung vào baseline count/avg_length và độ mạch lạc. FixedSize có thể bắt đầu/kết thúc giữa câu; bản crawl hiện còn tiêu đề lặp và nội dung giao diện, còn Sentence/Recursive chưa nhận được cấu trúc heading Markdown đầy đủ. Đây là hạn chế dữ liệu cần phân biệt với ảnh hưởng của embedding. So sánh với thành viên khác và phần học từ demo chờ bằng chứng thực tế.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | Đã có log; retrieval chưa đạt, chưa chấm câu trả lời LLM |
| **Tổng phần cá nhân** | **Chưa chốt; không tự nhận 60/60** |
