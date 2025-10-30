import streamlit as st
import pandas as pd
import requests
import os
import zipfile
from datetime import datetime
from PIL import Image

# ==================================
# 設定
# ==================================
st.set_page_config(page_title="🐭 マウス耳写真管理", layout="wide")
st.title("🐭 マウス耳写真管理アプリ")

# あなたの Google Apps Script Web API URL をここに貼る
API_URL = "https://script.google.com/macros/s/AKfycbxs2EzizXVeNJdERRlABROJR8NPBnDVtuPMJXKVZyu5UUw4mbPQHyYXAW_efhSjFLym/exec"

# Google Sheetsを読み取り（CSV経由）
SHEET_ID = "1m90P_Xfvtu8JJmUjQyNOylQ68Uvf151gjhzYxknjoW4"
SHEET_NAME = "Sheet1"
GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# ==================================
# データ読み込み
# ==================================
@st.cache_data(ttl=30)
def load_data():
    try:
        df = pd.read_csv(GSHEET_URL)
    except Exception:
        df = pd.DataFrame(columns=["mouse_id", "remark", "left_photo", "right_photo", "date"])
    return df

df = load_data()

# ==================================
# データ送信用関数
# ==================================
def save_to_gsheet(row):
    try:
        res = requests.post(API_URL, json=row)
        if res.status_code == 200:
            st.success("Google Sheetsに保存しました！")
        else:
            st.warning(f"保存失敗: {res.status_code}")
    except Exception as e:
        st.error(f"通信エラー: {e}")

# ==================================
# マウス登録
# ==================================
st.subheader("🧬 新しいマウスを登録")

with st.form("register_form"):
    new_id = st.text_input("マウス番号（例: M001）")
    remark = st.text_input("備考（任意）")
    submitted = st.form_submit_button("登録")

    if submitted and new_id:
        new_row = {
            "mouse_id": new_id,
            "remark": remark,
            "left_photo": "",
            "right_photo": "",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        save_to_gsheet(new_row)
        st.success(f"マウス {new_id} を登録しました！")
    elif submitted:
        st.warning("マウス番号を入力してください。")

# ==================================
# 写真アップロード
# ==================================
st.subheader("📸 マウス写真アップロード")

today_folder = os.path.join("uploads", datetime.now().strftime("%Y%m%d"))
os.makedirs(today_folder, exist_ok=True)

if len(df) == 0:
    st.info("まだマウスが登録されていません。")
else:
    for i, row in df.iterrows():
        with st.expander(f"🐁 {row['mouse_id']} - {row['remark']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("左耳写真")
                left_photo = st.file_uploader(f"{row['mouse_id']}_left", type=["jpg", "png"], key=f"left_{i}")
                if left_photo:
                    left_path = os.path.join(today_folder, f"{row['mouse_id']}_left.jpg")
                    Image.open(left_photo).save(left_path)
                    st.image(left_path, width=200)
            with col2:
                st.write("右耳写真")
                right_photo = st.file_uploader(f"{row['mouse_id']}_right", type=["jpg", "png"], key=f"right_{i}")
                if right_photo:
                    right_path = os.path.join(today_folder, f"{row['mouse_id']}_right.jpg")
                    Image.open(right_photo).save(right_path)
                    st.image(right_path, width=200)

# ==================================
# ZIPダウンロード
# ==================================
st.subheader("📦 今日の写真をまとめてダウンロード")

zip_filename = f"mouse_photos_{datetime.now().strftime('%Y%m%d')}.zip"
zip_path = os.path.join(today_folder, zip_filename)

if st.button("ZIPを作成"):
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in os.listdir(today_folder):
            if file.endswith((".jpg", ".png")):
                zipf.write(os.path.join(today_folder, file), file)
    with open(zip_path, "rb") as f:
        st.download_button("📥 ZIPをダウンロード", data=f, file_name=zip_filename, mime="application/zip")

st.markdown("---")
st.caption("© 2025 Mouse Manager | Streamlit + Google Sheets + GAS")
