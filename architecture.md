# Architecture & Design Notes — SceneSeek

Tài liệu này giải thích chi tiết thiết kế kỹ thuật hệ thống, dành cho người phát triển/duy trì project.

> **Bối cảnh dataset**: 838 video từ Hội thi AI Challenge HCMC 2026, trải nhiều chủ đề khác nhau (tin tức thời sự, thi múa lân, dạy nấu ăn, ôn thi online, phim tài liệu ngắn...). Điều này ảnh hưởng tới vài quyết định thiết kế đáng chú ý: `vocab` cho keyword extraction (§4.1) cần phủ được từ vựng đa domain thay vì chuyên biệt 1 lĩnh vực; và việc chọn model tổng quát (Jina CLIP v2, dangvantuan) thay vì fine-tune riêng cho 1 loại nội dung là hợp lý vì input quá đa dạng để tối ưu cho 1 domain cụ thể.

## 1. Tổng quan luồng hệ thống

```
Frontend (React)
   │  REST call qua sceneseek-frontend/src/api/client.js
   │  (fallback mock nếu backend trả 501 / network error)
   ▼
FastAPI routers
   ├── search_router.py  → 3 loại retrieval + similar frame
   ├── data_router.py    → browse keyframe theo timestamp
   └── event_router.py   → browse event theo event_id
   │
   ▼
tools/search_utils.py  → logic search/cluster/merge chính
   │
   ├── tools/query_encoding.py  → encode text (jina-clip-v2 / dangvantuan)
   └── tools/faiss_retrieval.py → wrapper generic cho FAISS index.search()
   │
   ▼
model_state.py (state toàn cục: model đã load, FAISS index, info_dict...)
   → inject vào router qua deps.py (Depends pattern, không import model_state trực tiếp trong router)
```

**Convention quan trọng**: mọi hàm trong `search_utils.py` nhận `index`/`device`/`info_dict` như **tham số** (mặc định lấy từ `model_state` nếu không truyền) — để router gọi qua `Depends()` (dễ mock khi test), đồng thời notebook/script độc lập vẫn gọi được bình thường không cần sửa gì.

## 2. Data Loading & Model Initialization

Toàn bộ model và index được load **một lần duy nhất khi `model_state.py` được import** (module-level, không load lại mỗi request), theo đúng pattern của `state.py` (dataset). Router không import `model_state` trực tiếp mà nhận qua `Depends()` trong `deps.py` — tách biệt "nơi lưu state" khỏi "nơi dùng state", dễ mock khi test.

### 2.1. Config-driven loading

Hai file config điều khiển toàn bộ việc load:
- `config/databases.json`: đường dẫn tới từng FAISS index, info dict, encoded frames, BM25 pickle, vocab, query cache DB — mỗi database có 1 key riêng (`hnsw_jinaclipv2`, `flatip_dangvantuan`, `bm25_flatip_dangvantuan`...).
- `config/models.json`: map tên model nội bộ (`jina-clip-v2`, `dangvantuan`) → model identifier thật trên HuggingFace (`jinaai/jina-clip-v2`, `dangvantuan/vietnamese-embedding`).

→ Đổi model/dataset chỉ cần sửa JSON, không cần sửa code load (`db_init.py`, `model_init.py` đọc config động qua `database_name`/`model_name`).

### 2.2. Model loading (`models/model_init.py`)

- Tự động chọn `cuda` nếu có, fallback `cpu`.
- 2 nhánh loader khác nhau vì 2 model dùng framework khác nhau: Jina CLIP v2 qua `transformers.AutoModel` (`trust_remote_code=True`, fp16 trên GPU), dangvantuan qua `sentence_transformers.SentenceTransformer`.
- `model_state.py` có check `_DANGVANTUAN_DEVICE != DEVICE` — nếu 2 model vô tình load lên device khác nhau (hiếm nhưng có thể xảy ra tuỳ config), log warning và **ưu tiên dùng device của Jina CLIP v2** làm `DEVICE` chung cho toàn hệ thống, thay vì raise lỗi cứng.

### 2.3. Index loading (`database/db_init.py`)

