"""
SafeNote Localization Module.

Provides a complete translation system with support for Turkish (tr),
English (en), and Azerbaijani (az).  Translations are stored as plain
dictionaries keyed by short identifier strings.  The ``Localization``
class wraps a chosen dictionary and exposes a ``tr()`` lookup method.
"""

from __future__ import annotations


# ============================================================================
# TURKISH TRANSLATIONS
# ============================================================================

TRANSLATIONS_TR: dict[str, str] = {
    # -- Application --------------------------------------------------------
    "app_name": "SafeNote",
    "slogan": "Gizliliğinize Saygı Duyan Ses Kaydı",

    # -- Navigation ---------------------------------------------------------
    "dashboard": "Ana Panel",
    "recording": "Kayıt",
    "library": "Kütüphane",
    "player": "Oynatıcı",
    "settings": "Ayarlar",
    "about": "Hakkında",

    # -- Recording ----------------------------------------------------------
    "start_recording": "Kaydı Başlat",
    "stop_recording": "Kaydı Durdur",
    "recording_active": "Kayıt Devam Ediyor",
    "recording_saved": "Kayıt Kaydedildi",
    "recording_ready": "Kayda Hazır",
    "microphone_active": "Mikrofon Etkin",
    "pause_recording": "Kaydı Duraklat",
    "resume_recording": "Kaydı Sürdür",
    "recording_paused": "Kayıt Duraklatıldı",
    "recording_duration": "Kayıt Süresi",
    "new_recording": "Yeni Kayıt",

    # -- Emergency ----------------------------------------------------------
    "emergency_hide": "Acil Gizle",
    "emergency_hide_desc": "Uygulamayı anında gizler ve kayıtları şifreler",
    "unlock": "Kilidi Aç",
    "workspace_locked": "Çalışma Alanı Kilitli",
    "workspace_locked_desc": "Devam etmek için kimliğinizi doğrulayın",

    # -- Player -------------------------------------------------------------
    "play": "Oynat",
    "pause": "Duraklat",
    "resume": "Devam Et",
    "stop": "Durdur",
    "seek_forward": "İleri Sar",
    "seek_backward": "Geri Sar",
    "volume": "Ses",
    "duration": "Süre",
    "position": "Konum",
    "no_recording_loaded": "Yüklü Kayıt Yok",
    "playback_speed": "Oynatma Hızı",

    # -- Decryption / Errors ------------------------------------------------
    "decryption_failed": "Şifre Çözme Başarısız",
    "file_corrupted": "Dosya Bozulmuş",
    "wrong_key": "Yanlış Anahtar",

    # -- Library ------------------------------------------------------------
    "search": "Ara",
    "sort_by": "Sırala",
    "filter_by": "Filtrele",
    "name": "Ad",
    "date": "Tarih",
    "size": "Boyut",
    "duration_col": "Süre",
    "rename": "Yeniden Adlandır",
    "delete": "Sil",
    "delete_confirm": "Silme Onayı",
    "delete_confirm_msg": "Bu kaydı silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.",
    "recording_details": "Kayıt Detayları",
    "export_wav": "WAV Olarak Dışa Aktar",
    "export_warning": "Dışa aktarılan dosya şifrelenmeyecektir. Devam etmek istiyor musunuz?",
    "import_recording": "Kayıt İçe Aktar",
    "file_saved": "Dosya Kaydedildi",
    "file_exists_overwrite": "Dosya zaten mevcut. Üzerine yazmak istiyor musunuz?",
    "no_recordings": "Henüz kayıt yok",
    "total_recordings": "Toplam Kayıt",
    "total_duration": "Toplam Süre",
    "total_size": "Toplam Boyut",
    "select_all": "Tümünü Seç",
    "deselect_all": "Seçimi Kaldır",
    "selected_count": "{} kayıt seçildi",
    "confirm_delete_multiple": "{} kaydı silmek istediğinizden emin misiniz?",

    # -- Settings sections --------------------------------------------------
    "settings_general": "Genel Ayarlar",
    "settings_audio": "Ses Ayarları",
    "settings_security": "Güvenlik Ayarları",
    "settings_shortcuts": "Kısayol Ayarları",
    "settings_language": "Dil Ayarları",
    "settings_storage": "Depolama Ayarları",
    "settings_about": "Hakkında",

    # -- Settings values ----------------------------------------------------
    "language": "Dil",
    "theme": "Tema",
    "theme_dark": "Koyu",
    "theme_light": "Açık",
    "auto_start": "Otomatik Başlat",
    "start_minimized": "Küçültülmüş Başlat",
    "check_updates": "Güncellemeleri Kontrol Et",
    "storage_directory": "Depolama Dizini",
    "browse": "Gözat",
    "sample_rate": "Örnekleme Hızı",
    "channels": "Kanallar",
    "mono": "Mono",
    "stereo": "Stereo",
    "shortcut_emergency": "Acil Gizleme Kısayolu",
    "shortcut_record": "Kayıt Kısayolu",
    "reset_defaults": "Varsayılanlara Sıfırla",
    "settings_saved": "Ayarlar Kaydedildi",
    "restart_required": "Değişikliklerin uygulanması için yeniden başlatma gerekli",

    # -- Common actions / buttons -------------------------------------------
    "apply": "Uygula",
    "cancel": "İptal",
    "save": "Kaydet",
    "ok": "Tamam",
    "error": "Hata",
    "warning": "Uyarı",
    "info": "Bilgi",
    "close": "Kapat",
    "confirm": "Onayla",
    "yes": "Evet",
    "no": "Hayır",
    "retry": "Yeniden Dene",
    "copy": "Kopyala",

    # -- First-run wizard ---------------------------------------------------
    "first_run_welcome": "SafeNote'a Hoş Geldiniz",
    "first_run_language": "Tercih ettiğiniz dili seçin",
    "first_run_storage": "Kayıtlarınızın saklanacağı dizini seçin",
    "first_run_theme": "Tercih ettiğiniz temayı seçin",
    "first_run_shortcuts": "Klavye kısayollarınızı yapılandırın",
    "first_run_complete": "Kurulum tamamlandı! Başlamaya hazırsınız.",
    "next": "İleri",
    "previous": "Geri",
    "finish": "Bitir",
    "skip": "Atla",
    "welcome_message": "SafeNote gizliliğe öncelik veren şifreli bir ses kayıt uygulamasıdır.",

    # -- About --------------------------------------------------------------
    "about_version": "Sürüm",
    "about_license": "Lisans: MIT",
    "about_org": "SafeNote Ekibi",
    "about_description": "SafeNote, gizliliğe odaklanan şifreli bir ses kayıt uygulamasıdır. "
                         "Tüm kayıtlarınız yerel olarak şifrelenir ve güvenle saklanır.",
    "about_security_model": "Güvenlik Modeli: Tüm ses kayıtları AES-256-GCM ile şifrelenir. "
                            "Anahtarlar cihazınızdan asla ayrılmaz.",
    "about_credits": "Katkıda Bulunanlar",
    "about_website": "Web Sitesi",

    # -- System tray --------------------------------------------------------
    "tray_open": "SafeNote'u Aç",
    "tray_record": "Kaydı Başlat",
    "tray_stop": "Kaydı Durdur",
    "tray_library": "Kütüphaneyi Aç",
    "tray_hide": "Gizle",
    "tray_exit": "Çıkış",
    "tray_show": "Göster",
    "tray_status_idle": "SafeNote - Boşta",
    "tray_status_recording": "SafeNote - Kayıt Yapılıyor",

    # -- Microphone errors --------------------------------------------------
    "no_microphone": "Mikrofon Bulunamadı",
    "microphone_disconnected": "Mikrofon Bağlantısı Kesildi",
    "recording_interrupted": "Kayıt Kesildi",
    "microphone_permission_denied": "Mikrofon erişim izni reddedildi",
    "select_microphone": "Mikrofon Seçin",

    # -- Encryption info ----------------------------------------------------
    "encryption_info": "Şifreleme Bilgisi",
    "key_management": "Anahtar Yönetimi",
    "key_warning": "Şifreleme anahtarınızı kaybederseniz kayıtlarınıza erişemezsiniz.",
    "key_backup_warning": "Lütfen şifreleme anahtarınızı güvenli bir yere yedekleyin.",
    "encryption_algorithm": "Şifreleme Algoritması",
    "key_derived": "Anahtar türetildi",
    "change_password": "Şifre Değiştir",
    "current_password": "Mevcut Şifre",
    "new_password": "Yeni Şifre",
    "confirm_password": "Şifreyi Onayla",
    "password_mismatch": "Şifreler uyuşmuyor",
    "password_too_short": "Şifre çok kısa",

    # -- Status bar ---------------------------------------------------------
    "status_ready": "Hazır",
    "status_recording": "Kayıt Yapılıyor",
    "status_playing": "Oynatılıyor",
    "status_paused": "Duraklatıldı",
    "status_error": "Hata Oluştu",
    "status_encrypting": "Şifreleniyor",
    "status_decrypting": "Şifre çözülüyor",
    "status_exporting": "Dışa aktarılıyor",
    "status_importing": "İçe aktarılıyor",

    # -- Miscellaneous ------------------------------------------------------
    "loading": "Yükleniyor...",
    "processing": "İşleniyor...",
    "unknown_error": "Bilinmeyen bir hata oluştu",
    "disk_space_low": "Disk alanı düşük",
    "unsaved_changes": "Kaydedilmemiş değişiklikler var. Çıkmak istediğinizden emin misiniz?",
    "format_hours": "sa",
    "format_minutes": "dk",
    "format_seconds": "sn",
}


