# Prototype Build Guide: PII Redaction Generator (Tahap 1)

**Menggunakan Antigravity — Prototipe Deteksi & Redaksi PII Dokumen Karyawan**

---

## 1. Tujuan Prototipe

Membangun *proof of concept* sistem deteksi & redaksi PII sederhana untuk dokumen internal karyawan (contoh: slip gaji, data HRIS format Excel/CSV), lengkap dengan **UI sederhana berbasis Streamlit** agar bisa langsung di-demo ke tim HR tanpa perlu buka terminal/kode.

**Target keluaran prototipe:**
- Input: dokumen contoh (CSV/Excel data karyawan, atau PDF slip gaji sederhana) — di-upload lewat UI
- Proses: deteksi otomatis field PII (nama, NIK, no. HP, email, no. rekening)
- Output: dokumen versi ter-redact (bisa didownload dari UI) + laporan ringkas ditampilkan di layar

---

## 2. Scope Prototipe (Batasi Dulu!)

Supaya cepat selesai dan terukur, batasi scope di tahap ini:

| Termasuk (Tahap 1) | Belum termasuk (Tahap selanjutnya) |
|---|---|
| Deteksi PII rule-based (regex): NIK, no. HP, email, NPWP | OCR untuk dokumen scan/gambar |
| 1 jenis dokumen dulu: CSV/Excel data karyawan | Multi-format dokumen (PDF, DOCX) |
| Redaksi sederhana (masking/blok) | Tokenization konsisten lintas dokumen |
| UI dasar: upload file → lihat hasil → download (Streamlit) | Role-based login & multi-user access |
| Uji coba dengan data dummy (bukan data karyawan asli!) | Human-in-the-loop review UI dengan approval workflow |
| Laporan akurasi dasar (jumlah terdeteksi, ditampilkan di UI) | Audit trail & logging permanen ke database |

> ⚠️ **Penting:** gunakan **data dummy/sintetis**, bukan data karyawan asli, selama tahap prototipe — untuk menghindari risiko kebocoran data sebelum sistem tervalidasi.

---

## 3. Prompt Awal untuk Antigravity

Gunakan prompt semacam ini sebagai starting point di Antigravity untuk generate skeleton project:

```
Buatkan project Python sederhana untuk PII detection & redaction prototype dengan spesifikasi:

1. Input: file CSV berisi data dummy karyawan (kolom: nama, NIK, no_hp, email, alamat, gaji)
2. Gunakan regex untuk mendeteksi pola: NIK (16 digit), no HP Indonesia (08xx), email, NPWP
3. Gunakan library spaCy atau Microsoft Presidio untuk mendeteksi nama orang (Named Entity Recognition)
4. Redaksi hasil deteksi dengan masking (contoh: 081****5678, N*** untuk nama)
5. Output: file CSV baru hasil redaksi + laporan ringkas (jumlah PII terdeteksi per kolom)
6. Buat juga dummy dataset generator (100 baris data karyawan fiktif) untuk testing
7. Buatkan UI sederhana pakai Streamlit dengan fitur:
   - Upload file CSV lewat drag-and-drop
   - Tombol "Proses Redaksi"
   - Tampilkan preview tabel: data asli (before) vs data hasil redaksi (after) berdampingan
   - Tampilkan ringkasan hasil deteksi (jumlah PII per kategori) dalam bentuk metric/angka besar atau bar chart
   - Tombol download hasil CSV yang sudah diredaksi
8. Struktur project: app.py (entry point Streamlit), detector.py, redactor.py, generate_dummy_data.py, requirements.txt
```

Setelah project ter-generate, minta Antigravity lanjutkan dengan prompt tambahan:

```
Tambahkan unit test sederhana untuk memvalidasi:
- Regex NIK menangkap 16 digit angka dengan benar
- Regex no HP menangkap format 08xx dan +62
- Fungsi redaksi tidak mengubah kolom yang bukan PII (misal kolom gaji tetap utuh)
```

Kalau ingin UI-nya lebih informatif, bisa tambahkan prompt lanjutan:

```
Tambahkan di Streamlit UI:
- Warning banner jika file yang diupload terdeteksi berisi data sensitif dalam jumlah besar (>X baris)
- Expandable section untuk lihat detail per baris mana saja PII yang terdeteksi dan jenisnya
- Sidebar untuk toggle jenis redaksi: "Mask sebagian" vs "Redact total (blok penuh)"
```

---

## 4. Gambaran Tampilan UI (Wireframe Sederhana)

