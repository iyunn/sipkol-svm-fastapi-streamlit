# -*- coding: utf-8 -*-
"""
Breast Cancer Prediction - Streamlit Frontend
Backend: FastAPI (deployed on Vercel) - TIDAK DIUBAH.
Perubahan pada file ini hanya di sisi UI/UX. Endpoint, request/response
contract, dan urutan nilai fitur yang dikirim ke API tetap identik
dengan versi asli.
"""

import streamlit as st
import requests

# ============================================================
# KONFIGURASI HALAMAN (native Streamlit, tidak ada HTML/CSS)
# ============================================================
st.set_page_config(
    page_title="Breast Cancer Prediction",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# KONSTANTA — TIDAK MENGUBAH LOGIC, HANYA LABEL TAMPILAN
# ============================================================
# Endpoint & kontrak API asli — TIDAK DIUBAH
API_URL = "https://sipkol-svm-fastapi-streamlit-kvlz.vercel.app/predict"

# Mapping label hasil prediksi (backend tetap kirim 0/1, UI tidak
# pernah menampilkan angka mentah ke user).
PREDICTION_LABELS = {
    0: {"label": "Malignant", "emoji": "🔴", "desc": "Sel terindikasi bersifat ganas (kanker)."},
    1: {"label": "Benign", "emoji": "🟢", "desc": "Sel terindikasi bersifat jinak (bukan kanker)."},
}

# Nama tampilan untuk 30 fitur, mengikuti konvensi standar dataset
# Wisconsin Breast Cancer (mean / standard error / worst).
# CATATAN: Ini hanya LABEL VISUAL. Urutan nilai yang dikirim ke API
# tetap index 0-29 apa adanya, sama seperti kode asli — jika urutan
# training model berbeda, cukup sesuaikan daftar nama ini saja.
BASE_MEASUREMENTS = [
    "Radius", "Texture", "Perimeter", "Area", "Smoothness",
    "Compactness", "Concavity", "Concave Points", "Symmetry", "Fractal Dimension",
]
FEATURE_GROUPS = {
    "Mean": [f"{m} (Mean)" for m in BASE_MEASUREMENTS],
    "Standard Error": [f"{m} (SE)" for m in BASE_MEASUREMENTS],
    "Worst": [f"{m} (Worst)" for m in BASE_MEASUREMENTS],
}
GROUP_ORDER = ["Mean", "Standard Error", "Worst"]  # menentukan urutan index 0-29

# ============================================================
# SIDEBAR — INFO APLIKASI
# ============================================================
with st.sidebar:
    st.markdown("### 🩺 Tentang Aplikasi")
    st.write(
        "Aplikasi ini memprediksi apakah sel tumor bersifat "
        "**Malignant (ganas)** atau **Benign (jinak)** berdasarkan "
        "30 hasil pengukuran citra sel, menggunakan model **SVM**."
    )
    st.divider()
    st.caption("**Model:** Support Vector Machine (SVM)")
    st.caption("**Input:** 30 fitur numerik (mean, SE, worst)")
    st.divider()
    st.info(
        "⚠️ Aplikasi ini dibuat untuk tujuan edukasi/demonstrasi. "
        "Bukan pengganti diagnosis medis profesional.",
        icon="⚠️",
    )

# ============================================================
# HERO SECTION
# ============================================================
st.title("🩺 Breast Cancer Prediction")
st.caption("Prediksi malignansi tumor berdasarkan pengukuran citra sel — didukung model Machine Learning (SVM)")
st.divider()

# ============================================================
# INPUT SECTION — dikelompokkan sesuai struktur data asli
# ============================================================
st.subheader("📋 Input Data Pengukuran")
st.write("Masukkan 30 nilai hasil pengukuran citra sel, dikelompokkan menjadi 3 kategori berikut:")

# Dict untuk menampung nilai input per fitur, urutan akhir disusun
# ulang sesuai GROUP_ORDER sebelum dikirim ke API.
input_values = {}

tabs = st.tabs([f"📊 {g}" for g in GROUP_ORDER])

for tab, group_name in zip(tabs, GROUP_ORDER):
    with tab:
        labels = FEATURE_GROUPS[group_name]
        col1, col2 = st.columns(2)
        for idx, label in enumerate(labels):
            target_col = col1 if idx < 5 else col2
            with target_col:
                input_values[(group_name, idx)] = st.number_input(
                    label,
                    value=0.0,
                    format="%.4f",
                    key=f"{group_name}_{idx}",
                )

st.divider()

# ============================================================
# SUSUN ULANG INPUT KE LIST SESUAI URUTAN ASLI (index 0-29)
# Logic pengiriman TIDAK DIUBAH — hanya cara input dikumpulkan.
# ============================================================
inputs = []
for group_name in GROUP_ORDER:
    for idx in range(len(BASE_MEASUREMENTS)):
        inputs.append(input_values[(group_name, idx)])

# ============================================================
# PREDICT BUTTON & LOGIC — TIDAK MENGUBAH REQUEST/RESPONSE CONTRACT
# ============================================================
predict_col = st.columns([1, 1, 1])[1]
with predict_col:
    predict_clicked = st.button("🔍 Predict", use_container_width=True, type="primary")

if predict_clicked:
    with st.spinner("Menganalisis data..."):
        try:
            response = requests.post(
                API_URL,
                json={"features": inputs},
                timeout=15,
            )
            response.raise_for_status()
            hasil = response.json()

            prediction = hasil["prediction"]
            probability = hasil["probability"]

            info = PREDICTION_LABELS.get(prediction)

            st.divider()
            st.subheader("📄 Hasil Prediksi")

            with st.container(border=True):
                if info is None:
                    # Fallback jika backend mengirim nilai di luar 0/1
                    st.warning(f"Nilai prediksi tidak dikenali: {prediction}")
                else:
                    res_col1, res_col2 = st.columns([1, 1])
                    with res_col1:
                        st.metric("Prediksi", f"{info['emoji']} {info['label']} (raw: {prediction})")
                        st.caption(info["desc"])
                    with res_col2:
                        st.metric("Confidence", f"{probability:.2%}")
                        st.progress(min(max(probability, 0.0), 1.0))

            if info and info["label"] == "Benign":
                st.success("✅ Hasil analisis selesai.")
            elif info and info["label"] == "Malignant":
                st.warning("⚠️ Hasil menunjukkan indikasi ganas. Disarankan konsultasi lebih lanjut.")

        except requests.exceptions.Timeout:
            st.error("⏱️ Request timeout. Server tidak merespons, coba lagi beberapa saat.")
        except requests.exceptions.ConnectionError:
            st.error("🔌 Gagal terhubung ke server prediksi. Periksa koneksi internet Anda.")
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ Server mengembalikan error: {e}")
        except (KeyError, ValueError):
            st.error("⚠️ Format response dari server tidak sesuai yang diharapkan.")
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan tak terduga: {e}")

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("Breast Cancer Prediction App · Powered by SVM & FastAPI · Modified by G.231.21.0165 - Fillian Adriansyah Utomo")
