# Solution Brief: PII Redaction & Anonymization Generator (PRAG)

**Internal Employee Document Privacy Automation System**

---

## 1. Latar Belakang & Masalah

Divisi HR, Finance, dan IT di perusahaan menyimpan ribuan dokumen internal yang mengandung *Personally Identifiable Information* (PII) milik karyawan — nama, NIK/KTP, no. HP, alamat rumah, tanggal lahir, no. rekening gaji, NPWP, data keluarga (untuk BPJS/asuransi), riwayat kesehatan (untuk klaim medis), hasil performance review, hingga data gaji.

Dokumen-dokumen ini sering perlu **dibagikan atau diproses lebih lanjut** untuk keperluan seperti:

- Analisis data HR (attrition analysis, engagement survey, workforce planning) oleh tim People Analytics
- Sharing dengan vendor payroll/asuransi/BPJS pihak ketiga
- Audit internal (finance audit, compliance audit, ISO)
- Training model AI internal (misal: chatbot HR, sistem rekomendasi talent, analisis sentimen survey karyawan)
- Litigasi ketenagakerjaan atau investigasi internal (dokumen harus di-redact sebelum diserahkan ke pihak eksternal/legal)
- Backup/migrasi sistem HRIS ke platform baru

Proses manual redaksi PII karyawan (dikerjakan tim HR/legal satu-satu) **lambat, berisiko human error, dan rawan pelanggaran UU PDP (Pelindungan Data Pribadi)** — apalagi jika volume dokumen besar (ribuan karyawan × banyak jenis dokumen). Di sinilah dibutuhkan sistem otomatis internal: **PII Redaction & Anonymization Generator (PRAG) untuk Dokumen Karyawan**.

---

## 2. Real Use Case Internal Perusahaan

### Use Case 1 — People Analytics: Analisis Data HR Tanpa Membocorkan Identitas
Tim People Analytics ingin menganalisis pola turnover, hasil engagement survey, dan data kompensasi untuk insight strategis. Sebelum data dibagikan ke analyst (apalagi jika ada konsultan eksternal terlibat), sistem otomatis menyamarkan nama, NIK, dan data identitas langsung — namun tetap mempertahankan atribut relevan (divisi, level jabatan, masa kerja, skor performance) agar analisis tetap valid.

### Use Case 2 — Sharing Data ke Vendor Payroll/Asuransi/BPJS
Setiap bulan, data karyawan (gaji, no. rekening, NIK, data keluarga) dikirim ke vendor payroll eksternal atau perusahaan asuransi. Sistem PRAG memastikan hanya field yang benar-benar dibutuhkan vendor yang terbuka, sementara data sensitif lain di-mask otomatis sesuai kebutuhan (prinsip *data minimization* dalam UU PDP).

### Use Case 3 — Audit Internal & Investigasi Ketenagakerjaan
Saat ada audit internal (finance/compliance) atau investigasi kasus (misal dugaan pelanggaran kode etik), dokumen terkait (email, chat, kontrak kerja, slip gaji) perlu direview oleh tim audit/legal. PII karyawan yang tidak relevan dengan kasus (misal karyawan lain yang hanya disebut sekilas) otomatis di-redact sebelum dokumen dibuka ke tim investigasi atau pihak eksternal (pengacara, regulator).

### Use Case 4 — Training Chatbot HR Internal / AI Assistant Karyawan
Perusahaan ingin membangun chatbot HR internal (misal untuk tanya-jawab kebijakan cuti, benefit, dsb) yang dilatih dari histori tiket HR & FAQ karyawan sebelumnya. Data historis ini mengandung nama & NIK karyawan yang bertanya — sistem PRAG membersihkan data ini otomatis sebelum dipakai untuk fine-tuning model AI internal.

### Use Case 5 — Migrasi Sistem HRIS / Backup Arsip Digital
Saat perusahaan pindah dari sistem HRIS lama ke platform baru, atau mendigitalisasi arsip fisik karyawan (kontrak kerja lama, ijazah, dokumen medical check-up), sistem otomatis membantu mengklasifikasikan dan menyamarkan dokumen yang butuh level kerahasiaan lebih tinggi sebelum diakses tim IT/migrasi.

