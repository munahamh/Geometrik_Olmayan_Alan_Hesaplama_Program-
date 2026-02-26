import cv2
import numpy as np
import pytesseract
import re

# ==================================================
# OpenCV pencerelerinin boyutlarını kontrol eden
# genel ayarlar
# ==================================================

TARGET_WIDTH = 1400  # OpenCV penceresinde gösterilecek görüntünün genişliği (px)
WIN_W = 600  # OpenCV pencere genişliği
WIN_H = 600  # OpenCV pencere yüksekliği


def open_big_window(win_name, w=WIN_W, h=WIN_H, x=60, y=60):
    """
    OpenCV için büyük ve yeniden boyutlandırılabilir pencere açar.
    - win_name : pencere adı
    - w, h     : pencere boyutları
    - x, y     : ekran üzerindeki konumu
    """
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, w, h)
    try:
        cv2.moveWindow(win_name, x, y)
    except Exception:
        # Bazı sistemlerde moveWindow desteklenmeyebilir
        pass


def show_scaled(window_name, image, target_width=TARGET_WIDTH):
    """
    Görüntüyü oranını bozmadan küçültüp büyüterek gösterir.
    Bu fonksiyon sadece görüntüyü gösterir, scale değeri döndürmez.
    """
    h, w = image.shape[:2]

    # Görüntü genişliği 0 ise direkt göster
    if w == 0:
        cv2.imshow(window_name, image)
        return

    # Yeni ölçek oranı
    scale = target_width / w
    new_h = int(h * scale)

    # Görüntüyü yeniden boyutlandır
    resized_img = cv2.resize(
        image,
        (target_width, new_h),
        interpolation=cv2.INTER_AREA
    )

    # OpenCV penceresinde göster
    cv2.imshow(window_name, resized_img)


def show_scaled_return(window_name, image, target_width=TARGET_WIDTH):
    """
    Görüntüyü oranını bozmadan gösterir ve ayrıca:
    - resized_img : ekranda görünen görüntü
    - scale       : orijinal görüntüye dönüşüm için ölçek
    """
    h, w = image.shape[:2]

    if w == 0:
        cv2.imshow(window_name, image)
        return image, 1.0

    scale = target_width / w
    new_h = int(h * scale)

    resized_img = cv2.resize(
        image,
        (target_width, new_h),
        interpolation=cv2.INTER_AREA
    )

    cv2.imshow(window_name, resized_img)
    return resized_img, scale