# ============================================================================
# ENGLISH TRANSLATIONS
# ============================================================================

TRANSLATIONS_EN: dict[str, str] = {
    # -- Application --------------------------------------------------------
    "app_name": "SafeNote",
    "slogan": "Audio Recording That Respects Your Privacy",

    # -- Navigation ---------------------------------------------------------
    "dashboard": "Dashboard",
    "recording": "Recording",
    "library": "Library",
    "player": "Player",
    "settings": "Settings",
    "about": "About",

    # -- Recording ----------------------------------------------------------
    "start_recording": "Start Recording",
    "stop_recording": "Stop Recording",
    "recording_active": "Recording in Progress",
    "recording_saved": "Recording Saved",
    "recording_ready": "Ready to Record",
    "microphone_active": "Microphone Active",
    "pause_recording": "Pause Recording",
    "resume_recording": "Resume Recording",
    "recording_paused": "Recording Paused",
    "recording_duration": "Recording Duration",
    "new_recording": "New Recording",

    # -- Emergency ----------------------------------------------------------
    "emergency_hide": "Emergency Hide",
    "emergency_hide_desc": "Instantly hides the application and encrypts recordings",
    "unlock": "Unlock",
    "workspace_locked": "Workspace Locked",
    "workspace_locked_desc": "Verify your identity to continue",

    # -- Player -------------------------------------------------------------
    "play": "Play",
    "pause": "Pause",
    "resume": "Resume",
    "stop": "Stop",
    "seek_forward": "Seek Forward",
    "seek_backward": "Seek Backward",
    "volume": "Volume",
    "duration": "Duration",
    "position": "Position",
    "no_recording_loaded": "No Recording Loaded",
    "playback_speed": "Playback Speed",

    # -- Decryption / Errors ------------------------------------------------
    "decryption_failed": "Decryption Failed",
    "file_corrupted": "File Corrupted",
    "wrong_key": "Wrong Key",

    # -- Library ------------------------------------------------------------
    "search": "Search",
    "sort_by": "Sort By",
    "filter_by": "Filter By",
    "name": "Name",
    "date": "Date",
    "size": "Size",
    "duration_col": "Duration",
    "rename": "Rename",
    "delete": "Delete",
    "delete_confirm": "Confirm Deletion",
    "delete_confirm_msg": "Are you sure you want to delete this recording? This action cannot be undone.",
    "recording_details": "Recording Details",
    "export_wav": "Export as WAV",
    "export_warning": "The exported file will not be encrypted. Do you want to continue?",
    "import_recording": "Import Recording",
    "file_saved": "File Saved",
    "file_exists_overwrite": "File already exists. Do you want to overwrite it?",
    "no_recordings": "No recordings yet",
    "total_recordings": "Total Recordings",
    "total_duration": "Total Duration",
    "total_size": "Total Size",
    "select_all": "Select All",
    "deselect_all": "Deselect All",
    "selected_count": "{} recordings selected",
    "confirm_delete_multiple": "Are you sure you want to delete {} recordings?",

    # -- Settings sections --------------------------------------------------
    "settings_general": "General Settings",
    "settings_audio": "Audio Settings",
    "settings_security": "Security Settings",
    "settings_shortcuts": "Shortcut Settings",
    "settings_language": "Language Settings",
    "settings_storage": "Storage Settings",
    "settings_about": "About",

    # -- Settings values ----------------------------------------------------
    "language": "Language",
    "theme": "Theme",
    "theme_dark": "Dark",
    "theme_light": "Light",
    "auto_start": "Auto Start",
    "start_minimized": "Start Minimized",
    "check_updates": "Check for Updates",
    "storage_directory": "Storage Directory",
    "browse": "Browse",
    "sample_rate": "Sample Rate",
    "channels": "Channels",
    "mono": "Mono",
    "stereo": "Stereo",
    "shortcut_emergency": "Emergency Hide Shortcut",
    "shortcut_record": "Record Shortcut",
    "reset_defaults": "Reset to Defaults",
    "settings_saved": "Settings Saved",
    "restart_required": "Restart required for changes to take effect",

    # -- Common actions / buttons -------------------------------------------
    "apply": "Apply",
    "cancel": "Cancel",
    "save": "Save",
    "ok": "OK",
    "error": "Error",
    "warning": "Warning",
    "info": "Info",
    "close": "Close",
    "confirm": "Confirm",
    "yes": "Yes",
    "no": "No",
    "retry": "Retry",
    "copy": "Copy",

    # -- First-run wizard ---------------------------------------------------
    "first_run_welcome": "Welcome to SafeNote",
    "first_run_language": "Choose your preferred language",
    "first_run_storage": "Choose the directory where your recordings will be stored",
    "first_run_theme": "Choose your preferred theme",
    "first_run_shortcuts": "Configure your keyboard shortcuts",
    "first_run_complete": "Setup complete! You are ready to go.",
    "next": "Next",
    "previous": "Previous",
    "finish": "Finish",
    "skip": "Skip",
    "welcome_message": "SafeNote is an encrypted audio recording application that puts privacy first.",

    # -- About --------------------------------------------------------------
    "about_version": "Version",
    "about_license": "License: MIT",
    "about_org": "SafeNote Team",
    "about_description": "SafeNote is a privacy-focused encrypted audio recording application. "
                         "All your recordings are encrypted locally and stored securely.",
    "about_security_model": "Security Model: All audio recordings are encrypted with AES-256-GCM. "
                            "Keys never leave your device.",
    "about_credits": "Credits",
    "about_website": "Website",

    # -- System tray --------------------------------------------------------
    "tray_open": "Open SafeNote",
    "tray_record": "Start Recording",
    "tray_stop": "Stop Recording",
    "tray_library": "Open Library",
    "tray_hide": "Hide",
    "tray_exit": "Exit",
    "tray_show": "Show",
    "tray_status_idle": "SafeNote - Idle",
    "tray_status_recording": "SafeNote - Recording",

    # -- Microphone errors --------------------------------------------------
    "no_microphone": "No Microphone Found",
    "microphone_disconnected": "Microphone Disconnected",
    "recording_interrupted": "Recording Interrupted",
    "microphone_permission_denied": "Microphone access permission denied",
    "select_microphone": "Select Microphone",

    # -- Encryption info ----------------------------------------------------
    "encryption_info": "Encryption Info",
    "key_management": "Key Management",
    "key_warning": "If you lose your encryption key, you will not be able to access your recordings.",
    "key_backup_warning": "Please back up your encryption key to a safe location.",
    "encryption_algorithm": "Encryption Algorithm",
    "key_derived": "Key derived",
    "change_password": "Change Password",
    "current_password": "Current Password",
    "new_password": "New Password",
    "confirm_password": "Confirm Password",
    "password_mismatch": "Passwords do not match",
    "password_too_short": "Password is too short",

    # -- Status bar ---------------------------------------------------------
    "status_ready": "Ready",
    "status_recording": "Recording",
    "status_playing": "Playing",
    "status_paused": "Paused",
    "status_error": "Error Occurred",
    "status_encrypting": "Encrypting",
    "status_decrypting": "Decrypting",
    "status_exporting": "Exporting",
    "status_importing": "Importing",

    # -- Miscellaneous ------------------------------------------------------
    "loading": "Loading...",
    "processing": "Processing...",
    "unknown_error": "An unknown error occurred",
    "disk_space_low": "Disk space is low",
    "unsaved_changes": "You have unsaved changes. Are you sure you want to exit?",
    "format_hours": "h",
    "format_minutes": "m",
    "format_seconds": "s",
}


