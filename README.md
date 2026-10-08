# Vinhomes AI Video Studio

Ứng dụng web cục bộ bằng Python/Streamlit, giao diện tiếng Việt, dựng video từ **tư liệu người dùng cung cấp**. MVP Giai đoạn 1 không cần API, không gọi dịch vụ trả phí và chạy trên CPU.

## Tính năng MVP

- Quản lý nhiều dự án, lưu kịch bản, cảnh, tư liệu, cấu hình, tiến độ và lịch sử xuất bằng JSON; tiếp tục sau khi đóng ứng dụng.
- Nhập MP4, MOV, JPG, PNG; tạo thumbnail, đọc kích thước, thời lượng và âm thanh; bỏ qua file trùng nội dung trong cùng dự án.
- Nhập kịch bản hoặc TXT UTF-8; chia theo câu/cụm từ và phân bổ thời lượng; thêm, sửa, xóa, đổi thứ tự cảnh thủ công.
- Gợi ý clip đơn giản theo tên, mô tả, địa điểm và thẻ người dùng nhập. **Không nhận diện địa điểm trong hình ảnh.** Mỗi cảnh cần được người dùng xác nhận trước khi xuất.
- Cắt từ giây được chọn, ghép cảnh, giữ đúng tỷ lệ bằng viền đen, không crop. Cảnh dài hơn clip sẽ giữ khung hình cuối và bù im lặng. Ảnh được giữ trong thời lượng cảnh.
- Giữ/tắt tiếng gốc hoặc dùng giọng đọc ghi sẵn thay thế, trộn nhạc có quyền sử dụng. Nhạc được lặp; giọng đọc ngắn được bù im lặng, dài bị cắt.
- Tiêu đề, CTA, chữ trắng viền tối; nhập SRT UTF-8 hoặc hiển thị chữ kịch bản theo cảnh. **Chữ theo cảnh không phải phụ đề tự đồng bộ lời nói.** SRT được ưu tiên và được ghi trực tiếp vào hình video.
- Fade nhẹ qua nền đen; MP4 H.264/AAC: 9:16 (1080×1920) hoặc 16:9 (1920×1080), xem thử 360×640 hoặc 640×360.
- Xem/tải nhiều phiên bản xuất, tên có tên dự án, ngày/giờ và mã riêng; không ghi đè bản cũ. Cache từng cảnh: sửa một cảnh không cần dựng lại cảnh khác; bước ghép/chữ/âm thanh cuối vẫn chạy lại.

**Chưa triển khai:** faster-whisper/nhận dạng giọng nói, AI phân tích kịch bản, giọng đọc AI, OpenCV/phân tích khung hình, metadata cho 5 nền tảng, GPU, timeline kéo thả, tiến độ theo từng frame và hàng đợi dựng nền. `services/ai_adapter.py` là điểm mở rộng cho Giai đoạn 2, không phải API đang hoạt động. Không tự sinh hình ảnh dự án hoặc bổ sung giá bán, pháp lý, tiến độ, chính sách.

## Cài trên Windows 10/11

### 1. Lấy ứng dụng

Trên GitHub, chọn **Code → Download ZIP**, giải nén vào thư mục riêng, ví dụ `C:\VinhomesStudio`. Thư mục phải chứa `app.py` và `requirements.txt`. Nếu đã có bản Git, dùng thư mục đó. Không cần Git để chạy từ ZIP.

### 2. Cài Python

Tải Python **3.11 trở lên** từ https://www.python.org/downloads/windows/. Khuyến nghị 3.11 hoặc 3.12 bản 64-bit. Khi cài, chọn **Add python.exe to PATH**. Mở **Command Prompt** (gõ `cmd` trong Start):

```bat
py --version
```

Nếu không nhận lệnh, mở lại Command Prompt; nếu vẫn lỗi, chạy lại bộ cài và bật Python Launcher/PATH.

### 3. Cài FFmpeg và ffprobe

Nếu Windows có `winget`, chạy trong Command Prompt:

```bat
winget install --id Gyan.FFmpeg --exact --source winget
```

Làm theo bộ cài rồi **đóng và mở lại Command Prompt**. Không tắt kiểm tra chữ ký hoặc checksum.

Nếu không có winget: vào https://ffmpeg.org/download.html → **Windows builds**, chọn bản đầy đủ từ nhà cung cấp được trang chính thức liên kết. Giải nén vào `C:\ffmpeg`. Tìm thư mục `bin` chứa cả `ffmpeg.exe` và `ffprobe.exe`. Trong Start, tìm **Edit environment variables for your account**, sửa **Path → New**, thêm đường dẫn thư mục bin thực tế, bấm OK rồi mở lại Command Prompt.

