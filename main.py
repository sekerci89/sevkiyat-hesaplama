import streamlit as st
import pandas as pd

# Sayfa Ayarları
st.set_page_config(page_title="Milkrun Tır Yükleme Hesaplayıcı", page_icon="🚛", layout="centered")

st.title("🚛 Tır Yükleme & Kapasite Hesaplayıcı")

# --- DORSE / TIR TİPİ SEÇİMİ ---
st.subheader("🚛 Tır/Dorse Tipini Seçin")

tir_secimi = st.selectbox(
    "Gelen Tırın Tipi:",
    (
        "Standart Tır (13.60m x 2.45m x 2.70m) - 90 m³",
        "Mega Tır (13.60m x 2.48m x 3.00m) - 100 m³",
        "Tilt Trailer (Özel Ölçü) - 86 m³"
    )
)

# Seçilen tır tipine göre kapasite ve uzunluk
if "90 m³" in tir_secimi:
    TIR_KAPASITE_M3 = 90.0
    TIR_UZUNLUK_CM = 1360.0  # 13.60 metre
elif "100 m³" in tir_secimi:
    TIR_KAPASITE_M3 = 100.0
    TIR_UZUNLUK_CM = 1360.0
else:
    TIR_KAPASITE_M3 = 86.0
    TIR_UZUNLUK_CM = 1360.0

st.info(f"Aktif Tır Kapasitesi: **{TIR_KAPASITE_M3} m³** | Tır Uzunluğu: **{TIR_UZUNLUK_CM / 100:.2f} Metre**")
st.divider()

# --- EXCEL READ ---
try:
    df = pd.read_excel("kasalar.xlsx")
except Exception as e:
    st.error("⚠️ 'kasalar.xlsx' dosyası bulunamadı! Lütfen dosyanın proje klasöründe olduğundan emin olun.")
    st.stop()

st.subheader("📦 Yüklenecek Kasaları Seçin")

toplam_hacim = 0.0
secilen_kasa_sayisi = 0

# Excel tablosundaki verileri işleme
for index, row in df.iterrows():
    kasa_kodu = str(row['kasa_kodu'])
    en = row['en']
    boy = row['boy']
    yukseklik = row['yukseklik']

    # cm3 -> m3 çevrimi
    tekil_hacim_m3 = (en * boy * yukseklik) / 1000000

    col1, col2 = st.columns([2, 1])
    with col1:
        secildi = st.checkbox(f"**{kasa_kodu}** ({en}x{boy}x{yukseklik} cm)")
    with col2:
        if secildi:
            adet = st.number_input(f"Adet", min_value=1, value=1, step=1, key=f"kasa_{index}")
            toplam_hacim += tekil_hacim_m3 * adet
            secilen_kasa_sayisi += adet

st.divider()

# --- SONUÇ EKRANI ---
st.subheader("📊 Sevkiyat Özet & Kapasite Durumu")

st.write(f"**Seçilen Toplam Kasa Adeti:** {secilen_kasa_sayisi} adet")
st.write(f"**Toplam Yüklenen Hacim:** {toplam_hacim:.2f} m³ / {TIR_KAPASITE_M3:.2f} m³")

if secilen_kasa_sayisi == 0:
    st.info("💡 Lütfen listeden sevkiyata eklenecek kasaları ve adetlerini girin.")
elif toplam_hacim <= TIR_KAPASITE_M3:
    kalan_bos_hacim = TIR_KAPASITE_M3 - toplam_hacim
    doluluk_yuzdesi = (toplam_hacim / TIR_KAPASITE_M3) * 100

    # Hacim doluluk oranına göre kalan net boş uzunluk hesabı
    kullanilan_uzunluk_cm = TIR_UZUNLUK_CM * (toplam_hacim / TIR_KAPASITE_M3)
    kalan_uzunluk_cm = TIR_UZUNLUK_CM - kullanilan_uzunluk_cm

    st.success(f"✅ **TIR YÜKLEMESİ UYGUN!** (Doluluk: %{doluluk_yuzdesi:.1f})")
    st.write(f"📦 Kalan Boş Hacim: **{kalan_bos_hacim:.2f} m³**")
    st.write(
        f"📏 **Tırın Arkasında Kalan Boş Mesafe:** ~ **{kalan_uzunluk_cm:.0f} cm** ({kalan_uzunluk_cm / 100:.2f} Metre)")
else:
    fazlalik = toplam_hacim - TIR_KAPASITE_M3
    doluluk_yuzdesi = (toplam_hacim / TIR_KAPASITE_M3) * 100
    st.error(f"⚠️ **KAPASİTE AŞILDI!** (Doluluk: %{doluluk_yuzdesi:.1f})")
    st.write(f"Seçilen kasalar tırın toplam alanını **{fazlalik:.2f} m³** aşıyor! Lütfen kasa sayılarını azaltın.")