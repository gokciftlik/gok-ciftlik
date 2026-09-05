import streamlit as st
import pandas as pd
import numpy as np
import base64
import glob
from datetime import datetime, timedelta, time
import time as time_lib

st.set_page_config(page_title="Gök Besi Çiftliği - Akıllı Otomasyon", layout="wide", page_icon="🐂")

# --- OTOMATİK SAYFA YENİLEME (CANLI SAYAÇ VE SENSÖRLER İÇİN) ---
# Sayfanın canlı akması için 10 saniyede bir otomatik güncellenmesini sağlar
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# Oturum ve Durum Yönetimi
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "aktif_sekme" not in st.session_state: st.session_state.aktif_sekme = "📊 Sürü Özeti & Hedef Kilo"
if "secili_kupe" not in st.session_state: st.session_state.secili_kupe = None

# Bildirim ve Otomasyon Durumları
if "bildirim_yem" not in st.session_state: st.session_state.bildirim_yem = True
if "bildirim_fan" not in st.session_state: st.session_state.bildirim_fan = True
if "bildirim_ates" not in st.session_state: st.session_state.bildirim_ates = True
if "bildirim_kilo" not in st.session_state: st.session_state.bildirim_kilo = True

if "fan_states" not in st.session_state:
    st.session_state.fan_states = {"Fan 1 (Doğu)": True, "Fan 2 (Orta)": False, "Fan 3 (Batı)": True}
if "cati_states" not in st.session_state:
    st.session_state.cati_states = {"Çatı Pencereleri Sol": True, "Çatı Pencereleri Sağ": True}