# ============================================================================
# AZERBAIJANI TRANSLATIONS
# ============================================================================

TRANSLATIONS_AZ: dict[str, str] = {
    # -- Application --------------------------------------------------------
    "app_name": "SafeNote",
    "slogan": "Məxfiliyinizə Hörmət Edən Səs Yazması",

    # -- Navigation ---------------------------------------------------------
    "dashboard": "İdarə Paneli",
    "recording": "Yazma",
    "library": "Kitabxana",
    "player": "Pleyер",
    "settings": "Parametrlər",
    "about": "Haqqında",

    # -- Recording ----------------------------------------------------------
    "start_recording": "Yazmağa Başla",
    "stop_recording": "Yazmanı Dayandır",
    "recording_active": "Yazma Davam Edir",
    "recording_saved": "Yazma Saxlanıldı",
    "recording_ready": "Yazmağa Hazır",
    "microphone_active": "Mikrofon Aktivdir",
    "pause_recording": "Yazmanı Fasilə Et",
    "resume_recording": "Yazmanı Davam Etdir",
    "recording_paused": "Yazma Fasilə Edildi",
    "recording_duration": "Yazma Müddəti",
    "new_recording": "Yeni Yazma",

    # -- Emergency ----------------------------------------------------------
    "emergency_hide": "Təcili Gizlət",
    "emergency_hide_desc": "Tətbiqi dərhal gizlədir və yazmaları şifrələyir",
    "unlock": "Kilidi Aç",
    "workspace_locked": "İş Sahəsi Kilidlidir",
    "workspace_locked_desc": "Davam etmək üçün şəxsiyyətinizi təsdiqləyin",

    # -- Player -------------------------------------------------------------
    "play": "Oxut",
    "pause": "Fasilə",
    "resume": "Davam Et",
    "stop": "Dayandır",
    "seek_forward": "İrəli Sar",
    "seek_backward": "Geri Sar",
    "volume": "Səs",
    "duration": "Müddət",
    "position": "Mövqe",
    "no_recording_loaded": "Yazma Yüklənməyib",
    "playback_speed": "Oxutma Sürəti",

    # -- Decryption / Errors ------------------------------------------------
    "decryption_failed": "Şifrə Açma Uğursuz Oldu",
    "file_corrupted": "Fayl Zədələnib",
    "wrong_key": "Yanlış Açar",

    # -- Library ------------------------------------------------------------
    "search": "Axtar",
    "sort_by": "Sırala",
    "filter_by": "Süzgəclə",
    "name": "Ad",
    "date": "Tarix",
    "size": "Ölçü",
    "duration_col": "Müddət",
    "rename": "Adını Dəyiş",
    "delete": "Sil",
    "delete_confirm": "Silməni Təsdiqlə",
    "delete_confirm_msg": "Bu yazmanı silmək istədiyinizə əminsiniz? Bu əməliyyat geri qaytarıla bilməz.",
    "recording_details": "Yazma Təfərrüatları",
    "export_wav": "WAV Olaraq İxrac Et",
    "export_warning": "İxrac edilən fayl şifrələnməyəcək. Davam etmək istəyirsiniz?",
    "import_recording": "Yazma İdxal Et",
    "file_saved": "Fayl Saxlanıldı",
    "file_exists_overwrite": "Fayl artıq mövcuddur. Üzərinə yazmaq istəyirsiniz?",
    "no_recordings": "Hələ yazma yoxdur",
    "total_recordings": "Ümumi Yazmalar",
    "total_duration": "Ümumi Müddət",
    "total_size": "Ümumi Ölçü",
    "select_all": "Hamısını Seç",
    "deselect_all": "Seçimi Ləğv Et",
    "selected_count": "{} yazma seçildi",
    "confirm_delete_multiple": "{} yazmanı silmək istədiyinizə əminsiniz?",

    # -- Settings sections --------------------------------------------------
    "settings_general": "Ümumi Parametrlər",
    "settings_audio": "Səs Parametrləri",
    "settings_security": "Təhlükəsizlik Parametrləri",
    "settings_shortcuts": "Qısayol Parametrləri",
    "settings_language": "Dil Parametrləri",
    "settings_storage": "Yaddaş Parametrləri",
    "settings_about": "Haqqında",

    # -- Settings values ----------------------------------------------------
    "language": "Dil",
    "theme": "Mövzu",
    "theme_dark": "Qaranlıq",
    "theme_light": "İşıqlı",
    "auto_start": "Avtomatik Başlat",
    "start_minimized": "Kiçildilmiş Başlat",
    "check_updates": "Yeniləmələri Yoxla",
    "storage_directory": "Yaddaş Qovluğu",
    "browse": "Gözdən Keçir",
    "sample_rate": "Nümunə Tezliyi",
    "channels": "Kanallar",
    "mono": "Mono",
    "stereo": "Stereo",
    "shortcut_emergency": "Təcili Gizlətmə Qısayolu",
    "shortcut_record": "Yazma Qısayolu",
    "reset_defaults": "Standart Dəyərlərə Sıfırla",
    "settings_saved": "Parametrlər Saxlanıldı",
    "restart_required": "Dəyişikliklərin tətbiqi üçün yenidən başlatma lazımdır",

    # -- Common actions / buttons -------------------------------------------
    "apply": "Tətbiq Et",
    "cancel": "Ləğv Et",
    "save": "Saxla",
    "ok": "Oldu",
    "error": "Xəta",
    "warning": "Xəbərdarlıq",
    "info": "Məlumat",
    "close": "Bağla",
    "confirm": "Təsdiqlə",
    "yes": "Bəli",
    "no": "Xeyr",
    "retry": "Yenidən Cəhd Et",
    "copy": "Kopyala",

    # -- First-run wizard ---------------------------------------------------
    "first_run_welcome": "SafeNote-a Xoş Gəldiniz",
    "first_run_language": "Üstünlük verdiyiniz dili seçin",
    "first_run_storage": "Yazmalarınızın saxlanacağı qovluğu seçin",
    "first_run_theme": "Üstünlük verdiyiniz mövzunu seçin",
    "first_run_shortcuts": "Klaviatura qısayollarınızı konfiqurasiya edin",
    "first_run_complete": "Quraşdırma tamamlandı! Başlamağa hazırsınız.",
    "next": "İrəli",
    "previous": "Geri",
    "finish": "Bitir",
    "skip": "Keç",
    "welcome_message": "SafeNote məxfiliyə üstünlük verən şifrəli səs yazma tətbiqidir.",

    # -- About --------------------------------------------------------------
    "about_version": "Versiya",
    "about_license": "Lisenziya: MIT",
    "about_org": "SafeNote Komandası",
    "about_description": "SafeNote məxfiliyə yönəlmiş şifrəli səs yazma tətbiqidir. "
                         "Bütün yazmalarınız yerli olaraq şifrələnir və təhlükəsiz saxlanılır.",
    "about_security_model": "Təhlükəsizlik Modeli: Bütün səs yazmaları AES-256-GCM ilə şifrələnir. "
                            "Açarlar heç vaxt cihazınızı tərk etmir.",
    "about_credits": "Əməkdaşlar",
    "about_website": "Veb Sayt",

    # -- System tray --------------------------------------------------------
    "tray_open": "SafeNote-u Aç",
    "tray_record": "Yazmağa Başla",
    "tray_stop": "Yazmanı Dayandır",
    "tray_library": "Kitabxananı Aç",
    "tray_hide": "Gizlət",
    "tray_exit": "Çıxış",
    "tray_show": "Göstər",
    "tray_status_idle": "SafeNote - Gözləmədə",
    "tray_status_recording": "SafeNote - Yazma Aparılır",

    # -- Microphone errors --------------------------------------------------
    "no_microphone": "Mikrofon Tapılmadı",
    "microphone_disconnected": "Mikrofon Əlaqəsi Kəsildi",
    "recording_interrupted": "Yazma Kəsildi",
    "microphone_permission_denied": "Mikrofona giriş icazəsi rədd edildi",
    "select_microphone": "Mikrofon Seçin",

    # -- Encryption info ----------------------------------------------------
    "encryption_info": "Şifrələmə Məlumatı",
    "key_management": "Açar İdarəetməsi",
    "key_warning": "Şifrələmə açarınızı itirsəniz, yazmalarınıza daxil ola bilməyəcəksiniz.",
    "key_backup_warning": "Zəhmət olmasa şifrələmə açarınızı etibarlı yerə yedəkləyin.",
    "encryption_algorithm": "Şifrələmə Alqoritmi",
    "key_derived": "Açar törədildi",
    "change_password": "Şifrəni Dəyiş",
    "current_password": "Cari Şifrə",
    "new_password": "Yeni Şifrə",
    "confirm_password": "Şifrəni Təsdiqlə",
    "password_mismatch": "Şifrələr uyğun gəlmir",
    "password_too_short": "Şifrə çox qısadır",

    # -- Status bar ---------------------------------------------------------
    "status_ready": "Hazır",
    "status_recording": "Yazma Aparılır",
    "status_playing": "Oxudulur",
    "status_paused": "Fasilə Edildi",
    "status_error": "Xəta Baş Verdi",
    "status_encrypting": "Şifrələnir",
    "status_decrypting": "Şifrə açılır",
    "status_exporting": "İxrac edilir",
    "status_importing": "İdxal edilir",

    # -- Miscellaneous ------------------------------------------------------
    "loading": "Yüklənir...",
    "processing": "Emal edilir...",
    "unknown_error": "Naməlum xəta baş verdi",
    "disk_space_low": "Disk sahəsi azdır",
    "unsaved_changes": "Saxlanılmamış dəyişikliklər var. Çıxmaq istədiyinizə əminsiniz?",
    "format_hours": "s",
    "format_minutes": "d",
    "format_seconds": "san",
}