- `faiss_database_processing()`: dùng chung cho cả HNSW và FlatIP (đọc `index_type` từ config để set thêm tham số riêng, VD: `hnsw.efSearch = 128` chỉ áp dụng khi `index_type == "hnsw"`). Có `assert index.ntotal == len(image_info_dict)` ngay khi load — fail sớm (fail-fast) nếu index và metadata bị lệch nhau thay vì lỗi ngầm lúc search.
- `load_bm25_flatip_dangvantuan()`: **không lưu file `.index` riêng** — build FAISS FlatIP từ `embeddings.pt` ngay lúc khởi động, vì build lại từ vector mất vài giây kể cả với hàng trăm nghìn vector, không đáng để maintain thêm 1 file binary.
- `load_bm25_database()`: deserialize thẳng object `BM25Okapi` đã fit sẵn từ `.pkl` — không re-fit lúc khởi động.

### 2.4. Chuẩn hoá `event_id` (quan trọng)

Dữ liệu event thô (`EVENT_TRANSCRIPTS`) có `event_id` **không local per video** và có thể có gap (VD quan sát thực tế: `L21_V014` có event_id `[0, 6, 16, 26, 44, ...]` thay vì liên tục) — do transcript được gộp từ nhiều nguồn/batch khác nhau.

`model_state.py` xử lý lại **một lần duy nhất tại đây** để mọi nơi khác (đặc biệt `event_router.py` và frontend) có thể giả định an toàn "event_id luôn reset về 0, liên tục, theo từng video":
- Sort toàn bộ event theo `(video_id, start)` trước.
- Duyệt qua, bỏ qua event thiếu `video_id` hoặc không resolve được frame nào qua `state.FRAME_BY_PATH` (không tốn 1 local id).
- Gán lại `event_id` mới = local, 0-based, gap-free theo thứ tự duyệt (giả định thứ tự này đã chronological vì raw event_id tăng dần trong data gốc).
- `source_event_id` (id gốc) vẫn được giữ lại riêng để debug/truy vết, không dùng cho logic filter.

→ Đây là lý do vì sao `event_router.py` (đã xem ở phần 5.2) có thể an toàn giả định "event_id local per video" — điểm giả định đó được **đảm bảo đúng tại nguồn** (`model_state.py`), không phải tự nhiên mà đúng.

### 2.5. Data-completeness check (soft, không hard-crash)

Sau khi build xong `ALL_EVENTS`, `model_state.py` kiểm tra: mọi `frame_path` được tham chiếu trong các event (FLATIP_DANGVANTUAN) có tồn tại trong `FRAME_PATH_TO_ROW` (dẫn xuất từ HNSW_JINACLIPV2) hay không — vì hệ thống ngầm giả định "HNSW bao phủ toàn bộ frame mà FLATIP tham chiếu tới".

Nếu thiếu, chỉ **log warning**, không raise lỗi — vì đây là vấn đề *độ đầy đủ của dữ liệu* (data completeness), không phải *lỗi schema*, nên không nên chặn cả hệ thống khởi động vì 1 vài frame thiếu. Cách tiếp cận này khác với `assert index.ntotal == len(image_info_dict)` ở trên — đó là lỗi cấu trúc bắt buộc phải chặn ngay.

## 3. Ba loại Retrieval

### 3.1. Type 1 — Frame Search (`/api/search/frame`)

Text-image search đơn giản nhất: encode query → search HNSW → enrich → sort.

- Model: **Jina CLIP v2** (text và image cùng chung không gian embedding).
- Index: FAISS **HNSW** (approximate nearest neighbor, đánh đổi tốc độ lấy độ chính xác gần đúng — phù hợp vì dataset chỉ cần "đủ tốt" cho browsing tương tác, không cần exact search).
- Route có xử lý `req.keywords` (nối trực tiếp vào cuối query text trước khi encode), nhưng UI hiện tại (`queryTypes.js`, `supportsKeywords: false` cho Type 1) không expose field này cho user — xem note ở §3.3 để biết vì sao đây là thiết kế nhất quán, không phải logic thừa.
- 3 chế độ sắp xếp (`sort_results`, `displayOption`):
  - `sort_by_score`: sắp theo distance tăng dần.
  - `sort_by_frame_index`: **giữ nguyên thứ tự FAISS trả về** (không sort lại theo frame_idx — đây là hành vi cố ý, khớp với notebook gốc).
  - `group_by_videoid`: nhóm theo video, xếp hạng video bằng `_video_ranking_score` (trung bình distance có trọng số theo vị trí trong top-k, nhân thêm `log2(n+1)` hoặc nghịch đảo tuỳ `higher_is_better`), rồi flatten lại — **giữ nguyên shape** để frontend (`GalleryItem.jsx`) không cần biết displayOption là gì.

