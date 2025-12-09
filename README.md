# pertemuan-11-pbo-# Refactoring Validator - Praktikum INF2143 (Modul 11) 

## Ringkasan
Tugas: Merefactor sistem validasi registrasi mahasiswa yang awalnya ditangani oleh satu kelas monolitik (ValidatorManager) sehingga melanggar prinsip SOLID, menjadi arsitektur berbasis *IValidationRule* dan *RegistrationService* yang menerima daftar rule via Dependency Injection.

## Analisis Pelanggaran (Sebelum)
- *SRP (Single Responsibility Principle)*: ValidatorManager menangani beberapa tanggung jawab (cek SKS, cek prasyarat, cek jadwal) sekaligus. Satu kelas memiliki banyak alasan untuk berubah.
- *OCP (Open/Closed Principle)*: Untuk menambah aturan validasi baru (mis. cek jadwal bentrok), kita harus membuka dan memodifikasi ValidatorManager—tidak terbuka untuk ekstensi tanpa modifikasi.
- *DIP (Dependency Inversion Principle)*: ValidatorManager bergantung langsung pada logika konkret (if/else) bukan pada abstraksi. High-level module tidak terpisah dari detil.

## Perubahan yang Dilakukan (Setelah)
- Dibuat abstraksi IValidationRule(ABC) dengan method validate.
- Implementasi konkret:
  - SksLimitRule — memeriksa batas SKS
  - PrerequisiteRule — memeriksa prasyarat mata kuliah
  - JadwalBentrokRule — memeriksa bentrokan jadwal (challenge)
- RegistrationService bertindak sebagai koordinator (hanya satu tanggung jawab: menjalankan daftar rule). Ia menerima daftar IValidationRule melalui constructor (Dependency Injection).

## Mengapa ini lebih baik?
- *SRP*: Setiap rule memiliki satu alasan untuk berubah.
- *OCP*: Menambahkan rule baru cukup membuat kelas baru yang mengimplementasikan IValidationRule dan menyuntikkannya — tanpa mengubah RegistrationService.
- *DIP*: RegistrationService hanya tergantung pada abstraksi IValidationRule, bukan implementasi konkret.

## Cara Menjalankan
1. Pastikan Python 3.8+ terpasang.
2. Jalankan:
