# Build Guide: OCR & Hybrid Document Detection (Tahap Lanjutan)

**Menangani Dokumen Campuran — Teks Native + Gambar/Scan dalam Satu Dokumen**

---

## 1. Tujuan

Melanjutkan prototipe dasar (regex + NER untuk teks native) dengan menambahkan kemampuan mendeteksi dan memproses **dokumen campuran** — misalnya PDF kontrak kerja yang sebagian halamannya teks asli, tapi ada lampiran foto KTP atau halaman hasil scan.

**Target keluaran tahap ini:**
- Sistem otomatis mendeteksi tiap halaman/elemen dokumen: apakah teks native atau gambar
- Halaman/elemen gambar diproses lewat OCR sebelum masuk ke PII detector yang sudah ada
- Output tetap konsisten: satu dokumen hasil redaksi utuh, baik yang asalnya teks maupun gambar

---

## 2. Kapan Kasus Ini Muncul (Real Case di Dokumen HR)

| Contoh Dokumen | Kondisi |
|---|---|
| Kontrak kerja PDF | Halaman 1-3 teks asli (hasil export Word), halaman 4 lampiran scan KTP |
| Dokumen medical check-up | Teks hasil ketik dokter + foto hasil lab yang di-scan |
| Slip gaji lama | Sudah full-scan (semua halaman gambar, tidak ada teks sama sekali) |
| Email/chat HR | Teks asli, tapi ada screenshot terlampir (misal screenshot WhatsApp berisi nama & no HP) |

Jenis dokumen paling terakhir (full-scan) sebenarnya lebih sederhana ditangani — seluruh halaman tinggal masuk OCR. Yang lebih rumit justru dokumen **campuran** di baris 1, 2, dan 4, karena butuh logic pemilahan per halaman/elemen.

---

## 3. Arsitektur Pipeline (Update dari Prototipe Sebelumnya)

```
[Dokumen Masuk: PDF/DOCX]
        │
        ▼
[Page/Element Splitter]
   - Buka dokumen per halaman (PyMuPDF/fitz untuk PDF)
   - Untuk tiap halaman, cek: apakah ada teks yang bisa di-extract langsung?
        │
        ├── ADA teks native ──────────┐
        │                              ▼
        │                    [PII Detector - existing]
        │                    (regex + NER dari prototipe Tahap 1)
        │                              │
        └── TIDAK ADA teks            │
            (halaman = gambar penuh   │
            atau ada embedded image)  │
                    │                  │
                    ▼                  │
            [OCR Engine]               │
            (Tesseract/AWS Textract)   │
                    │                  │
                    ▼                  │
            [PII Detector - existing] ◄┘
            (hasil OCR diproses sama seperti teks native)
                    │
                    ▼
        [Redactor - existing]
        (redaksi diterapkan ke teks; untuk gambar, redaksi berupa
         blok/box hitam di koordinat lokasi PII terdeteksi)
                    │
                    ▼
        [Output: Dokumen hasil redaksi utuh]
```

**Poin penting:** untuk halaman gambar, redaksi tidak cukup "ganti teks" — karena PII-nya ada di dalam gambar itu sendiri (misal foto KTP). Redaksi harus berupa **menggambar kotak hitam di atas koordinat pixel** tempat PII terdeteksi (OCR engine biasanya juga mengembalikan koordinat/bounding box dari tiap teks yang terbaca, bukan cuma teksnya).

---

## 4. Prompt untuk Antigravity (Lanjutan dari Prototipe Sebelumnya)

```
Lanjutkan project pii-redaction-prototype yang sudah ada (lihat PROGRESS.md untuk konteks).

Tambahkan modul baru untuk menangani dokumen PDF campuran (teks native + gambar/scan):

1. Buat file page_classifier.py:
   - Gunakan PyMuPDF (fitz) untuk membuka PDF per halaman
   - Untuk tiap halaman, cek apakah ada teks yang bisa di-extract (page.get_text())
   - Jika teks kosong atau sangat sedikit dibanding ukuran halaman, tandai halaman sebagai "image-based"

2. Buat file ocr_engine.py:
   - Gunakan pytesseract (Tesseract OCR) untuk ekstrak teks dari halaman image-based
   - Pastikan hasil OCR menyertakan bounding box tiap kata (gunakan pytesseract.image_to_data)
   - Return: teks hasil OCR + koordinat tiap kata

3. Update detector.py:
   - Terima input dari dua sumber: teks native ATAU hasil OCR (format sama)
   - Untuk hasil OCR, saat PII terdeteksi, simpan juga koordinat bounding box-nya

4. Update redactor.py:
   - Untuk teks native: redaksi seperti biasa (replace/mask teks)
   - Untuk halaman image-based: gambar kotak hitam solid di atas koordinat bounding box
     PII yang terdeteksi, menggunakan PIL/Pillow atau PyMuPDF drawing functions

5. Update app.py (Streamlit):
   - Tambahkan opsi upload PDF (selain CSV yang sudah ada)
   - Tampilkan preview halaman PDF before/after redaksi (bisa pakai st.image untuk render halaman sebagai gambar)
   - Tampilkan indikator per halaman: "Halaman 1: Teks Native" atau "Halaman 4: Diproses via OCR"

6. Tambahkan dummy test PDF (buat script generate_dummy_pdf.py) yang menghasilkan:
   - 1 PDF dengan halaman teks native berisi data dummy karyawan
   - 1 halaman tambahan berupa gambar hasil scan (bisa simulasikan dengan render teks ke gambar dulu)
```