### 3.2. Type 2 — Event Boundary Search (`/api/search/event-boundary`)

Đây là phần thuật toán phức tạp nhất hệ thống.

**Input**: 2–5 query text, theo đúng thứ tự thời gian người dùng muốn (channel 0 = cảnh sớm nhất, channel N-1 = cảnh muộn nhất).

**Validation ở router**:
- Bắt buộc 2 ≤ n ≤ 5.
- Nếu `strict=False` (tìm tương đối): bắt buộc n ≥ 3 (vì N=2 mà cho phép bỏ 1 cảnh thì chỉ còn 1 cảnh — vô nghĩa), và `minOccurrences` phải nằm trong `[2, n-1]`.

**Thuật toán cốt lõi — `_best_ordered_chain` (trong `search_utils.py`)**:
- Với mỗi video, gom tất cả candidate frame từ mọi channel lại, sort theo `frame_idx` tăng dần.
- Bài toán: tìm chuỗi con (subsequence) mà **channel index tăng chặt (strictly increasing)** dọc theo thời gian — tương đương "Longest Increasing Subsequence" nhưng tối ưu đồng thời 2 tiêu chí:
  1. Số channel khớp nhiều nhất (primary).
  2. Tổng distance nhỏ nhất trong các chain có cùng số channel (tie-break).
- Cài đặt: DP với parent-pointer, độ phức tạp O(m²) trên m candidate của từng video, dựng lại chain bằng cách truy vết `parent[]` ở cuối.
- Điều kiện "channel tăng chặt" đảm bảo mỗi channel chỉ xuất hiện tối đa 1 lần trong chain, và nhờ tính bắc cầu (transitivity) nên không cần kiểm tra trùng lặp channel thủ công.

**Điều kiện chấp nhận cluster** (`cluster_by_video`):
- `strict=True`: bắt buộc `effective_min_occurrences = n_channels` (khớp đủ mọi cảnh).
- `strict=False`: mặc định `max(2, n_channels - 1)` nếu không truyền `minOccurrences` — cho phép thiếu tối đa 1 cảnh, dung sai cho encoding/search không hoàn hảo.
- `start_idx == end_idx` → loại (không tạo được đoạn thời gian thật sự).

**Output**: mỗi cluster gồm `frames` (toàn bộ frame thật trong khoảng `[start_idx, end_idx]` của video, không chỉ các frame khớp), `matched_channels`, và `missing_channels` (kèm lý do: `no_match_in_video` hoặc `excluded_by_ordering` — hữu ích để debug tại sao 1 cảnh không được chọn dù có candidate).

**Sắp xếp cluster**: số channel khớp giảm dần → rồi theo `score` (tổng distance) tăng dần. `displayOption` bị **bỏ qua** ở route này (frontend hard-code `sort_by_frame_index` cho Type 2) — trong cluster, frame đã tự sort theo `frame_idx`.

### 3.3. Type 3 — Event Mention Search (`/api/search/event-mention`)

Text-text search trên transcript đã segment thành event.

**Không có keyword** → `search_flatip_dangvantuan_batch`:
- Encode bằng model **dangvantuan** (Vietnamese sentence embedding).
- Search FAISS FlatIP (exact search, vì dùng Inner Product = cosine similarity khi vector đã normalize).
- Over-fetch `k * fetch_multiplier` candidate rồi dedupe theo `(video_id, event_id)` — cần thiết vì 1 event có thể bị split thành nhiều chunk/vector khác nhau trong index.

**Có keyword** → `search_hybrid_bm25_flatip_batch`:
- Nhánh dense: giống trên nhưng dùng index `BM25_FLATIP_DANGVANTUAN`.
- Nhánh keyword: `bm25_search_batch` — tokenize bằng `pyvi` (phải khớp đúng cách tokenize lúc build index BM25), lấy top-k bằng `argpartition` (tránh sort toàn bộ mảng score không cần thiết), loại bỏ score ≤ 0 (không có từ khoá khớp).
- Merge 2 nhánh bằng **Reciprocal Rank Fusion (RRF)**: `score = Σ 1/(k_const + rank)` cho mỗi nhánh, dedupe theo `(video_id, event_id)`, ưu tiên payload của nhánh dense nếu trùng key. `k_const=60` là giá trị chuẩn trong literature, ít nhạy với thay đổi nhỏ.

