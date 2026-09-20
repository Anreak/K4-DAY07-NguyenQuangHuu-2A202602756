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
> Tôi xây dựng hàm `answer` theo mô hình RAG (Retrieval-Augmented Generation) hoàn chỉnh: gọi `store.search` để truy xuất các chunk phù hợp nhất, cấu trúc ngữ cảnh trích xuất thành chuỗi dữ liệu rõ ràng với số hiệu nguồn `[1]`, `[2]` kèm định danh tài liệu. Prompt được thiết kế chặt chẽ: chỉ đạo mô hình trả lời dựa trên ngữ cảnh được cung cấp, trích dẫn số thứ tự nguồn tương ứng và thông báo rõ nếu thông tin không tồn tại trong kho tri thức, đảm bảo tính minh bạch và truy vết nguồn dữ liệu. Trong pipeline benchmark, hàm `answer_from_results` được sử dụng để đưa trực tiếp kết quả đã qua bộ lọc metadata vào câu trả lời, đảm bảo tính nhất quán của chuỗi truy xuất.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.1.1, pluggy-1.6.0 -- D:\Python\python.exe
rootdir: D:\VInCode\K4-DAY07-NguyenQuangHuu-2A202602756
configfile: pytest.ini
plugins: anyio-4.15.1, langsmith-0.12.4, asyncio-1.4.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 47 items

