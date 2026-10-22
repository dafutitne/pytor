# Pytor NVIDIA miner

PRL (`pearlhash`) và QTC (`quantus`), Linux/Windows x64. Binary/process `pytor` / `pytor.exe`; agent `pytor/0.2.6`.

[Linux Ubuntu 22.04+: 0.2.6 jammy3](https://github.com/dafutitne/pytor/releases/tag/v0.2.6-jammy3) · [Windows: 0.2.6 brand1](https://github.com/dafutitne/pytor/releases/tag/v0.2.6-brand1)

Linux `brand1` yêu cầu GLIBC 2.38 và không chạy trên Ubuntu 22.04. Hãy dùng `jammy2`, kế thừa runtime Ubuntu 22.04 / GLIBC 2.35 của jammy1 và sửa tương thích PTX cho PRL; không cần nâng GLIBC hệ thống.

## Ubuntu / Linux — tải trực tiếp, không dùng script cài đặt

```console
curl -fL https://github.com/dafutitne/pytor/releases/download/v0.2.6-jammy3/pytor-linux-x86_64 -o pytor
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

Tải `pytor-windows-x86_64.zip` trong release **brand1**, giải nén rồi chạy trong PowerShell:

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

Linux jammy2 kế thừa runtime và native worker của jammy1, vốn được build và kiểm trên Ubuntu 22.04 / GLIBC 2.35. Jammy2 thay năm module PRL PTX bằng bản CUDA 12.8.93; 52 module GPU khác giữ nguyên. Binary jammy2 đã chạy kiểm version, integrity, CPU và GPU/pool trên RTX 3090; kết quả cụ thể ở phần dưới. Không sửa lỗi khởi tạo CUDA 999.

Windows brand1 dựa trên test14/windows-test5. Windows đã kiểm runtime, tên process, integrity, CPU selfcheck, PRL startup bằng GPU giả lập và frontend QTC bằng fixture; GPU Windows chưa kiểm thực tế.

Repository phân phối binary, tài liệu và bộ build jammy1 cho Ubuntu 22.04 (script/workflow/source host QTC). Source code ZIP/tar GitHub tự sinh chưa phải bộ source miner hoàn chỉnh. Xem build-info.json của đúng release để biết phạm vi kiểm chứng.

## Linux jammy2: tương thích PRL driver 570

Năm module PRL đã được biên dịch lại bằng CUDA 12.8.93 / PTX 8.7 để sửa lỗi 222; runtime jammy1 và 52 module GPU còn lại giữ nguyên. Kiểm trên RTX 3090 / driver 570.211.01: 56 proof SM86 và 4 proof portable đạt; một lượt kiểm tương thích pool có 1 accepted / 0 rejected qua relay/tunnel.

Đo riêng 120,193 giây sau khi dừng miner khác: trung bình 118,56 TH/s, cửa sổ sau khởi động 119,2–120,5 TH/s tại 300 W; lượt đo này có 0 accepted / 0 rejected. Chưa đối chiếu A/B bn, chưa kiểm ổn định dài hạn. QTC trên driver 570 chưa kiểm lại. Không gồm patch RTX8000 thử nghiệm; Windows vẫn là brand1.

Dừng miner khác trên cùng GPU trước khi đo. Thông tin và checksum có trong release jammy2.


## Banner terminal jammy3

Khi chạy PRL hoặc QTC, terminal in `Starting matrix` trước khi khởi tạo backend. Chỉ đổi thông báo và phiên bản entry point; 57 module GPU, native worker và toàn bộ runtime còn lại giữ nguyên so với jammy2. Hai nhánh khởi động đã kiểm với backend giả lập; không chạy lại GPU/pool cho thay đổi nhãn này. Windows vẫn dùng brand1.