> **Note**: Ở tầng UI, `keywords` **chỉ được expose cho Type 3** — theo `queryTypes.js` (`supportsKeywords: false` ở Type 1/2, `true` ở Type 3 duy nhất). Đây là quyết định scope có chủ đích cho MVP: Type 3 dùng text-text search trên transcript, nên keyword đơn giản là match/boost trực tiếp trên văn bản (dễ thiết kế, dễ kiểm chứng chất lượng). Type 1/2 dùng text-image search — keyword ở đây sẽ phải "boost" trong không gian embedding hình ảnh, một bài toán mơ hồ hơn (thế nào là 1 từ khoá "khớp" với 1 frame ảnh?), nên tạm để dành phát triển sau.
>
> Vì vậy logic xử lý `req.keywords` trong route Type 1 (`search_frame`, nối thẳng vào query) hiện tồn tại như một bước chuẩn bị cho hướng phát triển tương lai đó — route vẫn nhận và xử lý được nếu gọi trực tiếp, nhưng chưa có UI chính thức nào gửi field này lên.

**Sắp xếp**: cả 2 nhánh đều sort theo score giảm dần (cao hơn = tốt hơn, vì dùng Inner Product/cosine similarity) — **khác với Type 2** dùng L2 distance (thấp hơn = tốt hơn). Đây là điểm dễ gây bug nếu copy nhầm logic sort giữa 2 route — code đã note rõ để tránh reverse ranking nhầm.

### 3.4. Similar Frame Search (`/api/search/similar/{db_idx}`)

Không dùng FAISS — dùng trực tiếp `torch.cosine_similarity` + `torch.topk` trên toàn bộ `encoded_frames` đã preload trong `model_state`.

- Lý do không re-encode: frame đã có embedding sẵn trong index, tận dụng lại để tránh gọi model lần nữa (nhanh hơn, nhất quán hơn).
- Join `frame_path` giữa `info_dict` (dùng tên field gốc từ JSON annotation) và `state.ALL_FRAMES` (tên field đã normalize, có `db_idx`) — 2 hệ thống field name khác nhau cần map qua lại (`_FRAME_PATH_TO_DB_IDX`, `frame_path_to_row`).
- Kết quả loại bỏ chính frame query (cosine similarity = 1 với chính nó), lấy `top_k + 1` để bù trừ trước khi loại.

## 4. Keyword Suggestion (`/api/process_query`)

Route hỗ trợ gợi ý keyword cho ô tìm kiếm (frontend gọi qua `getKeywordSuggestions` trong `client.js`), tách biệt hoàn toàn khỏi 3 route retrieval — không dùng FAISS/embedding, chỉ xử lý rule-based trên chính câu query.

### 4.1. Pipeline trích xuất keyword (`keywords_utils.py`)

Thiết kế theo 2 tầng, ưu tiên tầng 1 trước:

1. **`rule_based_keyword_extractor`**: sinh n-gram (từ độ dài `max_ngram=4` giảm dần) từ query đã qua `ViTokenizer`, đối chiếu với `vocab` (tập từ khoá đã biết trước, load từ `model_state.KEYWORDS_RESOURCES`). Ưu tiên khớp cụm dài trước để tránh cắt vụn cụm từ có nghĩa (VD: ưu tiên khớp "xe máy màu đỏ" trước khi thử khớp "xe máy" hay "màu đỏ" riêng lẻ).
2. **`fallback_phrase_extractor`**: nếu tầng 1 không khớp gì (vocab không phủ được), fallback sang trích cụm từ trực tiếp bằng POS tagging (`ViPosTagger`), chỉ giữ các tag trong `FALLBACK_POS_TAGS = {N, Np, Ny, A}` (danh từ/tên riêng/tính từ liên tiếp). Có lọc phrase bị chứa trong phrase khác (`p in q`) để tránh trùng lặp con-cha.

`rule_based_with_fallback_extractor` gộp 2 tầng lại — đây là hàm thực tế được dùng trong `get_keywords()`.

> **Thiết kế mở rộng**: `get_or_generate_query_keywords()` nhận `generate_fn` như một tham số callback — hiện đang truyền `rule_based_with_fallback_extractor`, nhưng comment trong code ghi rõ đây là **điểm duy nhất cần đổi** khi muốn chuyển sang LLM-based keyword generation sau này (VD: gọi Claude Haiku), không cần sửa logic cache.

### 4.2. Cache layer (SQLite)

