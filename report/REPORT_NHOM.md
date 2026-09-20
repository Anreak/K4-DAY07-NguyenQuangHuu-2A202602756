# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Four bot\
**Thành viên:**
- Nguyễn Quang Hữu (Tài liệu 3, 4 & Chiến lược FixedSizeChunker)
- Nguyễn Nhật Thăng
- Nguyễn Minh Quyền
- Vương Việt Hoàng\
**Ngày:** 20/9/2026\

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách thương mại điện tử

**Tại sao nhóm chọn chủ đề này?**
> Shopee là nền tảng thương mại điện tử hàng đầu tại Việt Nam với hệ thống chính sách, quy định pháp lý và quy trình dịch vụ khách hàng rất phong phú, rõ ràng. Bộ dữ liệu này có sự phân hóa đối tượng sâu sắc giữa Người Mua (`buyer`) và Người Bán (`seller`), đồng thời có cấu trúc phân tầng theo điều khoản, số ngày, mốc thời gian và yêu cầu kỹ thuật cụ thể. Đây là ngữ liệu hoàn hảo để kiểm nghiệm khả năng chia nhỏ văn bản (chunking) và chứng minh sức mạnh của bộ lọc siêu dữ liệu (metadata filtering) trong hệ thống RAG thực tế.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | CHÍNH SÁCH TRẢ HÀNG VÀ HOÀN TIỀN | https://help.shopee.vn/portal/4/article/77251 | 2026-09-20 / not-stated | 19,637 | audience=both, category=returns-policy, language=vi |
| 2 | [Trả hàng/Hoàn tiền] Những quy định chung về Trả hàng/Hoàn tiền của Shopee | https://help.shopee.vn/portal/4/article/188931 | 2026-09-20 / not-stated | 6,378 | audience=buyer, category=returns-policy, language=vi |
| 3 | [Trả hàng/ Hoàn tiền] Hướng dẫn gửi yêu cầu Trả hàng/ Hoàn tiền | https://help.shopee.vn/portal/4/article/79233 | 2026-09-20 / not-stated | 2,570 | audience=buyer, category=returns-process, language=vi |
| 4 | [Trả hàng/Hoàn tiền] Hướng dẫn chuẩn bị bằng chứng khi yêu cầu Trả hàng/ Hoàn tiền | https://help.shopee.vn/portal/4/article/79467 | 2026-09-20 / not-stated | 3,519 | audience=buyer, category=returns-process, language=vi |
| 5 | [Trả hàng/ Hoàn tiền] Các phương thức gửi hàng hoàn trả và phí hoàn trả | https://help.shopee.vn/portal/4/article/189477 | 2026-09-20 / not-stated | 5,980 | audience=buyer, category=shipping-fee, language=vi |
| 6 | QUY CHẾ HOẠT ĐỘNG SÀN THƯƠNG MẠI ĐIỆN TỬ SHOPEE.VN | https://help.shopee.vn/portal/4/article/77245 | 2026-09-20 / not-stated | 77,900 | audience=both, category=platform-regulation, language=vi |
| 7 | QUY ĐỊNH VỀ ĐĂNG BÁN SẢN PHẨM TRÊN SHOPEE | https://help.shopee.vn/portal/4/article/77246 | 2026-09-20 / not-stated | 21,560 | audience=seller, category=seller-policy, language=vi |
| 8 | CHÍNH SÁCH CẤM/HẠN CHẾ SẢN PHẨM | https://help.shopee.vn/portal/4/article/77247 | 2026-09-20 / not-stated | 12,878 | audience=seller, category=product-restriction, language=vi |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng từ Trung tâm hỗ trợ Shopee Việt Nam (`help.shopee.vn`), không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có đầy đủ `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience` trong metadata. File `sources.csv` khớp một-một với các file `.md`.

### Cấu trúc Metadata (Metadata Schema)

**Nguồn của nhãn:** audience/category/language được nhóm bổ sung dựa trên đối tượng và chủ đề tài liệu. Bản crawl gốc chỉ có 5 trường nguồn; các nhãn bổ sung không thay đổi nội dung chính sách. Lab yêu cầu audience và ít nhất một trường hữu ích khác, không bắt buộc đồng thời cả category và language.

