import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Tır Sevkiyat Hesabı", layout="wide")

st.title("🚛 Tır Sevkiyat ve Taban Alanı Hesaplama")

# 1. Excel Dosyasını Yükleme / Okuma
@st.cache_data
def load_data():
    # Excel dosya adınızı buraya yazın (Örn: 'urunler.xlsx')
    df = pd.read_excel("urunler.xlsx")
    return df

try:
    df_urunler = load_data()
except Exception as e:
    st.error(f"Excel dosyası okunamadı. Lütfen dosya adını ve yolunu kontrol edin: {e}")
    st.stop()

# 2. Tır Ölçüleri (Standart Tır: 13.60 m x 2.40 m)
TIR_EN_M = 2.40
TIR_BOY_M = 13.60
TIR_TABAN_ALANI_M2 = TIR_EN_M * TIR_BOY_M  # 32.64 m²

st.sidebar.header("📦 Ürün Seçimi ve Adetler")

secilen_urunler = []

# Excel'deki ürünleri listeden seçme ve adet girme
for idx, row in df_urunler.iterrows():
    urun_kodu = row.get('Ürün Kodu', f"Ürün {idx+1}")
    en_cm = row.get('En (cm)', 0)
    boy_cm = row.get('Boy (cm)', 0)
    max_kat = row.get('Max Kat', 1)
    
    # Varsayılan Max Kat kontrolü (Eğer boşsa veya 0 ise 1 kabul et)
    if pd.isna(max_kat) or max_kat <= 0:
        max_kat = 1

    adet = st.sidebar.number_input(
        f"{urun_kodu} (Max Kat: {max_kat})", 
        min_value=0, 
        value=0, 
        step=1, 
        key=f"input_{idx}"
    )
    
    if adet > 0:
        secilen_urunler.append({
            "Ürün Kodu": urun_kodu,
            "En (cm)": en_cm,
            "Boy (cm)": boy_cm,
            "Max Kat": int(max_kat),
            "Adet": adet
        })

# 3. Hesaplama Motoru
if secilen_urunler:
    df_secilen = pd.DataFrame(secilen_urunler)
    
    toplam_gerekli_taban_m2 = 0.0
    ozet_liste = []

    for _, row in df_secilen.iterrows():
        en_m = row["En (cm)"] / 100.0
        boy_m = row["Boy (cm)"] / 100.0
        max_kat = row["Max Kat"]
        adet = row["Adet"]
        
        # 1 Kasanın tabanda kapladığı m²
        kasa_taban_m2 = en_m * boy_m
        
        # İstif katına göre tır tabanında kaplanan kasa yeri sayısı
        # Örn: 16 adet kasa, Max Kat 2 ise -> Tabanda 8 kasa yeri gerekir
        taban_kasa_adedi = math.ceil(adet / max_kat)
        
        # Bu ürünün kapladığı toplam taban alanı
        urun_toplam_taban_m2 = taban_kasa_adedi * kasa_taban_m2
        toplam_gerekli_taban_m2 += urun_toplam_taban_m2

        ozet_liste.append({
            "Ürün Kodu": row["Ürün Kodu"],
            "Toplam Adet": adet,
            "Max Kat": max_kat,
            "Tabanda Kapladığı Kasa Yeri": taban_kasa_adedi,
            "Kapladığı Taban Alanı (m²)": round(urun_toplam_taban_m2, 2)
        })

    doluluk_yuzdesi = (toplam_gerekli_taban_m2 / TIR_TABAN_ALANI_M2) * 100
    kalan_taban_m2 = TIR_TABAN_ALANI_M2 - toplam_gerekli_taban_m2

    # 4. Sonuçları Ekrana Yazdırma
    st.subheader("📊 Sevkiyat Doluluk Özet Raporu")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Tır Doluluk Oranı", f"%{round(doluluk_yuzdesi, 1)}")
    col2.metric("Kullanılan Taban Alanı", f"{round(toplam_gerekli_taban_m2, 2)} m²")
    col3.metric("Kalan Taban Alanı", f"{round(max(0.0, kalan_taban_m2), 2)} m²")

    if doluluk_yuzdesi > 100:
        st.error(f"⚠️ DİKKAT: Yüklenen malzemeler tır taban alanını %{round(doluluk_yuzdesi - 100, 1)} oranında aşıyor! İkinci bir tır veya düzenleme gerekli.")
    else:
        st.success("✅ Seçilen ürünler tırın taban alanına sığıyor.")

    st.write("---")
    st.subheader("📋 Ürün Bazlı Detay Listesi")
    st.dataframe(pd.DataFrame(ozet_liste), use_container_width=True)

else:
    st.info("Hesaplama yapabilmek için lütfen soldaki panelden en az bir ürün adedi giriniz.")