def calculate_area_from_image(image_path):
    """
    OTOMATİK MOD

    - En büyük contour → ölçülecek şekil
    - İkinci büyük contour → referans nesne

    Geri dönüş:
    (nesne_alani_px, referans_uzunlugu_px, mesaj)
    """
    try:
        # Görüntüyü dosyadan oku
        img = cv2.imread(image_path)
        if img is None:
            return 0, 0, "Hata: Görüntü okunamadı."

        # Gri tona çevir
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Siyah-beyaz threshold (arka plan / nesne ayırımı)
        _, thresh = cv2.threshold(
            gray, 127, 255, cv2.THRESH_BINARY_INV
        )

        # Threshold sonucunu büyük pencerede göster
        win1 = "1. Bilgisayarin Goorusu (Threshold)"
        open_big_window(win1, x=40, y=40)
        show_scaled(win1, thresh, target_width=TARGET_WIDTH)

        # Beyaz bölgelerin sınırlarını (contour) bul
        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Çok küçük alanlı nesneleri ele
        contours = [c for c in contours if cv2.contourArea(c) > 50]

        # En az iki nesne olmalı (şekil + referans)
        if len(contours) < 2:
            cv2.destroyAllWindows()
            return 0, 0, "Hata: Görüntüde en az 2 nesne olmalı (Şekil + Referans)."

        # Alanlarına göre büyükten küçüğe sırala
        sorted_contours = sorted(
            contours,
            key=cv2.contourArea,
            reverse=True
        )

        # En büyük nesne ölçülecek şekil
        object_contour = sorted_contours[0]
        # İkinci büyük nesne referans
        ref_contour = sorted_contours[1]

        # Şeklin alanını piksel cinsinden hesapla
        object_area_px = float(cv2.contourArea(object_contour))

        # Referans nesnenin uzunluğunu bul
        rect = cv2.minAreaRect(ref_contour)
        (center), (width, height), angle = rect
        ref_length_px = float(max(width, height))

        # Sonuçları görselleştirmek için kopya görüntü
        debug_img = img.copy()

        # Şekli yeşil çiz
        cv2.drawContours(debug_img, [object_contour], -1, (0, 255, 0), 3)

        # Referansı mavi çiz
        cv2.drawContours(debug_img, [ref_contour], -1, (255, 0, 0), 3)

        # Sonucu büyük pencerede göster
        win2 = "2. Tespit Edilen Nesneler (Yesil: Nesne, Mavi: Referans)"
        open_big_window(win2, x=80, y=80)
        show_scaled(win2, debug_img, target_width=TARGET_WIDTH)

        print("Pencereleri kapatmak için klavyeden bir tuşa basın...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        return object_area_px, ref_length_px, "Başarılı (Otomatik)"

    except Exception as e:
        cv2.destroyAllWindows()
        return 0, 0, f"Hata: {str(e)}"


def calculate_area_from_image_manual(image_path, target_width=TARGET_WIDTH):
    """
    MANUEL MOD

    Kullanıcı:
    - İlk tıklama: ölçülecek şekil (yeşil)
    - İkinci tıklama: referans nesne (mavi)

    Kontroller:
    - Enter      : Onay
    - Backspace  : Son seçimi sil
    - ESC        : İptal
    """
    try:
        # Görüntüyü oku
        img = cv2.imread(image_path)
        if img is None:
            return 0, 0, "Hata: Görüntü okunamadı."

        # Gri tona çevir
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Threshold işlemi
        _, thresh = cv2.threshold(
            gray, 127, 255, cv2.THRESH_BINARY_INV
        )

        # Threshold görüntüsünü göster
        win_thr = "1. Threshold"
        open_big_window(win_thr, x=40, y=40)
        show_scaled(win_thr, thresh, target_width=target_width)

        # Contour bul
        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Küçük nesneleri ele
        contours = [c for c in contours if cv2.contourArea(c) > 50]

        if len(contours) < 2:
            cv2.destroyAllWindows()
            return 0, 0, "Hata: En az 2 nesne olmalı (Şekil + Referans)."

        # Manuel seçim penceresi
        win = "2. Elle Secim - 1) Nesne 2) Referans | Enter=OK, ESC=Iptal"
        open_big_window(win, x=80, y=80)

        selected_object = None
        selected_ref = None

        # İlk gösterim ve scale hesaplama
        _, scale = show_scaled_return(
            win,
            img.copy(),
            target_width=target_width
        )

        # Ekranı yeniden çizme fonksiyonu
        def redraw():
            tmp = img.copy()

            # Tüm nesneleri gri çiz
            cv2.drawContours(tmp, contours, -1, (160, 160, 160), 2)

            # Seçilen şekli yeşil çiz
            if selected_object is not None:
                cv2.drawContours(tmp, [selected_object], -1, (0, 255, 0), 4)

            # Seçilen referansı mavi çiz
            if selected_ref is not None:
                cv2.drawContours(tmp, [selected_ref], -1, (255, 0, 0), 4)

            show_scaled_return(win, tmp, target_width=target_width)

        # Tıklanan noktaya ait contour'u bul
        def pick_contour_at(x_orig, y_orig):
            for c in contours:
                if cv2.pointPolygonTest(
                        c,
                        (float(x_orig), float(y_orig)),
                        False
                ) >= 0:
                    return c
            return None

        # Mouse tıklama olayı
        def mouse_cb(event, x, y, flags, param):
            nonlocal selected_object, selected_ref

            if event == cv2.EVENT_LBUTTONDOWN:
                # Ekran koordinatlarını orijinale çevir
                x_orig = int(x / scale)
                y_orig = int(y / scale)

                c = pick_contour_at(x_orig, y_orig)
                if c is None:
                    return

                # İlk seçim: şekil
                if selected_object is None:
                    selected_object = c
                # İkinci seçim: referans
                elif selected_ref is None:
                    if c is selected_object:
                        return
                    selected_ref = c
                # Üçüncü seçim: referansı değiştir
                else:
                    if c is not selected_object:
                        selected_ref = c

                redraw()

        cv2.setMouseCallback(win, mouse_cb)
        redraw()

        # Klavye kontrolleri
        while True:
            key = cv2.waitKey(0) & 0xFF

            # ESC → iptal
            if key == 27:
                cv2.destroyAllWindows()
                return 0, 0, "İptal edildi."

            # Backspace / Delete → geri al
            if key in [8, 127]:
                if selected_ref is not None:
                    selected_ref = None
                elif selected_object is not None:
                    selected_object = None
                redraw()

            # Enter → hesapla
            if key in [13, 10]:
                if selected_object is None or selected_ref is None:
                    continue

                # Alan ve referans uzunluğu hesapla
                object_area_px = float(
                    cv2.contourArea(selected_object)
                )

                rect = cv2.minAreaRect(selected_ref)
                (center), (width, height), angle = rect
                ref_length_px = float(max(width, height))

                cv2.destroyAllWindows()
                return object_area_px, ref_length_px, "Başarılı (Elle Seçim)"

    except Exception as e:
        cv2.destroyAllWindows()
        return 0, 0, f"Hata: {str(e)}"


# 3.mod referans uzunlugunu algiliyor
def calculate_area_from_image_full_auto(image_path):
    try:
        # Görüntüyü dosyadan oku
        img = cv2.imread(image_path)
        if img is None:
            return 0, 0, "Hata: Görüntü okunamadı."

        # Gri tona çevir
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Siyah-beyaz threshold (arka plan / nesne ayırımı)
        _, thresh = cv2.threshold(
            gray, 127, 255, cv2.THRESH_BINARY_INV
        )

        # Threshold sonucunu büyük pencerede göster
        win1 = "1. Bilgisayarin Goorusu (Threshold)"
        open_big_window(win1, x=40, y=40)
        show_scaled(win1, thresh, target_width=TARGET_WIDTH)

        # Beyaz bölgelerin sınırlarını (contour) bul
        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Çok küçük alanlı nesneleri ele
        contours = [c for c in contours if cv2.contourArea(c) > 50]

        # En az iki nesne olmalı (şekil + referans)
        if len(contours) < 2:
            cv2.destroyAllWindows()
            return 0, 0, "Hata: Görüntüde en az 2 nesne olmalı (Şekil + Referans)."

        # Alanlarına göre büyükten küçüğe sırala
        sorted_contours = sorted(
            contours,
            key=cv2.contourArea,
            reverse=True
        )

        # En büyük nesne ölçülecek şekil
        object_contour = sorted_contours[0]
        # İkinci büyük nesne referans
        ref_contour = sorted_contours[1]

        # Şeklin alanını piksel cinsinden hesapla
        object_area_px = float(cv2.contourArea(object_contour))

        # Referans nesnenin uzunluğunu bul
        rect = cv2.minAreaRect(ref_contour)
        (center), (width, height), angle = rect
        ref_length_px = float(max(width, height))

        # Sonuçları görselleştirmek için kopya görüntü
        debug_img = img.copy()

        # Şekli yeşil çiz
        cv2.drawContours(debug_img, [object_contour], -1, (0, 255, 0), 3)

        # Referansı mavi çiz
        cv2.drawContours(debug_img, [ref_contour], -1, (255, 0, 0), 3)

        # Sonucu büyük pencerede göster
        win2 = "2. Tespit Edilen Nesneler (Yesil: Nesne, Mavi: Referans)"
        open_big_window(win2, x=80, y=80)
        show_scaled(win2, debug_img, target_width=TARGET_WIDTH)

        print("Pencereleri kapatmak için klavyeden bir tuşa basın...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        return object_area_px, ref_length_px, 36.0, "Başarılı (Otomatik)"

    except Exception as e:
        cv2.destroyAllWindows()
        return 0, 0, f"Hata: {str(e)}"