---

## 5. Dependencies Tambahan

```txt
pymupdf          # PyMuPDF, untuk baca & manipulasi PDF per halaman
pytesseract       # OCR wrapper untuk Tesseract
pillow            # manipulasi gambar (untuk gambar kotak redaksi)
pdf2image         # convert halaman PDF ke gambar untuk preview di Streamlit
```

Perlu install Tesseract binary di sistem (bukan cuma library Python):
```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr

# Untuk bahasa Indonesia
sudo apt install tesseract-ocr-ind
```

> Kalau nanti sudah masuk tahap enterprise dan butuh akurasi OCR lebih tinggi (terutama untuk KTP yang seringkali kualitas scan-nya jelek), pertimbangkan ganti ke **AWS Textract** atau **Google Document AI** yang jauh lebih robust dibanding Tesseract untuk kondisi real-world.

---

## 6. Tantangan yang Perlu Diantisipasi

| Tantangan | Penjelasan | Mitigasi Awal |
|---|---|---|
| Kualitas scan rendah | Foto KTP miring, buram, atau pencahayaan jelek → OCR gagal baca | Tesseract punya preprocessing dasar (grayscale, threshold) — bisa ditambahkan di ocr_engine.py |
| Halaman "semi-image" | Ada halaman dengan teks native TAPI juga ada gambar kecil di dalamnya (misal logo perusahaan + tanda tangan scan) | Perlu deteksi embedded image terpisah dari teks, bukan cuma di level halaman — bisa pakai `page.get_images()` di PyMuPDF |
| Orientasi gambar terbalik/miring | Hasil scan kadang ke-rotate | Tambahkan deteksi orientasi otomatis sebelum OCR (Tesseract punya OSD - Orientation and Script Detection) |
| Bahasa campuran (Indonesia-Inggris) | Nama, alamat pakai bahasa Indonesia, tapi ada istilah bahasa Inggris di kontrak | Gunakan `tesseract-ocr-ind` + `tesseract-ocr-eng` sekaligus saat OCR |

---

## 7. Checklist Validasi Tahap OCR

- [ ] Sistem berhasil membedakan halaman teks native vs halaman gambar secara otomatis
- [ ] OCR berhasil membaca teks dari halaman gambar dummy dengan akurasi cukup (uji manual, bandingkan hasil OCR vs teks asli)
- [ ] PII yang terdeteksi dari hasil OCR berhasil di-redact dengan kotak hitam di posisi yang benar (tidak geser/salah lokasi)
- [ ] Dokumen PDF output tetap bisa dibuka normal dan halaman non-PII (misal halaman tanpa data karyawan) tidak ikut ke-redact
- [ ] UI Streamlit menampilkan preview before/after untuk kedua jenis halaman (native & OCR) dengan jelas

---

## 8. Langkah Setelah Tahap Ini Berhasil

1. Uji dengan dokumen dummy yang benar-benar mirip kondisi riil (scan miring, kualitas rendah) untuk stress-test OCR.
2. Diskusikan dengan tim HR/Legal: apakah level akurasi OCR saat ini sudah cukup untuk dokumen sensitif seperti KTP, atau perlu upgrade ke Textract/Document AI sebelum lanjut ke MVP.
3. Lanjut ke **Tahap 3 (MVP dengan Human-in-the-Loop)** sesuai solution brief utama — gabungkan hasil kerja prototipe teks (Tahap 1) dan OCR (tahap ini) jadi satu pipeline utuh, tambahkan dashboard review yang bisa menampilkan flag "confidence rendah" khusus untuk hasil dari OCR (karena OCR secara natural lebih rawan salah dibanding teks native).

---

*Dokumen ini adalah lanjutan dari `Prototype_Build_Guide_Antigravity.md`, fokus khusus menangani dokumen campuran teks + gambar. Update juga `PROGRESS.md` di project kamu setelah tahap ini selesai, supaya sesi/akun Antigravity berikutnya tahu progres sampai di mana.*