---

## 3. Tujuan Sistem

1. **Otomatisasi deteksi PII karyawan** dalam berbagai jenis dokumen internal (kontrak kerja PDF, slip gaji, hasil performance review DOCX, data Excel HRIS, scan KTP/ijazah, email/chat HR).
2. **Redaksi/anonimisasi konsisten sesuai UU PDP** (dan kebijakan internal data governance perusahaan), termasuk prinsip *data minimization* — hanya membagikan data yang benar-benar diperlukan tiap pihak (vendor, auditor, analyst).
3. **Menjaga utilitas data untuk keperluan internal** — misalnya untuk People Analytics, data tetap bisa dianalisis (divisi, jabatan, tenure, skor performance) meski identitas personal sudah disamarkan (`[EMP_001]` konsisten dipakai untuk karyawan yang sama di seluruh dokumen terkait).
4. **Role-based access & audit trail** — level redaksi bisa berbeda tergantung siapa yang mengakses (misal: tim Finance lihat data gaji lengkap, tim eksternal hanya lihat versi ter-mask), dan semua akses/redaksi tercatat untuk audit.
5. **Human-in-the-loop review** — tim HR/Legal internal tetap melakukan spot-check untuk dokumen sensitif tinggi (investigasi, litigasi) sebelum dokumen dibagikan keluar.
6. **Scalable secara bertahap** — dimulai dari satu divisi/proses (misal payroll bulanan), lalu diperluas ke seluruh dokumen HR perusahaan.

---

## 4. Arsitektur Sistem (High-Level)

```
[Input Layer]
   Dokumen karyawan: kontrak kerja (PDF/DOCX), slip gaji, data HRIS (Excel/CSV),
   scan KTP/KK/ijazah, hasil performance review, email/tiket HR, chat internal
        │
        ▼
[Ingestion & OCR Layer]
   - OCR untuk dokumen scan (KTP, ijazah, kontrak fisik) — Tesseract / AWS Textract / Google Vision
   - Parser format dokumen (PDF, DOCX, XLSX/CSV dari sistem HRIS)
   - Koneksi langsung ke sumber data internal (HRIS, payroll system, shared drive HR)
        │
        ▼
[PII Detection Engine]
   - Rule-based (Regex): NIK, NPWP, no. HP, email, no. rekening
   - NER Model (Named Entity Recognition): nama karyawan, nama anggota keluarga, alamat
       → Model: spaCy / Presidio (Microsoft) / fine-tuned untuk format dokumen HR Indonesia
   - Context-aware detection (LLM-based) untuk kasus ambigu (misal nama atasan di kontrak vs nama karyawan itu sendiri)
        │
        ▼
[Anonymization/Redaction Engine]
   - Redaction: hapus/blok total (■■■■) — untuk dokumen keluar ke pihak eksternal
   - Masking: sebagian (081****5678) — untuk dashboard internal level tertentu
   - Tokenization: ganti dengan ID konsisten ([EMP_001] selalu merujuk karyawan yang sama di seluruh dokumen)
   - Role-based redaction: level redaksi berbeda sesuai role pengakses (HRBP, Finance, vendor eksternal, auditor)
        │
        ▼
[Human-in-the-Loop Review Layer]
   - Dashboard untuk tim HR/Legal internal melakukan spot-check
   - Flagging kasus low-confidence (misal nama yang ambigu) untuk direview manual
   - Feedback loop → dipakai retrain model deteksi khusus format dokumen internal perusahaan
        │
        ▼
[Output & Audit Layer]
   - Dokumen hasil anonimisasi sesuai tujuan (analytics/vendor/audit/AI training)
   - Audit log (siapa akses, kapan, dokumen apa, level redaksi apa)
   - Compliance report internal (untuk keperluan audit UU PDP / ISO 27001)
```

---

## 5. Tahapan Pengerjaan: Prototipe → Enterprise