# ============================================================================
# Language registry
# ============================================================================

#: Maps language codes to their translation dictionaries.
LANGUAGE_MAP: dict[str, dict[str, str]] = {
    "tr": TRANSLATIONS_TR,
    "en": TRANSLATIONS_EN,
    "az": TRANSLATIONS_AZ,
}

#: Human-readable names for each supported language.
LANGUAGE_NAMES: dict[str, str] = {
    "tr": "Türkçe",
    "en": "English",
    "az": "Azərbaycanca",
}


# ============================================================================
# Localization class
# ============================================================================

class Localization:
    """
    Translation helper that resolves string keys against a loaded language
    dictionary.

    Usage::

        loc = Localization("tr")
        label = loc.tr("start_recording")   # -> "Kaydı Başlat"
        loc.set_language("en")
        label = loc.tr("start_recording")   # -> "Start Recording"
    """

    def __init__(self, language_code: str = "tr") -> None:
        """
        Initialise the localizer.

        Parameters
        ----------
        language_code : str
            One of ``'tr'``, ``'en'``, or ``'az'``.
        """
        self._language_code: str = language_code
        self._translations: dict[str, str] = LANGUAGE_MAP.get(
            language_code, TRANSLATIONS_TR
        )

    # -- public API ---------------------------------------------------------

    @property
    def language_code(self) -> str:
        """Return the currently active language code."""
        return self._language_code

    def set_language(self, language_code: str) -> None:
        """
        Switch to a different language.

        Parameters
        ----------
        language_code : str
            One of ``'tr'``, ``'en'``, or ``'az'``.

        Raises
        ------
        ValueError
            If *language_code* is not a recognised language.
        """
        if language_code not in LANGUAGE_MAP:
            raise ValueError(
                f"Unsupported language: {language_code!r}. "
                f"Choose from {list(LANGUAGE_MAP.keys())}."
            )
        self._language_code = language_code
        self._translations = LANGUAGE_MAP[language_code]

    def tr(self, key: str, *args, **kwargs) -> str:
        """
        Translate *key* in the current language.

        If positional or keyword arguments are supplied the translated
        string is formatted with ``str.format(*args, **kwargs)``.

        Parameters
        ----------
        key : str
            Translation key (e.g. ``"start_recording"``).

        Returns
        -------
        str
            The translated string, or the raw *key* when no translation
            is found (to make missing keys obvious during development).
        """
        text = self._translations.get(key, key)
        if args or kwargs:
            try:
                return text.format(*args, **kwargs)
            except (IndexError, KeyError):
                return text
        return text

    @staticmethod
    def available_languages() -> dict[str, str]:
        """
        Return a mapping of language codes to their display names.

        Returns
        -------
        dict[str, str]
            E.g. ``{"tr": "Türkçe", "en": "English", "az": "Azərbaycanca"}``.
        """
        return dict(LANGUAGE_NAMES)
