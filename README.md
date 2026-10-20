# Pytor NVIDIA miner

PRL (`pearlhash`) và QTC (`quantus`), Linux/Windows x64. Binary/process `pytor` / `pytor.exe`; agent `pytor/0.2.6`.

[Tải bản 0.2.6 brand1](https://github.com/dafutitne/pytor/releases/tag/v0.2.6-brand1)

## Ubuntu / Linux — tải trực tiếp, không dùng script cài đặt

```console
curl -fL https://github.com/dafutitne/pytor/releases/download/v0.2.6-brand1/pytor-linux-x86_64 -o pytor
chmod +x pytor
./pytor --version
./pytor --verify-bundle
```

PRL:

```console
./pytor --algorithm pearlhash --pool HOST:PORT --wallet ADDRESS.WORKER
```

QTC:

```console
./pytor --algorithm quantus --pool HOST:PORT --wallet ADDRESS.WORKER
```

Thay `HOST:PORT` và `ADDRESS.WORKER` bằng cấu hình của bạn. Với relay/tunnel, dùng cổng TCP localhost của tunnel đã cấu hình; không đưa URL WSS trực tiếp vào `--pool`.

## Windows

Tải `pytor-windows-x86_64.zip` trong Releases, giải nén rồi chạy trong PowerShell:

```powershell
.\pytor.exe --algorithm pearlhash --pool HOST:PORT --wallet ADDRESS.WORKER
.\pytor.exe --algorithm quantus --pool HOST:PORT --wallet ADDRESS.WORKER
```

Nếu tải riêng `pytor-windows-x86_64.exe`, đổi tên file thành `pytor.exe` để tên process là pytor. PID là số do hệ điều hành cấp, không phải tên miner.

Mỗi nền tảng chỉ cần một binary; kernel đã tích hợp, không cần folder kernel bên ngoài. Cần driver NVIDIA và hệ điều hành tương thích; không cần cài Python hoặc CUDA Toolkit.

## Log và chỉ số

- PRL: `pytor-logs/pytor-prl.jsonl`.
- QTC: `pytor-logs/pytor-qtc.jsonl`.
- Đường dẫn tính từ thư mục chạy lệnh; tùy chọn `--log FILE` để đổi.
- PRL proof được lưu cùng thư mục log, theo tiền tố tên file log.
- `matrixcount` → `mathex`; `matrixcount_window` → `mathex_window`; `matrixcount_unit` → `mathex_unit`. Dashboard cần cập nhật tên trường.
- Đơn vị giữ nguyên: PRL **TH/s**, QTC **H/s**.

## Kiểm SHA256

Tải `SHA256SUMS` từ cùng release. Linux dùng `sha256sum pytor` và so với dòng `pytor-linux-x86_64` (đổi tên file không đổi hash). Windows dùng `Get-FileHash .\pytor.exe -Algorithm SHA256` và so với dòng `pytor-windows-x86_64.exe`.

## Phạm vi bản phát hành

Đây là bản đổi branding/log từ Kaetech. Linux dựa trên test16; Windows dựa trên test14/windows-test5. 57 module GPU trong mỗi gói giữ nguyên byte. Không có tối ưu GPU mới trong lượt đổi tên này.

Windows đã kiểm chạy binary, tên process, integrity, CPU selfcheck và PRL startup bằng GPU giả lập + TCP localhost. Frontend/default log QTC đã kiểm bằng fixture. Linux đã kiểm cấu trúc ELF/archive và frontend, chưa chạy lại binary đổi tên trên Linux. Chưa đo lại GPU/pool cho bản branding; Windows GPU vẫn chưa được kiểm thực tế. Không sửa lỗi khởi tạo CUDA 999.

`build-info.json` và `branding-validation.json` ghi phạm vi kiểm tra. Repository này phân phối binary và tài liệu; Source code ZIP/tar tự sinh của GitHub chỉ chứa nội dung repository, không phải bộ source miner hoàn chỉnh.
