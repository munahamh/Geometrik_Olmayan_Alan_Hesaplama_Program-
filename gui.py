import sys
# PyQt5 arayüzünde kullanılacak temel bileşenler
from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QLabel, QVBoxLayout,
    QWidget, QFileDialog, QMessageBox, QGroupBox,
    QLineEdit, QHBoxLayout, QRadioButton
)
# Hizalama ve sabitler
from PyQt5.QtCore import Qt
# Yazı tipi, resim ve giriş doğrulama araçları
from PyQt5.QtGui import QFont, QPixmap, QDoubleValidator

# Görüntü işleme ve alan hesaplama fonksiyonları
from logic import calculate_area_from_image, calculate_area_from_image_manual, calculate_area_from_image_full_auto


# ==================================================
#           ANA UYGULAMA SINIFI
# ==================================================
class AreaCalculatorUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # ----------------------------------------------
        # 1) Ana pencere ayarları
        # ----------------------------------------------
        self.setWindowTitle("Alan Hesaplama Sistemi")  # Pencere başlığı
        self.setGeometry(100, 100, 750, 750)  # Pencere konumu ve boyutu

        # Uygulamada kullanılacak varsayılan font
        app_font = QFont("Tahoma", 11)
        self.setFont(app_font)

        # ----------------------------------------------
        # 2) Arayüz tasarımı (Qt StyleSheet)
        # ----------------------------------------------
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f7fb; }
            QLabel { font-size: 14px; color: #111827; font-weight: 500; }
            QLabel#TitleLabel { font-size: 22px; font-weight: bold; color: #1a73e8; margin-bottom: 10px; }
            QLabel#ResultLabel {
                font-size: 18px; font-weight: bold; color: #047857;
                background-color: #d1fae5; border: 1px solid #10b981;
                border-radius: 8px; padding: 10px;
            }
            QPushButton {
                background-color: #2563eb; color: #ffffff; border: none;
                border-radius: 8px; padding: 12px 24px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #9ca3af; color: #e5e7eb; }
            QLineEdit {
                border: 1px solid #d1d5db; border-radius: 6px; padding: 8px; background-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold; border: 1px solid #d0d7e2; border-radius: 8px;
                margin-top: 10px; padding: 15px; background-color: #ffffff;
            }
        """)

        # ----------------------------------------------
        # Central Widget (ana içerik alanı)
        # ----------------------------------------------
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Yüklenen görüntünün dosya yolu
        self.current_image_path = None

        # Arayüz elemanlarını oluştur
        self.setup_ui()

    # ==================================================
    #           ARAYÜZ OLUŞTURMA
    # ==================================================
    def setup_ui(self):
        # Ana dikey yerleşim
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # ----------------------------------------------
        # Başlık etiketi
        # ----------------------------------------------
        title = QLabel("Görüntüden Şekil Alanı Hesaplama")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ----------------------------------------------
        # Görüntü gösterim alanı
        # ----------------------------------------------
        self.label_image = QLabel("Lütfen görüntüyü yükleyin\n(Şekil + Referans Nesne)")
        self.label_image.setAlignment(Qt.AlignCenter)
        self.label_image.setStyleSheet(
            "border: 2px dashed #9ca3af; background: #e5e7eb; color: #4b5563; font-size: 14px;"
        )
        self.label_image.setFixedSize(690, 400)
        self.label_image.setScaledContents(True)
        layout.addWidget(self.label_image, alignment=Qt.AlignCenter)

        # ----------------------------------------------
        # Hesaplama yöntemi seçimi
        # ----------------------------------------------
        method_group = QGroupBox("Seçim Yöntemi")
        method_layout = QHBoxLayout()

        # Otomatik: En büyük contour = nesne
        self.rb_auto = QRadioButton("Yarı Otomatik (En büyük = nesne)")
        # Manuel: Kullanıcı mouse ile seçer
        self.rb_manual = QRadioButton("Manuel (Elle seç)")
        # referans nesneyi algilayip hesaplayan mod
        self.rb_auto2 = QRadioButton("Tam Otomatik (referans algılama)")

        self.rb_auto.setChecked(True)

        method_layout.addWidget(self.rb_auto)
        method_layout.addWidget(self.rb_manual)
        method_layout.addWidget(self.rb_auto2)

        method_group.setLayout(method_layout)
        layout.addWidget(method_group)

        # ----------------------------------------------
        # Referans nesne uzunluğu (cm)
        # ----------------------------------------------
        calib_group = QGroupBox("Referans Nesne Bilgisi")
        calib_layout = QHBoxLayout()

        lbl_info = QLabel("Yanına koyduğunuz nesnenin uzunluğu (cm):")
        self.input_ref_size = QLineEdit()
        self.input_ref_size.setPlaceholderText("Örn: 14.5 (Kalem) veya 2.5 (Para)")
        self.input_ref_size.setValidator(QDoubleValidator())  # Sadece sayı

        calib_layout.addWidget(lbl_info)
        calib_layout.addWidget(self.input_ref_size)
        calib_group.setLayout(calib_layout)
        layout.addWidget(calib_group)

        # RadioButton sinyalleri baglma
        self.rb_auto2.toggled.connect(self.update_calib_input_state)
        self.rb_auto.toggled.connect(self.update_calib_input_state)
        self.rb_manual.toggled.connect(self.update_calib_input_state)

        # ----------------------------------------------
        # Butonlar
        # ----------------------------------------------
        btns_layout = QHBoxLayout()

        self.btn_load = QPushButton("📂 Görüntü Yükle")
        self.btn_load.clicked.connect(self.load_image)

        self.btn_calc = QPushButton("📐 Alanı Hesapla")
        self.btn_calc.clicked.connect(self.run_calculation)
        self.btn_calc.setEnabled(False)

        btns_layout.addWidget(self.btn_load)
        btns_layout.addWidget(self.btn_calc)
        layout.addLayout(btns_layout)

        # ----------------------------------------------
        # Sonuç etiketi
        # ----------------------------------------------
        self.lbl_result = QLabel("Sonuç: —")
        self.lbl_result.setObjectName("ResultLabel")
        self.lbl_result.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_result)

        self.central_widget.setLayout(layout)
        self.update_calib_input_state()
        # ==================================================
        #   REFERANS GİRİŞ AKTİF / PASİF KONTROLÜ
        # ==================================================

    def update_calib_input_state(self):
        if self.rb_auto2.isChecked():  # TAM OTOMATİK MOD
            self.input_ref_size.setEnabled(False)
            self.input_ref_size.clear()
            self.input_ref_size.setPlaceholderText("Otomatik modda gerekmez")
        else:
            self.input_ref_size.setEnabled(True)
            self.input_ref_size.setPlaceholderText(
                "Örn: 14.5 (Kalem) veya 2.5 (Para)"
            )

    # ==================================================
    #           GÖRÜNTÜ YÜKLEME
    # ==================================================
    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Görüntü Seç", "", "Images (*.png *.jpg *.jpeg)"
        )

        if path:
            self.current_image_path = path
            self.label_image.setPixmap(QPixmap(path))
            self.btn_calc.setEnabled(True)
            self.lbl_result.setText("Görüntü yüklendi. Referans uzunluğunu girin.")

    # ==================================================
    #           ALAN HESAPLAMA
    # ==================================================
    def run_calculation(self):
        if not self.current_image_path:
            QMessageBox.warning(self, "Uyarı", "Görüntü yüklenmedi!")
            return

        self.btn_calc.setEnabled(False)

        try:
            # ================= TAM OTOMATIK =================
            if self.rb_auto2.isChecked():
                obj_area_px, ref_len_px, real_ref_cm, msg = \
                    calculate_area_from_image_full_auto(self.current_image_path)

            # ================= MANUEL =================
            elif self.rb_manual.isChecked():
                real_ref_cm = self.get_ref_cm_from_input()
                if real_ref_cm is None:
                    return

                obj_area_px, ref_len_px, msg = \
                    calculate_area_from_image_manual(self.current_image_path)

            # ================= YARI OTOMATIK =================
            else:
                real_ref_cm = self.get_ref_cm_from_input()
                if real_ref_cm is None:
                    return

                obj_area_px, ref_len_px, msg = \
                    calculate_area_from_image(self.current_image_path)

            # ================= HESAP =================
            if obj_area_px == 0 or ref_len_px == 0:
                self.lbl_result.setText(f"❌ {msg}")
                return

            px_per_cm = ref_len_px / real_ref_cm
            real_area = obj_area_px / (px_per_cm ** 2)

            self.lbl_result.setText(
                f"✅ Gerçek Alan: {real_area:.2f} cm²\n{msg}"
            )

        finally:
            self.btn_calc.setEnabled(True)



