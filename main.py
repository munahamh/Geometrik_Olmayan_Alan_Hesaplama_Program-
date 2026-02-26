import sys
# PyQt5 uygulamasını başlatmak için gerekli sınıf
from PyQt5.QtWidgets import QApplication

# Arayüzün tanımlı olduğu gui.py dosyasından
# AreaCalculatorUI sınıfını içe aktarıyoruz
from gui import AreaCalculatorUI


# ==================================================
#           PROGRAMIN BAŞLANGIÇ NOKTASI
# ==================================================
# Bu kontrol, dosyanın doğrudan çalıştırılıp
# çalıştırılmadığını kontrol eder.
# Eğer bu dosya "python main.py" şeklinde
# çalıştırıldıysa aşağıdaki kodlar çalışır.
if __name__ == "__main__":

    # ----------------------------------------------
    # 1) Qt uygulamasını oluştur
    # ----------------------------------------------
    # QApplication:
    # - Pencereleri yönetir
    # - Mouse / klavye olaylarını yakalar
    # - Uygulamanın çalışması için zorunludur
    app = QApplication(sys.argv)

    # ----------------------------------------------
    # 2) Ana pencereyi oluştur
    # ----------------------------------------------
    # AreaCalculatorUI:
    # gui.py dosyasında tanımlanan ana arayüz sınıfıdır
    window = AreaCalculatorUI()

    # ----------------------------------------------
    # 3) Ana pencereyi ekranda göster
    # ----------------------------------------------
    window.show()

    # ----------------------------------------------
    # 4) Olay döngüsünü (Event Loop) başlat
    # ----------------------------------------------
    # app.exec_():
    # - Programın sürekli çalışmasını sağlar
    # - Kullanıcı pencereyi kapatana kadar bekler
    #
    # sys.exit(...):
    # - Program kapatıldığında düzgün bir şekilde çıkış yapar
sys.exit(app.exec_())