```
┌─────────────────────────────────────────────┐
│  PII Redaction Prototype - Internal HR Tool  │
├─────────────────────────────────────────────┤
│  📁 Upload file CSV data karyawan             │
│  [ Drag & drop file di sini / Browse files ]  │
│                                                │
│  ⚙️ Mode Redaksi:  ( ) Mask sebagian          │
│                    ( ) Redact total            │
│                                                │
│  [ 🔍 Proses Redaksi ]                        │
├─────────────────────────────────────────────┤
│  📊 Ringkasan Deteksi PII                     │
│   NIK: 100   No HP: 98   Email: 95  Nama: 87 │
├─────────────────────────────────────────────┤
│  Preview: Data Asli   |   Data Ter-redaksi   │
│  ┌───────────────┐    ┌───────────────┐      │
│  │ tabel before  │    │ tabel after    │      │
│  └───────────────┘    └───────────────┘      │
│                                                │
│  [ ⬇️ Download Hasil CSV ]                    │
└─────────────────────────────────────────────┘
```

Sederhana, tapi cukup untuk demo internal ke tim HR/Legal — mereka bisa lihat langsung "sebelum vs sesudah" tanpa perlu paham kode sama sekali.

---

## 5. Struktur Project yang Disarankan

```
pii-redaction-prototype/
├── app.py                      # entry point Streamlit (jalankan: streamlit run app.py)
├── detector.py                 # logic deteksi PII (regex + NER)
├── redactor.py                  # logic masking/redaksi
├── generate_dummy_data.py      # generator data karyawan fiktif untuk testing
├── requirements.txt
├── data/
│   ├── dummy_input.csv          # data dummy sebelum diproses
│   └── output_redacted.csv      # hasil setelah redaksi (auto-generated, hasil download)
├── tests/
│   └── test_detector.py
└── README.md
```

Cara menjalankan UI setelah project jadi:
```bash
streamlit run app.py
```
Browser otomatis terbuka di `http://localhost:8501` — dari situ kamu bisa upload file, klik proses, dan lihat hasilnya langsung.

---

## 6. Dependencies Utama

```txt
streamlit
pandas
spacy
presidio-analyzer
presidio-anonymizer
faker          # untuk generate data dummy realistis
pytest         # untuk unit test
```

Setelah install, jangan lupa download model bahasa untuk spaCy:
```bash
python -m spacy download en_core_web_sm
```
> Catatan: model default spaCy bahasa Inggris. Untuk nama Indonesia, deteksi NER kemungkinan kurang akurat di tahap awal — ini wajar untuk prototipe, akan diperbaiki di tahap fine-tuning (Tahap 3).

---

## 7. Contoh Pola Regex untuk Field Indonesia

| Field | Pola Regex (contoh) |
|---|---|
| NIK | `\b\d{16}\b` |
| No. HP | `\b(?:\+62\|62\|0)8[1-9][0-9]{6,9}\b` |
| NPWP | `\b\d{2}\.\d{3}\.\d{3}\.\d{1}-\d{3}\.\d{3}\b` |
| Email | `\b[\w.-]+@[\w.-]+\.\w+\b` |
| No. Rekening (umum, 10–16 digit) | `\b\d{10,16}\b` *(perlu konteks tambahan agar tidak bentrok dengan NIK)* |

---

## 8. Checklist Validasi Prototipe

Sebelum lanjut ke Tahap 2 (MVP), pastikan:

- [ ] Sistem berhasil mendeteksi minimal 4 jenis PII dasar (NIK, no HP, email, nama) dari data dummy
- [ ] Recall deteksi diukur manual (bandingkan hasil deteksi vs data asli yang sudah diketahui)
- [ ] Output file redaksi bisa dibuka & format tetap rapi (tidak merusak struktur CSV)
- [ ] Ada laporan sederhana: total baris diproses, total PII ditemukan per kategori
- [ ] UI Streamlit berjalan lokal tanpa error, upload-proses-download berjalan lancar end-to-end
- [ ] Preview before/after di UI menampilkan data dengan benar dan mudah dibandingkan
- [ ] Kode sudah di-review untuk memastikan tidak ada data dummy yang ter-log/ter-print secara tidak sengaja ke console/log file

---

## 9. Langkah Setelah Prototipe Berhasil

1. Demokan hasil prototipe (langsung lewat UI Streamlit) ke tim HR/Legal internal untuk validasi kebutuhan.
2. Kumpulkan feedback: field PII apa yang masih kelewat, format dokumen apa yang perlu ditambahkan, dan masukan soal UX dari UI.
3. Lanjut ke **Tahap 2 (MVP dengan Human-in-the-Loop)** sesuai solution brief utama — kembangkan UI Streamlit ini menjadi dashboard yang lebih lengkap (role-based login, dukungan OCR, riwayat proses/audit trail), dan mulai uji coba dengan sampel data HR riil (dengan persetujuan & pengawasan tim Legal/Compliance).

---

*Dokumen ini adalah panduan teknis pendamping dari `Solution_Brief_PII_Redaction_System.md`, khusus untuk eksekusi Tahap 2 (Prototipe) menggunakan Antigravity.*