### **Tahap 1 — Discovery & Requirement (1–2 minggu)**
- Inventarisasi jenis dokumen karyawan yang ada (kontrak kerja, slip gaji, data HRIS, hasil performance review, dokumen medical check-up, dsb) beserta lokasinya (HRIS, shared drive, email, sistem payroll).
- Petakan field PII apa saja yang muncul di tiap jenis dokumen (NIK, NPWP, no. rekening, alamat, data keluarga).
- Tentukan kebutuhan compliance internal (UU PDP, kebijakan data governance perusahaan, kontrak dengan vendor pihak ketiga).
- Tentukan siapa saja yang akan mengakses data hasil anonimisasi (People Analytics, vendor payroll, auditor, tim legal) dan level redaksi yang dibutuhkan tiap pihak.

### **Tahap 2 — Prototipe / Proof of Concept (2–4 minggu)**
- Bangun pipeline sederhana: regex + open-source NER (spaCy / Microsoft Presidio) untuk deteksi PII dasar pada dokumen HR (nama, NIK, email, no. HP).
- Uji coba pada satu jenis dokumen dulu — misal slip gaji atau data Excel HRIS satu divisi (contoh: 50–100 data karyawan).
- Output: dokumen/data hasil redaksi + laporan akurasi (precision/recall) yang direview tim HR internal.
- Tools: Python, spaCy/Presidio, Streamlit untuk demo dashboard internal sederhana.

### **Tahap 3 — MVP dengan Human-in-the-Loop (1–2 bulan)**
- Tambahkan dashboard review untuk tim HR/Legal internal melakukan spot-check hasil redaksi.
- Tambahkan dukungan OCR untuk dokumen scan (KTP, ijazah, kontrak kerja lama yang masih fisik).
- Fine-tune model NER dengan pola dokumen HR internal perusahaan (format kontrak, template slip gaji, dsb — biasanya beda dari dokumen umum).
- Bangun sistem tokenization konsisten (`[EMP_001]` selalu merujuk karyawan yang sama di seluruh dokumen terkait).
- Implementasi role-based redaction dasar (misal: HR lihat data penuh, vendor eksternal lihat versi ter-mask).

### **Tahap 4 — Pilot di Satu Proses Bisnis (2–3 bulan)**
- Terapkan penuh pada satu proses nyata terlebih dahulu — misal proses bulanan pengiriman data ke vendor payroll/BPJS, atau proses People Analytics kuartalan.
- Integrasi langsung dengan sistem HRIS/payroll perusahaan (via API atau scheduled export).
- Tambahkan audit trail lengkap (siapa akses, kapan, level redaksi apa) & compliance reporting otomatis untuk keperluan audit internal.
- Ukur metrik: akurasi deteksi, waktu proses, dan yang paling kritikal — tingkat false negative (PII karyawan yang kelolosan), karena berisiko pelanggaran UU PDP dan menyangkut kepercayaan karyawan terhadap perusahaan.

### **Tahap 5 — Rollout ke Seluruh Divisi/Proses HR (3–6 bulan)**
- Perluas ke seluruh jenis dokumen karyawan (kontrak, performance review, dokumen investigasi, arsip lama) dan seluruh divisi.
- Infrastruktur internal yang scalable (bisa on-premise jika data sangat sensitif, atau private cloud sesuai kebijakan IT security perusahaan).
- Continuous feedback loop: hasil review tim HR terus dipakai retrain model secara berkala agar makin akurat mengenali format dokumen internal.
- Selaraskan dengan kebijakan retensi data & hak akses karyawan (misal hak karyawan untuk tahu data apa yang disimpan/diproses, sesuai UU PDP).
- SLA internal, monitoring, dan prosedur eskalasi jika ditemukan kebocoran/kesalahan redaksi.

### **Tahap 6 — Maintenance & Continuous Improvement (ongoing)**
- Monitoring perubahan format dokumen baru (misal template kontrak kerja baru, sistem HRIS baru) yang mungkin belum dikenali sistem.
- Update kebijakan internal & regulasi terbaru (perubahan UU PDP, kebijakan perusahaan) ke dalam sistem compliance.
- Evaluasi berkala bersama tim HR, Legal, dan IT Security terhadap efektivitas sistem.

