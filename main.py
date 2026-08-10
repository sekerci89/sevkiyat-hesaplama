import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Tır Sevkiyat Hesabı", layout="wide")

st.title("🚛 Tır / Dorse Sevkiyat ve Taban Alanı Hesaplama")

# 1. Excel Dosyasını Yükleme / Okuma
@st.cache_data
def load_data():
    # Excel dosya adınız
    df = pd.read_excel("kasalar1.xlsx")
    return df

try:
    df_urunler = load_data()
except Exception as e:
    st.error(f"Excel dosyası okunamadı. Lütfen dosya adını ve yolunu kontrol edin: {e}")
    st.stop()

# 2. Araç / Dorse Tipi Seçimi
st.sidebar.header("🚛 Araç Tipi Seçimi")
arac_tipleri = {
    "Standart Tır (13.60m x 2.40m)": {"en": 2.40, "boy": 13.60},
    "Mega Tır (13.60m x 2.48m)": {"en": 2.48, "boy": 13.60},
    "Kırkayak Kamyon (8.20m x 2.45m)": {"en": 2.45, "boy": 8.20},
    "Onteker Kamyon (7.20m x 2.45m)": {"en": 2.45, "boy": 7.20}
}

secilen_arac_adi = st.sidebar.selectbox("Lütfen Yükleme Yapılacak Aracı Seçin:", list(arac_tipleri.keys()))
secilen_arac = arac_tipleri[secilen_arac_adi]

TIR_EN_M = secilen_arac["en"]
TIR_BOY_M = secilen_arac["boy"]
TIR_TABAN_ALANI_M2 = TIR_EN_M * TIR_BOY_M

st.sidebar.write("---")
st.sidebar.header("📦 Ürün Seçimi ve Adetler")

secilen_urunler = []

# Excel'deki ürünleri listeden seçme ve adet girme
for idx, row in df_urunler.iterrows():
    kasa_kodu = row.get('kasa_kodu', f"Kasa {idx+1}")
    en_cm = row.get('en', 0)
    boy_cm = row.get('boy', 0)
    max_kat = row.get('max_kat', 1)
    
    if pd.isna(max_kat) or max_kat <= 0:
        max_kat = 1

    adet = st.sidebar.number_input(
        f"{kasa_kodu} ({en_cm}x{boy_cm} cm | Max: {int(max_kat)})", 
        min_value=0, 
        value=0, 
        step=1, 
        key=f"input_{idx}"
    )
    
    if adet > 0:
        secilen_urunler.append({
            "kasa_kodu": kasa_kodu,
            "en": en_cm,
            "boy": boy_cm,
            "max_kat": int(max_kat),
            "Adet": adet
        })

# 3. Hesaplama Motoru (Ortak İstifleme Mantığı)
if secilen_urunler:
    df_secilen = pd.DataFrame(secilen_urunler)
    
    # Boyutları (En, Boy) ve Max Kat değerleri AYNI olan kasaları grupluyoruz
    gruplanmis = df_secilen.groupby(['en', 'boy', 'max_kat'])
    
    toplam_gerekli_taban_m2 = 0.0
    grup_ozet_liste = []

    for (en_cm, boy_cm, max_kat), grup in gruplanmis:
        toplam_grup_adedi = grup['Adet'].sum()
        kasa_kodlari = ", ".join(grup['kasa_kodu'].tolist())
        
        en_m = en_cm / 100.0
        boy_m = boy_cm / 100.0
        
        # 1 Kasanın tabanda kapladığı m²
        kasa_taban_m2 = en_m * boy_m
        
        # Aynı boyuttaki kasalar kendi içinde birleştirilerek üst üste diziliyor
        taban_kasa_adedi = math.ceil(toplam_grup_adedi / max_kat)
        
        # Grubun toplam taban alanı
        grup_taban_m2 = taban_kasa_adedi * kasa_taban_m2
        toplam_gerekli_taban_m2 += grup_taban_m2

        grup_ozet_liste.append({
            "Kasa Grubu / Kodları": kasa_kodlari,
            "Ölçü (En x Boy cm)": f"{en_cm} x {boy_cm}",
            "Max Kat": max_kat,
            "Toplam Adet": toplam_grup_adedi,
            "Tabanda Kapladığı Yeri (Adet)": taban_kasa_adedi,
            "Kapladığı Taban Alanı (m²)": round(grup_taban_m2, 2)
        })

    doluluk_yuzdesi = (toplam_gerekli_taban_m2 / TIR_TABAN_ALANI_M2) * 100
    kalan_taban_m2 = max(0.0, TIR_TABAN_ALANI_M2 - toplam_gerekli_taban_m2)
    
    # 📏 Tırın arkasında kalan boylamasına boşluk hesabı (Metre ve CM cinsinden)
    kalan_boy_metre = kalan_taban_m2 / TIR_EN_M
    kalan_boy_cm = round(kalan_boy_metre * 100)

    # 4. Sonuçları Ekrana Yazdırma
    st.subheader(f"📊 Sevkiyat Doluluk Özet Raporu ({secilen_arac_adi})")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Araç Doluluk Oranı", f"%{round(doluluk_yuzdesi, 1)}")
    col2.metric("Kullanılan Taban Alanı", f"{round(toplam_gerekli_taban_m2, 2)} m²")
    col3.metric("Kalan Taban Alanı", f"{round(kalan_taban_m2, 2)} m²")
    col4.metric("Kalan Boylamasına Boşluk", f"{kalan_boy_cm} cm", f"{round(kalan_boy_metre, 2)} m")

    if doluluk_yuzdesi > 100:
        st.error(f"⚠️ DİKKAT: Seçilen yükler {secilen_arac_adi} taban alanını %{round(doluluk_yuzdesi - 100, 1)} oranında aşıyor!")
    else:
        st.success(f"✅ Seçilen ürünler sığıyor. Tır kapısında arkada kalan net boşluk: **{kalan_boy_cm} cm** ({round(kalan_boy_metre, 2)} metre)")

    st.write("---")
    st.subheader("📋 Gruplandırılmış İstifleme Detay Listesi")
    st.caption("Not: Aynı taban ölçüsüne ve istif katına sahip kasalar tekli parçaları birbirinin üstüne gelecek şekilde hesaplanmıştır.")
    st.dataframe(pd.DataFrame(grup_ozet_liste), use_container_width=True)

else:
    st.info("Hesaplama yapabilmek için lütfen soldaki panelden araç tipini seçip ürün adedi giriniz.")