- Cache theo key = MD5 hash của query đã normalize (lowercase + gộp whitespace) — **không** bỏ dấu hay lọc stopword ở bước normalize này (cố ý, để tránh 2 câu khác nghĩa nhưng giống nhau sau khi bỏ dấu bị coi là cùng 1 cache entry).
- Cache hit → tăng `hit_count` (phục vụ phân tích query phổ biến sau này) và trả kết quả đã lưu, không tính toán lại.
- Cache miss → chạy `generate_fn`, lưu kết quả kèm `gen_method` (`"none"` hoặc `"rule_based"`) và `gen_model` (nhãn để audit/so sánh khi đổi phương pháp — hiện là `"rule_based_v1"`).
- Vì gọi `sqlite3.connect()` mỗi request (không giữ connection pool), phù hợp cho MVP nhưng cần lưu ý nếu tải tăng cao (xem mục Open Questions).

## 5. Browse & Verify Layer

Mục đích: cho phép user xác nhận nhanh kết quả (giảm false positive) mà không cần chạy lại retrieval.

### 5.1. Data Browser (`/api/data`)
- Lọc theo `video_ID` (exact `"L21_V001"` hoặc prefix `"L21"` gộp nhiều video) + khoảng `timestamp`/`timestamp_end`.
- Chỉ áp dụng filter timestamp khi có `video_ID` chính xác (1 video) — vì so sánh thời gian giữa nhiều video khác nhau không có ý nghĩa.

### 5.2. Event Browser (`/api/events`)
- Tương tự Data Browser nhưng lọc theo `event_id` thay vì timestamp.
- **Khác biệt quan trọng**: `event_id` là **local per video** (reset về 0 ở mỗi video) — filter theo range chỉ hợp lệ khi chọn đúng 1 video, bị bỏ qua nếu chọn theo prefix nhiều video.
- Sentinel `event_id_end = -1` nghĩa là "đến event cuối cùng của video" — resolve server-side dựa trên `max_event_id` tính từ **toàn bộ pool của video đó**, độc lập với pagination/filter khác (để UI hiển thị đúng giá trị "cuối" thật, không bị lệch do đang xem trang nào).
- Filter theo **giá trị** `event_id` chứ không theo vị trí trong list — vì `ALL_EVENTS` có thể bị "thủng" (gap) do loại bỏ các event không resolve được hết frame qua `frame_by_path`.

## 6. Frontend Integration Pattern

`client.js` dùng pattern **"thử API thật trước, fallback mock nếu thất bại"**:
- Route đã implement → trả 200 → dùng data thật.
- Route chưa implement → backend trả 501 → catch → dùng mock.
- Backend không chạy (network error, `TypeError`) → catch → dùng mock.
- Lỗi khác (4xx/5xx thật sự) → **không** fallback, ném lỗi để hiển thị cho user.

→ Lợi ích: frontend và backend có thể phát triển song song, không cần feature flag hay rebuild khi 1 route được implement xong — chỉ cần backend ngừng trả 501 là client tự động chuyển sang dùng data thật.

## 7. Trade-offs & Decisions Log