Ba nơi lưu thông tin có vai trò khác nhau:

- `data/urls.csv`: đầu vào crawler, hiện gồm **8 nguồn của nhóm**; các cột `url,doc_id,title,audience,category,language,document_version,license_or_permission`.
- `data/Chinh_sach_thuong_mai_dien_tu/sources.csv`: kiểm kê **8 file đã thu thập**, đúng schema của `docs/DATA_COLLECTION.md`: `doc_id,file_path,title,source_url,retrieved_at,document_version,license_or_permission`. `file_path` tính từ gốc repo và phải tồn tại. Không yêu cầu manifest có cùng header với CSV đầu vào.
- Frontmatter từng `.md`: metadata tài liệu dùng khi ingest. Crawler ánh xạ `url` thành `source_url`, thêm `retrieved_at`; `audience/category/language` nằm trong frontmatter. `license_or_permission` được giữ trong CSV để ghi căn cứ sử dụng, không mặc định là trường lọc.

`document_version=not-stated` nghĩa là chưa xác định được phiên bản/ngày hiệu lực từ nguồn lưu; không lấy năm thu thập làm phiên bản chính sách. `retrieved_at` là ngày thu thập đã ghi, không phải ngày chính sách có hiệu lực. Số ký tự trong bảng được tính trên phần thân Markdown, gồm tiêu đề, sau `strip()`, không gồm YAML frontmatter.

Khi ingest, mọi chunk kế thừa metadata nguồn; `Document.id=<doc_id>#<index>`, `metadata.doc_id` vẫn là ID file gốc và `chunk_index` là số thứ tự từ 0. Filter `audience=buyer` chỉ khớp `buyer`, không bao gồm `both`.


| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `79233` | Định danh duy nhất cho tài liệu, phục vụ việc quản lý, liên kết chunk và xóa tài liệu (`delete_document`). |
| `title` | string | `[Trả hàng/ Hoàn tiền] Hướng dẫn gửi yêu cầu Trả hàng/ Hoàn tiền` | Hiển thị tiêu đề chuẩn cho người dùng và hỗ trợ kiểm tra ngữ cảnh nguồn. |
| `source_url` | string | `https://help.shopee.vn/portal/4/article/79233` | Minh bạch nguồn gốc, cho phép Agent trích dẫn URL chính thức (Source Traceability). |
| `retrieved_at` | string (date) | `2026-09-20` | Kiểm soát ngày thu thập, đánh giá độ mới của chính sách sàn TMĐT. |
| `document_version` | string | `not-stated` | Phiên bản/ngày hiệu lực từ nguồn; dùng `not-stated` khi chưa xác định được. |
| `audience` | string | `buyer`, `seller`, `both` | Phân biệt đối tượng áp dụng. Đây là trường quyết định để lọc metadata tránh nhầm lẫn giữa quy định cho Người Mua và Người Bán. |
| `category` | string | `returns-process`, `shipping-fee`, `seller-policy` | Phân loại mảng chính sách, giúp thu hẹp không gian tìm kiếm khi người dùng hỏi về chủ đề chuyên biệt. |
| `language` | string | `vi` | Phục vụ lọc theo ngôn ngữ tiếng Việt. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(body, chunk_size=300)` trên phần thân đã bỏ frontmatter: FixedSize overlap=30, Sentence tối đa 3 câu/chunk, Recursive size=300. Đây là baseline riêng, khác cấu hình cá nhân 500/50. Số liệu sau được chạy lại trên bản crawl mới (chỉ bổ sung nhãn frontmatter, giữ nguyên phần thân); xem log benchmark.

| Tài liệu | Chiến lược | Số chunk | Độ dài trung bình |
|---|---|---|---|
| `188931` | `fixed_size` | 24 | 294.5 |
| `188931` | `by_sentences` | 10 | 632.8 |
| `188931` | `recursive` | 27 | 234.3 |
| `79233` | `fixed_size` | 10 | 284.0 |
| `79233` | `by_sentences` | 8 | 317.8 |
| `79233` | `recursive` | 10 | 255.2 |
| `79467` | `fixed_size` | 13 | 298.4 |
| `79467` | `by_sentences` | 12 | 290.2 |
| `79467` | `recursive` | 15 | 232.7 |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Quang Hữu (Cá nhân)**
- **Loại chiến lược:** FixedSizeChunker (cửa sổ trượt)
- **Mô tả & lý do chọn cho chủ đề này:**
  > Cấu hình `chunk_size=500`, `overlap=50`. Lựa chọn chiến lược chia nhỏ theo kích thước cố định để kiểm tra tính hiệu quả của phương pháp đường cơ sở (baseline). Độ chồng chéo 50 ký tự được kỳ vọng sẽ bảo toàn các từ khóa và ngữ cảnh giáp ranh giữa hai chunk liên tiếp khi trích xuất dữ liệu từ các tài liệu hướng dẫn quy trình Shopee.

**Thành viên 2 — Nguyễn Nhật Thăng**
- **Loại chiến lược:** [Thành viên tự chọn & điền]
- **Mô tả & lý do chọn:** *(Thành viên tự điền 2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (nếu có)
```

