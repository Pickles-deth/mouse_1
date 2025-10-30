import streamlit as st
import pandas as pd
import os
import zipfile
from datetime import datetime
from PIL import Image
from io import BytesIO

# --------------------------
# 基本設定
# --------------------------
st.set_page_config(page_title="🐭 マウス耳写真管理アプリ", layout="wide")
st.title("🐭 マウス耳写真管理アプリ")

# Google Sheets 設定（CSV読み取りのみ）
SHEET_ID = "1m90P_Xfvtu8JJmUjQyNOylQ68Uvf151gjhzYxknjoW4"  # あなたのシートID
SHEET_NAME = "Sheet1"
GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# --------------------------
# Google Sheets 読み込み
# --------------------------
@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(GSHEET_URL)
    except Exception as e:
        st.warning(f"Google Sheetsを読み込めませんでした。空データを使用します。({e})")
        df = pd.DataFrame(columns=["mouse_id", "remark", "left_photo", "right_photo", "date"])
    return df

df = load_data()

# --------------------------
# データ保存用ディレクトリ
# --------------------------
os.makedirs("uploads", exist_ok=True)
today_folder = os.path.join("uploads", datetime.now().strftime("%Y%m%d"))
os.makedirs(today_folder, exist_ok=True)

# --------------------------
# マウス登録フォーム
# --------------------------
st.subheader("🧬 新しいマウスを登録")
with st.form("register_form"):
    new_id = st.text_input("マウス番号（例: M001）")
    remark = st.text_input("備考（任意）")
    submitted = st.form_submit_button("登録")

    if submitted and new_id:
        new_row = {"mouse_id": new_id, "remark": remark, "left_photo": "", "right_photo": "", "date": datetime.now().strftime("%Y-%m-%d")}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        st.success(f"マウス {new_id} を登録しました！")
    elif submitted:
        st.warning("マウス番号を入力してください。")

# --------------------------
# マウス一覧と写真アップロード
# --------------------------
st.subheader("📸 マウス写真アップロード")

if len(df) == 0:
    st.info("まだ登録されたマウスがありません。上で新規登録してください。")
else:
    for i, row in df.iterrows():
        with st.expander(f"🐁 {row['mouse_id']} - {row['remark']}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write("左耳写真")
                left_photo = st.file_uploader(f"{row['mouse_id']} 左耳", type=["jpg", "jpeg", "png"], key=f"left_{i}")
                if left_photo:
                    left_path = os.path.join(today_folder, f"{row['mouse_id']}_left.jpg")
                    Image.open(left_photo).save(left_path)
                    df.at[i, "left_photo"] = left_path
                    st.image(left_path, width=200)

            with col2:
                st.write("右耳写真")
                right_photo = st.file_uploader(f"{row['mouse_id']} 右耳", type=["jpg", "jpeg", "png"], key=f"right_{i}")
                if right_photo:
                    right_path = os.path.join(today_folder, f"{row['mouse_id']}_right.jpg")
                    Image.open(right_photo).save(right_path)
                    df.at[i, "right_photo"] = right_path
                    st.image(right_path, width=200)

# --------------------------
# ZIPダウンロード機能
# --------------------------
st.subheader("📦 今日のデータをまとめてダウンロード")

zip_filename = f"mouse_photos_{datetime.now().strftime('%Y%m%d')}.zip"
zip_path = os.path.join(today_folder, zip_filename)

if st.button("ZIPファイルを作成"):
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in os.listdir(today_folder):
            if file.endswith((".jpg", ".jpeg", ".png")):
                zipf.write(os.path.join(today_folder, file), file)
    st.success("ZIPファイルを作成しました！")

    with open(zip_path, "rb") as f:
        st.download_button(
            label="📥 ZIPをダウンロード",
            data=f,
            file_name=zip_filename,
            mime="application/zip"
        )

# --------------------------
# フッター
# --------------------------
st.markdown("---")
st.caption("© 2025 Mouse Manager | Streamlit + Google Sheets")