| Quyết định | Lý do | Trade-off |
|---|---|---|
| HNSW cho Type 1/2, FlatIP cho Type 3 | Type 1/2 cần tốc độ cho tương tác realtime; Type 3 dataset event nhỏ hơn nên chấp nhận exact search | HNSW là approximate, có thể miss vài kết quả biên |
| RRF thay vì weighted score để merge dense+BM25 | Không cần tune trọng số giữa 2 thang điểm khác nhau (cosine similarity vs BM25 score) | RRF chỉ dùng rank, bỏ qua độ lớn chênh lệch score thực tế |
| `_best_ordered_chain` dùng DP O(m²) thay vì brute-force | Đủ nhanh vì m (candidate/video) nhỏ trong thực tế; đơn giản hơn so với thuật toán tối ưu hơn | Không scale tốt nếu k quá lớn (nhiều candidate/video) |
| Similar Frame dùng cosine trực tiếp thay vì FAISS | Tận dụng embedding đã preload, tránh thêm 1 index riêng | Chạy trên toàn bộ `encoded_frames` mỗi lần gọi — không scale nếu dataset lớn hơn nhiều |
| Frontend fallback mock theo status 501 | Cho phép dev song song FE/BE không cần feature flag | Dễ nhầm lẫn nếu backend vô tình trả 501 cho lỗi thật — cần đảm bảo 501 chỉ dùng cho "chưa implement" |
| Keyword suggestion dùng rule-based (vocab + POS tag) thay vì LLM ngay từ đầu | Nhanh, không tốn chi phí API, đủ dùng cho MVP; đã thiết kế sẵn điểm cắm LLM sau (`generate_fn`) | Không suy luận được từ đồng nghĩa/liên quan ngoài vocab; chất lượng phụ thuộc độ phủ của vocab |
| `supportsKeywords` khai báo tường minh per-type trong `queryTypes.js`, chỉ bật cho Type 3 ở MVP này | Type 3 (text-text trên transcript) dễ thiết kế keyword matching hơn Type 1/2 (text-image) — khái niệm "khớp keyword" rõ ràng hơn nhiều khi so trên văn bản so với so trong không gian embedding hình ảnh | Backend Type 1 đã có sẵn logic xử lý `keywords` (nối vào query) chờ dùng, nhưng chưa được kiểm chứng chất lượng vì UI chưa expose |
| Cache keyword bằng SQLite, key = MD5(normalized query) | Đơn giản, không cần thêm service; tránh tính lại rule-based cho query lặp lại | Không cache được các query "gần giống nhau" (khác 1 từ là miss); mở kết nối SQLite mỗi request |
| Load model/index 1 lần khi import `model_state.py`, không load lại mỗi request | Tránh overhead nặng (load model, đọc index) lặp lại; đơn giản hơn attach vào `app.state` (router không cần `Request`) | Khởi động app chậm hơn (phải load hết mọi thứ trước khi nhận request đầu tiên); không hot-reload được model/index khi đang chạy |
| Chuẩn hoá lại `event_id` thành local/gap-free ngay tại `model_state.py` (thay vì xử lý ở từng nơi dùng) | Đảm bảo giả định "event_id reset per video" đúng tại nguồn, các consumer phía sau (router, frontend) không cần tự xử lý gap/offset | Mất liên kết trực tiếp với `event_id` gốc trong data thô (phải tra `source_event_id` nếu cần debug ngược) |
| Data-completeness check (HNSW phủ FLATIP) chỉ log warning, không raise | Không chặn khởi động app vì lỗi dữ liệu không nghiêm trọng (thiếu vài frame) | Nguy cơ bug ngầm nếu thiếu quá nhiều frame mà không ai để ý log warning |
| `load_bm25_flatip_dangvantuan` build FlatIP index từ vector mỗi lần khởi động (không lưu file `.index`) | Build nhanh (vài giây) ngay cả với dataset lớn, đỡ phải maintain thêm 1 file binary dễ lệch với embeddings gốc | Tốn thời gian khởi động app mỗi lần restart (dù nhỏ), phải giữ `embeddings.pt` làm nguồn duy nhất |

## 8. Open Questions / Risks

- `/api/search/{type}/refine` (relevance feedback) đã được frontend gọi nhưng cần xác nhận trạng thái implement ở backend.
- `_best_ordered_chain` với O(m²) — cần benchmark nếu `k` (top-k mỗi query) tăng lớn, đặc biệt khi 1 video có nhiều candidate trùng lặp.
- Keyword cache mở `sqlite3.connect()` mỗi request, không dùng connection pool — cần đánh giá lại nếu traffic tăng hoặc chuyển sang gọi LLM (latency generate sẽ cao hơn nhiều so với rule-based, cache hit-rate sẽ quan trọng hơn).
- Assumption "HNSW_JINACLIPV2 phủ toàn bộ frame mà FLATIP_DANGVANTUAN tham chiếu" chỉ được log warning nếu vi phạm, không có cơ chế tự động vá — cần theo dõi log khởi động thường xuyên, đặc biệt sau khi cập nhật dataset.
- `_DANGVANTUAN_DEVICE != DEVICE` hiện chỉ log warning và ép dùng `DEVICE` chung — nếu điều này thực sự xảy ra (2 model lệch device), cần xác minh dangvantuan có bị silent chạy sai device (ảnh hưởng tốc độ) hay không.
- Renumbering `event_id` phụ thuộc giả định "raw event_id tăng dần chronological trong data gốc" — nếu nguồn dữ liệu tương lai không đảm bảo điều này, thứ tự event sau khi renumber có thể sai mà không có gì cảnh báo.
- `__TODO: các risk khác nếu phát hiện thêm trong quá trình test__`