Kiểm tra:

```bat
ffmpeg -version
ffprobe -version
```

Cần FFmpeg có `libx264`, AAC và bộ lọc `subtitles` (libass). Nút Cài đặt trong ứng dụng kiểm tra các thành phần này. Windows thường đã có Arial hỗ trợ tiếng Việt.

### 4. Cài thư viện

Mở thư mục ứng dụng trong File Explorer, gõ `cmd` vào thanh địa chỉ và nhấn Enter. Cửa sổ lệnh sẽ mở đúng thư mục. Chạy lần lượt:

```bat
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Bước tải thư viện cần Internet. Không cần kích hoạt môi trường ảo hay đổi chính sách PowerShell.

### 5. Mở ứng dụng

Trong cùng cửa sổ Command Prompt:

```bat
.venv\Scripts\python.exe -m streamlit run app.py
```

Hoặc nhấp đúp `run_windows.bat` sau khi cài đặt. Trên **máy Windows của bạn**, trình duyệt mở tại `http://localhost:8501`; nếu không tự mở, nhập địa chỉ đó. Giữ cửa sổ Command Prompt mở. Dừng bằng **Ctrl+C**. Lần sau chỉ cần bước 5; dữ liệu đã lưu vẫn còn.

Ứng dụng mặc định chỉ lắng nghe trên máy cục bộ. Không mở ra Internet: MVP chưa có đăng nhập/phân quyền. Địa chỉ localhost trên dành cho máy Windows của bạn, không phải liên kết xem ứng dụng trong cloud Codex.

## Dựng video đầu tiên

1. **Tổng quan:** nhập tên, tạo dự án; chọn dự án đang mở ở danh sách bên trái.
2. **Thư viện tư liệu:** chọn video/ảnh rồi **Nhập tư liệu**. Mở từng tư liệu để lưu tên, mô tả, địa điểm và thẻ. Tối đa 200 MB/file; chia clip lớn trước khi nhập.
3. **Kịch bản:** nhập hoặc đọc TXT UTF-8 vào bản nháp rồi **Lưu kịch bản**. Tự kiểm chứng các thông tin thương mại/pháp lý.
4. **Biên tập cảnh:** chọn thời lượng và chia theo quy tắc hoặc thêm thủ công. Chọn clip, điểm cắt, thời lượng, xác nhận phù hợp rồi **Lưu cảnh**. Muốn chia lại cần xác nhận thay cảnh cũ. Thay kịch bản không tự thay các cảnh đã lưu.
5. **Âm thanh & Phụ đề:** chọn tiếng gốc/giọng đọc; tải nhạc và xác nhận quyền sử dụng. Nhập SRT nếu có. **Lưu âm thanh và phụ đề**. Không có SRT thì có thể bật chữ kịch bản theo cảnh.
6. **Cài đặt:** sửa tiêu đề, CTA, tỷ lệ và fade rồi lưu. CTA mặc định: “Theo dõi hành trình khám phá Vinhomes Hải Vân Bay Đà Nẵng”. Nội dung ưu tiên: Đảo Ngọc → Vịnh Mây → Bạch Vân.
7. **Xem trước & Xuất:** chọn xem thử và **Dựng và xuất video**. Kiểm tra hình, tiếng, chữ và thông tin. Chọn Full HD để xuất chính thức rồi **Tải MP4 về máy**.

Gợi ý: video ngắn 30–90 giây, video dài 180–600 giây. Giới hạn MVP: 600 giây/cảnh, 60 phút/dự án. Full HD trên CPU có thể chậm; thử 360p trước. Tiến độ theo bước/cảnh, không đo từng frame. Khi dựng không sửa cùng dự án trong tab khác; MVP dành cho một người dùng trên máy.

## Thử khi chưa có video thật

```bat
.venv\Scripts\python.exe -m workflow.demo --export
```

Lệnh tạo dự án thử với video có tiếng, video không tiếng, ảnh và xuất MP4 6 giây. Tư liệu ghi rõ **mẫu tổng hợp, không phải hình ảnh thực tế Vinhomes**. Mở hoặc làm mới ứng dụng để chọn mẫu. Mỗi lần chạy tạo dự án riêng.

## SRT tiếng Việt

Lưu file UTF-8, đuôi `.srt`, ví dụ:

```srt
1
00:00:00,000 --> 00:00:02,000
Khám phá Đảo Ngọc.

2
00:00:02,000 --> 00:00:04,000
Ghé thăm Vịnh Mây.
```

