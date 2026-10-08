# Kết quả kiểm thử Giai đoạn 1

Ngày: 08/10/2026. Môi trường thực thi: Linux cloud, Python 3.12.14, FFmpeg/ffprobe 7.1.5, Streamlit 1.50.0, Pillow 11.3.0, pytest 8.4.2. Xử lý bằng CPU, tối đa 2 threads cho các bộ mã hóa/bộ lọc được cấu hình.

## Kết quả thực tế

Lệnh trong `/workspace/vinhomes-video-automation`:

```sh
/workspace/venvs/vinhomes-studio/bin/python -m pytest -q
```

**15 passed in 33.45s**. Không có test failed/skipped/xfail trong lần chạy này.

- Nhập, chia kịch bản tiếng Việt; chỉnh thời lượng/nội dung và lưu, mở lại dự án JSON.
- Tạo tư liệu bằng FFmpeg; nhập video có tiếng, MOV không tiếng và ảnh PNG, tạo thumbnail/metadata.
- Bắt lỗi thiếu tư liệu/xác nhận, điểm cắt ngoài video, file hỏng, FFmpeg thiếu, API chưa triển khai và đường dẫn ngoài ứng dụng.
- Xuất thực tế cả 9:16/16:9 và preview/Full HD: 360×640, 640×360, 1080×1920, 1920×1080; xác nhận H.264/AAC và thời lượng.
- Giải mã toàn bộ MP4 bằng FFmpeg với `-xerror`; đo năng lượng âm thanh từ PCM đã giải mã, kiểm tra cả tiếng nguồn và chế độ im lặng.
- Nhập SRT UTF-8, kiểm tra mốc, lưu nội dung tiếng Việt, xác nhận vùng chữ trắng xuất hiện trong hình; kiểm tra khung hình mẫu bằng mắt thấy dấu tiếng Việt.
- Video không có tiếng và cảnh dài hơn nguồn được bù đúng, ảnh xuất được. Thử trộn giọng đọc/nhạc; yêu cầu xác nhận quyền dùng nhạc.
- Kiểm tra hash tư liệu nguồn sau xuất không đổi. Xuất lại tái sử dụng 3/3 cảnh; sửa một cảnh tái sử dụng 2/3 cảnh và không thay file cache cũ.
- Streamlit AppTest: tạo/chuyển dự án, mở cả 7 mục, lưu kịch bản, chia cảnh, thay tư liệu/chỉnh thời lượng, yêu cầu xác nhận lại và xuất MP4 bằng nút giao diện. Không có exception hoặc lỗi giao diện trong luồng xuất mẫu.

## Chạy ứng dụng và mẫu riêng ngoài tests

Đã chạy `python -m workflow.demo --export`: dự án tổng hợp 3 cảnh, MP4 6 giây, 360×640, có H.264 và AAC. Đã giải mã toàn bộ file thành công và xem khung hình có tiêu đề/chữ tiếng Việt. Đây là tư liệu thử, không phải hình ảnh thực tế dự án.

Đã khởi động Streamlit bằng môi trường ảo `/workspace/venvs/vinhomes-studio`, `--server.headless true --server.address 127.0.0.1 --server.port 8501`. Yêu cầu nội bộ đến health endpoint và trang HTML đều trả HTTP 200. AppTest xác thực hành vi ứng dụng bổ sung cho health check.

`pip check`: **No broken requirements found**. `git diff --check` không báo lỗi. File media, dự án JSON, cache và MP4 tạo ra được Git bỏ qua; chỉ `.gitkeep` được dùng để giữ thư mục rỗng trong mã nguồn.

## Khả năng tái sử dụng môi trường

Đã thực thi script cài môi trường ảo, cài `requirements.txt` và kiểm tra FFmpeg/ffprobe/font; chạy lại thành công khi dependencies đã có. Đã lưu `install_script` và `start_skill` vào bản nháp cấu hình cloud. Không thêm secrets, biến API hoặc nới quyền mạng. Bản nháp lưu thành công chưa có nghĩa được Publish hay đã xác thực phục hồi trong task mới.

## Giới hạn xác nhận

- Chưa chạy trực tiếp trên Windows hoặc kiểm thử bộ cài Python/winget/launcher BAT trên Windows. README cung cấp hướng dẫn Windows và các biến công cụ/font.
- Chưa kiểm thử kéo thả/tải file bằng trình duyệt thật; nhập media được kiểm thử ở dịch vụ và luồng UI được kiểm thử bằng AppTest. Không có công cụ browser automation trong phiên này.
- Chưa thử tư liệu thực địa, codec camera đặc biệt, file lớn hoặc dựng liên tục 3–10 phút. Full HD đã được kiểm tra bằng dữ liệu nhỏ.
- Chưa tự nhận dạng giọng nói, tạo giọng đọc AI, gọi API AI hoặc tạo metadata 5 nền tảng. Không gọi API có phí hay triển khai dịch vụ trả phí.
- Phụ đề theo kịch bản là chữ theo cảnh, không phải đồng bộ tự động lời nói. SRT dùng thời gian người dùng cung cấp.
- Tiến độ là theo bước/cảnh; dựng vẫn chạy đồng bộ. Nếu tắt ứng dụng giữa chừng, cần xuất lại; cache hoàn tất giúp tiếp tục.