**Thành viên 3 — Nguyễn Minh Quyền**
- **Loại chiến lược:** [Thành viên tự chọn & điền]
- **Mô tả & lý do chọn:** *(Thành viên tự điền 2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (nếu có)
```

**Thành viên 4 — Vương Việt Hoàng**
- **Loại chiến lược:** [Thành viên tự chọn & điền]
- **Mô tả & lý do chọn:** *(Thành viên tự điền 2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (nếu có)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| **Nguyễn Quang Hữu** | FixedSizeChunker (overlap=50) | Chưa chốt; 0/5 câu có chunk chứa đáp án với Mock | Cài đặt đơn giản, tốc độ thực thi nhanh, có overlap nối ranh giới | Cắt ngẫu nhiên giữa câu từ, dễ làm đứt đoạn câu điều khoản |
| **Nguyễn Nhật Thăng** | [Chờ kết quả chạy] | /10 | [Thành viên tự điền] | [Thành viên tự điền] |
| **Nguyễn Minh Quyền** | [Chờ kết quả chạy] | /10 | [Thành viên tự điền] | [Thành viên tự điền] |
| **Vương Việt Hoàng** | [Chờ kết quả chạy] | /10 | [Thành viên tự điền] | [Thành viên tự điền] |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *[Nhóm sẽ thảo luận và thống nhất đánh giá sau khi cả 4 thành viên hoàn thành việc chạy benchmark riêng]*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có thời hạn bao nhiêu ngày kể từ khi đơn hàng giao thành công để gửi yêu cầu Trả hàng/Hoàn tiền đối với hàng thông thường và thực phẩm tươi sống? | Người mua có 15 ngày kể từ khi giao hàng thành công để gửi yêu cầu; riêng thực phẩm tươi sống và đông lạnh chỉ có thời hạn 24 giờ. | `188931.md` & `77251.md` (Điều 3.2) |
| 2 | Người mua có thể gửi yêu cầu Trả hàng/Hoàn tiền trực tiếp từ trang đơn hàng trên ứng dụng Shopee theo các bước như thế nào? | Bước 1: Mở app > Tôi > Chờ giao hàng/Đã giao; Bước 2: Bấm Trả hàng/Hoàn tiền; Bước 3: Chọn tình huống; Bước 4: Chọn sản phẩm; Bước 5: Chọn lý do; Bước 6: Chọn phương án; Bước 7: Điền mô tả, tải ảnh/video bằng chứng, email; Bước 8: Gửi yêu cầu. | `79233.md` (Mục 1, Cách 1) |
| 3 | Khi khiếu nại hàng bị bể vỡ hoặc lỗi, video mở kiện hàng của Người mua cần đáp ứng những tiêu chuẩn kỹ thuật nào về cách quay và dung lượng? | Video phải quay liên tục không cắt ghép, rõ nét, thấy 6 mặt kiện hàng, thấy rõ mã vận đơn và tem niêm phong. Dung lượng tối đa: video không quá 100MB (tối đa 1 phút), ảnh không quá 5MB/ảnh. | `79467.md` (Mục 2 và Mục 4) |
| 4 | Người mua có phải trả phí vận chuyển khi gửi hàng hoàn trả về cho Người bán không? | Người mua được miễn phí ship hoàn về nếu chọn hình thức "Lấy hàng tại nhà" hoặc "Gửi hàng tại bưu cục" liên kết với Shopee; nếu tự sắp xếp thì thanh toán trước và Shopee hỗ trợ hoàn lại sau. | `189477.md` (Mục 1 và 2) |
| 5 | Thời gian xử lý yêu cầu Trả hàng / Hoàn tiền là bao lâu? *(Cần filter `audience: buyer`)* | Đối với Người mua, yêu cầu Trả hàng/Hoàn tiền thường được Shopee xử lý trong khoảng 3 - 5 ngày làm việc; thời gian nhận tiền hoàn từ 1 - 14 ngày làm việc. | `79233.md` (Mục 2) |

### Tổng hợp chất lượng truy xuất của nhóm

Nguyễn Quang Hữu đã chạy lại bản crawl mới: 8 tài liệu, 337 chunks FixedSize 500/50, MockEmbedder. Cả 5 câu chưa có đủ chuỗi bằng chứng trong ngữ cảnh gold; điểm nội dung 0/10, không phải điểm cuối cùng cho toàn bộ phần benchmark cá nhân. Agent đang dùng stub nên chưa chấm chất lượng câu trả lời.

A/B câu 5 đã chạy trên FixedSize, Sentence và Recursive; bảng top-3/score có ở báo cáo cá nhân mục 5, nội dung đầy đủ ở `ket_qua_benchmark.txt`. Cả ba có thay đổi top-3 khi lọc nhưng chưa lấy đủ đáp án. Chưa chứng minh điều kiện “filter giúp trả lời đúng”; cần kiểm chứng bằng embedding thật. Nhãn audience là phân loại do nhóm gán, không phải metadata do website cung cấp.

Kết quả chạy ba chunker phục vụ A/B kỹ thuật, không thay thế phần chiến lược hoặc kết quả của thành viên khác. Chưa kết luận chiến lược tốt nhất.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Nội dung có thể trình bày từ bằng chứng hiện có:**
1. Quy trình ingest: tách frontmatter, giữ metadata trên từng chunk, truy vết bằng doc_id và chunk ID.
2. A/B filter câu 5 thay đổi ứng viên nhưng chưa lấy đúng đáp án; phân tích đánh đổi khi loại `both`.
3. Failure case câu 1: top-1 `77246#11` nói về hình ảnh đăng bán, không có thời hạn 15 ngày/24 giờ. Mock không có ngữ nghĩa, nên chưa thể kết luận chunking là nguyên nhân chính.

**Bài học rút ra khi so sánh trong nhóm:** Chờ kết quả và demo thực tế của các thành viên; không khẳng định Heading tốt nhất khi chưa có log so sánh.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ:
> 1. Xây dựng bộ parser Markdown chi tiết hơn để bóc tách riêng các bảng biểu quy định thời gian (như bảng thời gian hoàn tiền theo từng ngân hàng) thành các cặp Key-Value có cấu trúc trước khi chunk.
> 2. Bổ sung thêm metadata `product_type` (thực phẩm, điện tử, thời trang) vì chính sách đổi trả Shopee có những ngoại lệ rất ngặt nghèo theo từng ngành hàng.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | Đủ 8 nguồn và manifest; cần rà soát nguồn/ngoại lệ khi chốt gold |
| Thiết kế chiến lược (Strategy Design) | Chờ so sánh đủ thành viên |
| Chất lượng truy xuất (Retrieval Quality) | Chưa đạt với Mock; chưa chấm câu trả lời LLM |
| Thuyết trình (Demo) | Chờ demo thực tế |
| **Tổng phần nhóm** | **Chưa chốt** |