Mốc tính từ đầu video xuất, tăng dần, không chồng lấn, không vượt thời lượng. MVP không căn lại SRT khi đổi thứ tự/thời lượng cảnh; sửa SRT và xem thử lại.

## Cấu trúc và sao lưu

```text
app.py                  Khởi động Streamlit
config/defaults.json    Mặc định dự án mới
workflow/               Chia cảnh, điều phối xuất, tạo mẫu
services/               Lưu dự án, media, FFmpeg, audio, subtitle, adapter AI
ui/                     Bảy mục giao diện tiếng Việt
tests/                  Kiểm thử nghiệp vụ, FFmpeg và Streamlit
inputs/scripts/         File kịch bản của bạn (tùy chọn)
inputs/media/<id>/      Bản sao tư liệu và thumbnail
projects/<id>/          project.json và cache cảnh
outputs/<id>/           Các phiên bản MP4
```

Đóng ứng dụng rồi chép cả `projects`, `inputs`, `outputs` để sao lưu/di chuyển. Giữ vị trí tương đối các thư mục. Nút JSON chỉ sao lưu cấu hình, không gồm media. `.gitignore` loại trừ dữ liệu này; **không force-add video, dữ liệu cá nhân hoặc khóa API vào Git**. Không dùng dữ liệu thật trong test. Có thể xóa cache khi ứng dụng dừng; lần xuất sau dựng lại cảnh. Không xóa tư liệu đang được tham chiếu.

## Xử lý lỗi

| Lỗi | Cách xử lý |
|---|---|
| Không tìm thấy ffmpeg/ffprobe | Kiểm tra `-version`, thêm đúng bin vào PATH, mở lại cửa sổ lệnh và ứng dụng. |
| Thiếu libx264/AAC/subtitles | Cài FFmpeg đầy đủ từ nguồn được trang chính thức liên kết. |
| Không tìm thấy font | Kiểm tra Arial; đặt VIDEO_STUDIO_FONT đến font TTF hỗ trợ tiếng Việt nếu cần. |
| Chưa chọn/xác nhận tư liệu | Chọn clip, xác nhận và Lưu cảnh cho từng cảnh. |
| Điểm bắt đầu ngoài video | Điểm bắt đầu phải nhỏ hơn thời lượng nguồn. |
| SRT lỗi/vượt thời lượng | Sửa mốc, dùng UTF-8; thử bỏ SRT để kiểm tra video. |
| Thiếu quyền sử dụng nhạc | Xác nhận nhạc được cấp phép rồi lưu, hoặc bỏ nhạc. |
| Không đọc/lưu file | Kiểm tra quyền ghi, dung lượng và bản sao lưu. |
| Quá thời gian xử lý | Giảm thời lượng, dùng xem thử; cache cảnh đã xong vẫn được giữ. |
| API chưa triển khai | Dùng quy tắc/thủ công; MVP không cần API. |
| Không xem được MOV nguồn | Thử xuất MP4; dùng trình phát trên Windows nếu trình duyệt không hỗ trợ codec nguồn. |

Có thể đặt đường dẫn đầy đủ trong Command Prompt trước khi chạy:

```bat
set "FFMPEG_BINARY=C:\ffmpeg\bin\ffmpeg.exe"
set "FFPROBE_BINARY=C:\ffmpeg\bin\ffprobe.exe"
set "VIDEO_STUDIO_FONT=C:\Windows\Fonts\arial.ttf"
```

`.env.example` hướng dẫn tên biến; MVP không tự đọc `.env` và không lưu khóa API.

## Kiểm thử

Windows:

```bat
.venv\Scripts\python.exe -m pytest -q
```

Linux/cloud cần Python 3.11+, FFmpeg/ffprobe đầy đủ và Noto Sans/DejaVu Sans:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m streamlit run app.py --server.headless true
```

Test sinh tư liệu nhỏ ở thư mục tạm, thực sự xuất và giải mã MP4 ở hai tỷ lệ/hai chất lượng, kiểm tra tiếng, chữ, cache, bảo toàn nguồn và thao tác giao diện. Kết quả thực tế ở `VALIDATION.md`. Cần xác nhận thêm trên Windows thật; cloud/Linux không chứng minh mọi codec hay bộ cài Windows hoạt động.

Không tự triển khai dịch vụ trả phí. Giai đoạn 2/3 sẽ bổ sung adapter riêng và chỉ sử dụng API có phí sau khi được đồng ý.