tests/test_benchmark.py::test_agent_uses_filtered_context_without_searching_again PASSED [  2%]
tests/test_benchmark.py::test_empty_selected_context_does_not_call_llm PASSED [  4%]
tests/test_benchmark.py::test_gold_document_without_answer_does_not_earn_content_points PASSED [  6%]
tests/test_benchmark.py::test_evidence_across_gold_chunks_is_counted_at_top_two PASSED [  8%]
tests/test_benchmark.py::test_optional_metadata_does_not_block_ingestion PASSED [ 10%]
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [ 12%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [ 14%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [ 17%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 25%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 27%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 29%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 31%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 34%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 36%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 38%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 40%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 44%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 46%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 48%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 51%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 53%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 55%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 63%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 65%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 68%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 70%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 72%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 74%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 78%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 82%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 85%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 87%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 89%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 91%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 93%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 47 passed in 0.08s ==============================
```

**Kết quả:** Vượt qua toàn diện **47 / 47** bài kiểm thử (gồm 42 bài kiểm thử mã nguồn cơ bản và 5 bài kiểm thử nâng cao cho bộ lọc metadata, xử lý trường hợp biên và chấm điểm truy xuất RAG).

Môi trường kiểm tra: Python 3.12.8, pytest-9.1.1, hệ điều hành Windows. Toàn bộ các tiêu chí kỹ thuật đáp ứng chuẩn xác các yêu cầu đề ra.

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

Lệnh: `python bench.py --backend gemini --personal-only`. Corpus thực nghiệm cá nhân gồm **2 tài liệu (`79233`, `79467`), 14 chunks** tạo bởi `FixedSizeChunker(chunk_size=500, overlap=50)`. Backend sử dụng mô hình **Google Gemini Embedding (`gemini-embedding-001`, 3072 chiều)**, mã hóa ngữ nghĩa tiếng Việt chuyên sâu thay cho mock băm. Dữ liệu nạp có Frontmatter tách riêng và truyền vào từng chunk (`doc_id` là tên file gốc; ID chunk là `79233#0`, `79467#0`...).

Đánh giá chất lượng truy xuất được thực hiện tự động qua hai tiêu chí: `document_only_score` (truy xuất đúng tài liệu gold chuẩn) và `content_score` (sự hiện diện đầy đủ của các chuỗi bằng chứng thông tin `EVIDENCE` trong các chunk trích xuất). Tác tử tổng hợp và xuất kết quả có trích dẫn nguồn cho toàn bộ 5 truy vấn:

| Câu | Top-3 (score) | Điểm đúng tài liệu | Điểm nội dung | Ghi chú ngữ nghĩa |
|---|---|---|---|---|
| 1 | `79233#0` (0.7554)<br>`79233#5` (0.7466)<br>`79233#4` (0.7094) | 0/2 | 0/2 | Câu hỏi 1 thuộc tài liệu `188931` & `77251` (phần thành viên khác phụ trách, ngoài phạm vi 2 file cá nhân). |
| 2 | `79233#0` (0.8877)<br>`79233#1` (0.8795)<br>`79233#5` (0.8041) | 2/2 | 0/2 | **Đạt Top-1 đúng tài liệu gold `79233`**. Chunk 1 chứa trọn Bước 1, 2, 3; các bước 4-8 bị cắt sang chunk sau do giới hạn kích thước 500 ký tự. |
| 3 | `79467#2` (0.8527)<br>`79467#3` (0.8353)<br>`79467#4` (0.7517) | 2/2 | 0/2 | **Đạt Top-1 đúng tài liệu gold `79467`**. Khớp 5/8 từ khóa quy định: *liên tục, không bị cắt ghép, 6 mặt, mã vận đơn, niêm phong*. |
| 4 | `79233#5` (0.7377)<br>`79233#0` (0.7334)<br>`79233#1` (0.6875) | 0/2 | 0/2 | Câu hỏi 4 thuộc tài liệu `189477` (phần thành viên khác phụ trách, ngoài phạm vi 2 file cá nhân). |
| 5 | `79233#5` (0.7946)<br>`79233#0` (0.7801)<br>`79233#4` (0.7716) | 2/2 | 2/2 | **Đạt 2/2 điểm tuyệt đối!** Top-1 trích xuất đúng `79233`, chứa đầy đủ bằng chứng cả 2 mốc thời gian: *3 - 5 ngày làm việc* và *1 - 14 ngày làm việc*. |

**Phân tích kết quả thực nghiệm:** 
- Trên phạm vi các câu hỏi thuộc 2 tài liệu cá nhân phụ trách (Câu 2, Câu 3, Câu 5), chiến lược `FixedSizeChunker(500, 50)` kết hợp `GeminiEmbedder` đạt **tỷ lệ trích xuất đúng tài liệu chuẩn 100% (3/3 câu đạt Rank 1)** với độ tương tự Cosine thực tế rất cao (từ 0.7946 đến 0.8877). 
- Câu 5 đạt điểm nội dung tuyệt đối (2/2 điểm) nhờ độ dài chunk 500 ký tự gom trọn vẹn cả đoạn điều khoản thời gian xử lý và thời gian nhận tiền hoàn của Shopee.
- Câu 1 và Câu 4 đạt 0 điểm do ranh giới dữ liệu thực nghiệm cá nhân (tài liệu gold thuộc phần thu thập của thành viên khác trong nhóm).

### A/B câu 5 trên ba chiến lược (Dữ liệu thực nghiệm Gemini)

| Chiến lược | Filter | Top-3 (score) | Điểm nội dung |
|---|---|---|---|
| FixedSizeChunker(500, 50) | Không | `79233#5` (0.7946)<br>`79233#0` (0.7801)<br>`79233#4` (0.7716) | **2/2** |
| FixedSizeChunker(500, 50) | buyer | `79233#5` (0.7946)<br>`79233#0` (0.7801)<br>`79233#4` (0.7716) | **2/2** |
| SentenceChunker(3) | Không | `79233#6` (0.8098)<br>`79233#0` (0.7794)<br>`79233#5` (0.7445) | **2/2** |
| SentenceChunker(3) | buyer | `79233#6` (0.8098)<br>`79233#0` (0.7794)<br>`79233#5` (0.7445) | **2/2** |
| RecursiveChunker(500) | Không | `79233#4` (0.7896)<br>`79233#0` (0.7814)<br>`79233#1` (0.7203) | **0/2** |
| RecursiveChunker(500) | buyer | `79233#4` (0.7896)<br>`79233#0` (0.7814)<br>`79233#1` (0.7203) | **0/2** |

Thực nghiệm A/B cho thấy:
1. `FixedSizeChunker(500, 50)` và `SentenceChunker(3)` đều đạt điểm nội dung tối đa **2/2** trên Câu 5, giữ trọn vẹn ngữ cảnh thời gian.
2. `RecursiveChunker(500)` không đạt điểm nội dung (0/2) do phân tách theo dấu đoạn `\n\n` vô tình chia mốc thời gian xử lý khiếu nại (3 - 5 ngày) và thời gian hoàn tiền (1 - 14 ngày) vào hai chunk độc lập, khiến không có chunk đơn lẻ nào chứa đủ cả 2 thông số.
3. Cả 2 tài liệu đều có `audience: buyer` nên bộ lọc metadata duy trì độ chính xác 100% mà không làm thất thoát kết quả.

### Failure case và phân tích

Tại **Câu hỏi số 2** (hướng dẫn 8 bước gửi yêu cầu), mặc dù mô hình tìm đúng tài liệu `79233` ở Top-1 với điểm tương tự 0.8877, điểm nội dung vẫn là 0/2 do chỉ có Bước 1, Bước 2, Bước 3 nằm trong chunk đầu tiên (`79233#1`), còn các Bước 4 đến Bước 8 bị đẩy sang chunk tiếp theo.
- **Nguyên nhân kỹ thuật:** Kích thước cửa sổ `chunk_size=500` ký tự quá nhỏ so với tổng chiều dài văn bản của một quy trình 8 bước (~950 ký tự).
- **Giải pháp cải tiến:** Nâng `chunk_size` lên 1000 ký tự đối với các tài liệu hướng dẫn quy trình dạng danh sách bước, hoặc ứng dụng Section/Heading Chunking để gom toàn bộ một tiểu mục quy trình thành một đơn vị ngữ nghĩa trọn vẹn.

**Đánh giá chiến lược FixedSizeChunker(500, 50):** Phương pháp này đảm bảo tính ổn định cao về kích thước bộ nhớ, tốc độ chunking nhanh nhất (tạo ra 14 chunks gọn gàng từ 2 tài liệu). Cơ chế trượt cửa sổ với độ chồng chéo 50 ký tự (`overlap`) phát huy hiệu quả tốt ở Câu 5 khi kết nối liền mạch các câu quy định thời hạn. Hạn chế tự nhiên là nguy cơ chia cắt quy trình dài nhiều bước (như Câu 2).

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) |5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10/ 10 |
| Hoàn thiện code (Core Implementation — tests) | 30/ 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5/ 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8/ 10 |
| **Tổng phần cá nhân** | 58/ 60** |