---

## 6. Tech Stack yang Disarankan

| Layer | Teknologi |
|---|---|
| OCR | AWS Textract / Google Document AI / Tesseract (untuk scan KTP, ijazah, kontrak fisik) |
| PII Detection | Microsoft Presidio, spaCy NER, atau LLM internal (fine-tuned untuk format dokumen HR perusahaan) |
| Backend Pipeline | Python (FastAPI), Apache Airflow (orkestrasi proses batch bulanan, misal payroll) |
| Integrasi Sumber Data | API/connector ke HRIS (misal Workday, SAP SuccessFactors, atau sistem HRIS internal), shared drive perusahaan |
| Storage | On-premise server atau private cloud terenkripsi (sesuai kebijakan IT Security perusahaan), PostgreSQL untuk metadata & audit log |
| Human Review Dashboard | React/Next.js + backend API, dengan role-based login (HR, Legal, Finance) |
| Deployment | Docker + Kubernetes (bisa dimulai dari VM internal untuk pilot, scale ke cluster jika sudah rollout penuh) |
| Monitoring | Grafana + Prometheus, plus internal compliance logging (terintegrasi dengan tim IT Security/GRC) |

> Catatan: karena ini dokumen internal karyawan yang sangat sensitif, disarankan **on-premise atau private cloud** dibanding public cloud murni, tergantung kebijakan keamanan data perusahaan.

---

## 7. Metrik Keberhasilan (KPI)

- **Recall PII detection** — target >98%, karena data karyawan yang kelolosan = risiko pelanggaran UU PDP & menurunkan kepercayaan karyawan terhadap perusahaan.
- **Precision** — hindari over-redaction yang membuat data tidak berguna lagi untuk People Analytics.
- **Waktu proses** — misal target proses data payroll bulanan yang tadinya manual berhari-hari menjadi hitungan jam.
- **Human review rate** — persentase dokumen yang masih perlu direview manual tim HR/Legal, ditargetkan menurun seiring model membaik.
- **Kepatuhan internal audit** — hasil audit UU PDP/ISO 27001 terkait pengelolaan data karyawan.

---

## 8. Risiko & Mitigasi

| Risiko | Mitigasi |
|---|---|
| PII karyawan kelolosan (false negative) | Kombinasi rule-based + ML + human review wajib untuk dokumen sensitif tinggi (investigasi, litigasi, data kesehatan) |
| Data karyawan diakses pihak yang tidak berwenang | Role-based access control ketat + audit log setiap akses |
| Model salah kenali format dokumen internal baru | Fine-tuning berkelanjutan dengan feedback tim HR internal |
| Resistensi internal (tim HR terbiasa proses manual) | Sosialisasi & pelatihan, mulai dari pilot kecil sebelum rollout penuh |
| Perubahan regulasi/kebijakan internal | Sistem compliance rule yang modular & mudah diupdate oleh tim Legal/GRC |

---

## 9. Rekomendasi Langkah Awal

1. Mulai dari **satu proses paling berulang dan berisiko tinggi** — misal proses bulanan kirim data ke vendor payroll/BPJS, karena dampaknya jelas terukur (waktu proses, kepatuhan) dan volumenya konsisten tiap bulan untuk uji coba sistem.
2. Libatkan tim **HR, Legal/Compliance, dan IT Security** sejak tahap discovery, bukan hanya tim teknis — karena keputusan level redaksi dan kebijakan akses data karyawan butuh persetujuan lintas fungsi.
3. Jangan langsung full automation — pertahankan **human-in-the-loop** di tahap awal untuk membangun kepercayaan terhadap akurasi sistem sebelum mengurangi review manual secara bertahap.

---

*Dokumen ini adalah draft awal solution brief untuk kebutuhan internal — dapat disesuaikan lebih lanjut sesuai struktur organisasi, sistem HRIS yang dipakai, serta kebijakan data governance yang berlaku di perusahaan Anda.*