# CSS Tasarımı
def apply_custom_style(blur=False):
    bg_files = glob.glob("arka_plan*")
    bg_css = ""
    if bg_files:
        with open(bg_files[0], "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        overlay = "rgba(15, 23, 42, 0.82)" if blur else "rgba(15, 23, 42, 0.40)"
        blur_val = "8px" if blur else "0px"
        bg_css = f"""
        .stApp {{
            background: linear-gradient({overlay}, {overlay}), url("data:image/jpeg;base64,{encoded_string}");
            background-size: cover; background-position: center; background-attachment: fixed;
            backdrop-filter: blur({blur_val}); transition: all 0.5s ease;
        }}
        """

    st.markdown(f"""
        <style>
        {bg_css}
        div[data-testid="stMetric"], .stDataFrame, div[data-testid="stForm"] {{
            background: rgba(15, 23, 42, 0.82) !important;
            border: 1px solid rgba(217, 119, 6, 0.4) !important;
            border-radius: 12px !important; backdrop-filter: blur(10px);
        }}
        section[data-testid="stSidebar"] {{
            background-color: rgba(15, 23, 42, 0.94) !important;
            border-right: 2px solid #d97706;
        }}
        .yem-box {{
            background: rgba(217, 119, 6, 0.25); border: 2px solid #f59e0b;
            padding: 10px; border-radius: 10px; text-align: center; color: white; margin-bottom: 8px;
        }}
        .sensor-box {{
            background: rgba(15, 23, 42, 0.75); border: 1px solid #d97706;
            padding: 10px; border-radius: 10px; text-align: center; color: white;
        }}
        </style>
    """, unsafe_allow_html=True)

# GİRİŞ EKRANI
if not st.session_state.logged_in:
    apply_custom_style(blur=False)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br><h2 style='text-align:center; color:#f59e0b;'>GÖK BESİ ÇİFTLİĞİ</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            email = st.text_input("E-Posta")
            password = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş Yap", use_container_width=True):
                if email == "admin@gokciftlik.com" and password == "123456":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Hatalı Giriş!")
    st.stop()

# VERİ HAZIRLIĞI
bugun = datetime.now()
if "tartimlar" not in st.session_state:
    st.session_state.tartimlar = [
        {"Kupe": "TR33001", "Cins": "Angus", "Tarih": bugun - timedelta(days=30), "Kilo": 390.0, "Sicaklik": 38.6},
        {"Kupe": "TR33001", "Cins": "Angus", "Tarih": bugun, "Kilo": 425.0, "Sicaklik": 38.5},
        {"Kupe": "TR33002", "Cins": "Simmental", "Tarih": bugun - timedelta(days=30), "Kilo": 410.0, "Sicaklik": 38.5},
        {"Kupe": "TR33002", "Cins": "Simmental", "Tarih": bugun, "Kilo": 480.0, "Sicaklik": 39.8},
        {"Kupe": "TR33004", "Cins": "Angus", "Tarih": bugun - timedelta(days=30), "Kilo": 350.0, "Sicaklik": 350.0},
        {"Kupe": "TR33004", "Cins": "Angus", "Tarih": bugun, "Kilo": 356.0, "Sicaklik": 38.4},
    ]

df_tartim = pd.DataFrame(st.session_state.tartimlar)
df_tartim["Tarih"] = pd.to_datetime(df_tartim["Tarih"])
son_tartimlar = df_tartim.sort_values("Tarih").groupby("Kupe").last().reset_index()

apply_custom_style(blur=(st.session_state.aktif_sekme != "📊 Sürü Özeti & Hedef Kilo"))

# SENSÖR VE İKLİM VERİLERİ (Tarsus / Sarıveli)
ahir_temp = 31.8  # °C
ahir_nem = 68     # %

# ÜST HEADER & SAĞ KÖŞE İKLİM / SAYAÇ PANELİ
top_col1, top_col2 = st.columns([2.8, 1.2])

with top_col1:
    st.title("🐂 GÖK BESİ ÇİFTLİĞİ")
    st.caption("Tarsus / Sarıveli Canlı Otomasyon ve Sürü Takip Paneli")

with top_col2:
    # 1. Yemleme Saati Canlı Sayacı (07:00 & 19:00)
    now = datetime.now()
    t_sabah = datetime.combine(now.date(), time(7, 0))
    t_aksam = datetime.combine(now.date(), time(19, 0))
    
    if now < t_sabah: hedef_yem = t_sabah; etiket = "Sabah Yemlemesi"
    elif now < t_aksam: hedef_yem = t_aksam; etiket = "Akşam Yemlemesi"
    else: hedef_yem = t_sabah + timedelta(days=1); etiket = "Sabah Yemlemesi"
    
    kalan_sn = int((hedef_yem - now).total_seconds())
    saat, dk, sn = kalan_sn // 3600, (kalan_sn % 3600) // 60, kalan_sn % 60
    
    st.markdown(f"""
        <div class="yem-box">
            <small>⏰ {etiket} (07:00 / 19:00)</small><br>
            <span style="font-size:18px; font-weight:bold; color:#f87171;">{saat} Saat {dk} Dk {sn} Sn</span>
        </div>
    """, unsafe_allow_html=True)

    # 2. Yemleme Sayacının Altındaki Canlı İklim Sensörleri
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.markdown(f"""
            <div class="sensor-box">
                <small>🌡️ Sıcaklık</small><br>
                <b style="font-size:16px; color:#f59e0b;">{ahir_temp} °C</b>
            </div>
        """, unsafe_allow_html=True)
    with s_col2:
        st.markdown(f"""
            <div class="sensor-box">
                <small>💧 Bağıl Nem</small><br>
                <b style="font-size:16px; color:#38bdf8;">%{ahir_nem}</b>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ACİL UYARI BANNERLARI
atesli = son_tartimlar[son_tartimlar["Sicaklik"] >= 39.5]
duran_fanlar = [k for k, v in st.session_state.fan_states.items() if not v]

if st.session_state.bildirim_ates and not atesli.empty:
    for _, row in atesli.iterrows():
        st.error(f"🚨 **KRİTİK UYARI:** {row['Kupe']} küpeli {row['Cins']} yüksek ateşe sahip ({row['Sicaklik']}°C)!")

if st.session_state.bildirim_fan and duran_fanlar:
    st.warning(f"⚠️ **FAN ARIZASI:** {', '.join(duran_fanlar)} KAPALI veya DURDU!")

# NAVİGASYON
st.sidebar.title("Gök Besi Menü")
menu_secim = st.sidebar.radio(
    "Navigasyon",
    ["📊 Sürü Özeti & Hedef Kilo", "🌀 İklim & Otomasyon Butonları", "📈 Ağırlık Artış Analizi", "⚙️ Bildirim & Uyarı Ayarları"],
    index=["📊 Sürü Özeti & Hedef Kilo", "🌀 İklim & Otomasyon Butonları", "📈 Ağırlık Artış Analizi", "⚙️ Bildirim & Uyarı Ayarları"].index(st.session_state.aktif_sekme)
)
st.session_state.aktif_sekme = menu_secim

if st.sidebar.button("🚪 Çıkış Yap"):
    st.session_state.logged_in = False
    st.rerun()

# İÇERİK SEKMELERİ
if st.session_state.aktif_sekme == "📊 Sürü Özeti & Hedef Kilo":
    st.subheader("📋 Sürü Durumu")
    st.dataframe(son_tartimlar, use_container_width=True)

elif st.session_state.aktif_sekme == "🌀 İklim & Otomasyon Butonları":
    st.subheader("⚙️ Manuel Otomasyon Kontrol Paneli")
    st.markdown("### 🌀 Helikopter Fan Manuel Kontrolleri")
    f_cols = st.columns(3)
    for i, (fan_adı, durum) in enumerate(st.session_state.fan_states.items()):
        with f_cols[i]:
            st.write(f"**{fan_adı}**")
            st.write("Durum: " + ("🟢 ÇALIŞIYOR" if durum else "🔴 DURDU / KAPALI"))
            if st.button("KAPAT 🛑" if durum else "AÇ ▶️", key=f"fan_btn_{i}", use_container_width=True):
                st.session_state.fan_states[fan_adı] = not durum
                st.rerun()

elif st.session_state.aktif_sekme == "📈 Ağırlık Artış Analizi":
    st.subheader("📈 Tartım ve Ağırlık Artış Analizi")
    chart_df = df_tartim.pivot(index="Tarih", columns="Kupe", values="Kilo")
    st.line_chart(chart_df, use_container_width=True)

elif st.session_state.aktif_sekme == "⚙️ Bildirim & Uyarı Ayarları":
    st.subheader("🔔 Uyarım ve Bildirim Tercihleri")
    st.session_state.bildirim_yem = st.toggle("⏰ Yemleme Saati Uyarıları", value=st.session_state.bildirim_yem)
    st.session_state.bildirim_fan = st.toggle("🌀 Fan Durma Bildirimleri", value=st.session_state.bildirim_fan)
    st.session_state.bildirim_ates = st.toggle("🌡️ Ateş Alarmları", value=st.session_state.bildirim_ates)

# CANLI YENİLEME TETİKLEYİCİSİ (Her 5 saniyede bir ekranı arkada günceller)
time_lib.sleep(5)
st.rerun()