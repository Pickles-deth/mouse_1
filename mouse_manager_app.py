import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pandas as pd
import io, os, zipfile
from PIL import Image

st.set_page_config(page_title="マウス耳写真管理", layout="wide")
st.title("🐭 マウス耳写真管理アプリ")

# Google Sheets接続（個人認証だけでOK）
conn = st.connection("gsheets", type=GSheetsConnection)

# データを読み込み（存在しない場合は空データ作成）
df = conn.read(worksheet="Sheet1", ttl=5)
if df.empty:
    df = pd.DataFrame(columns=["mouse_id", "remark", "date_added"])

# --- 新規登録 ---
st.subheader("🧬 新規マウス登録")
new_mouse = st.text_input("マウス番号", placeholder="例: 001")
remark = st.text_input("備考", placeholder="例: 系統・特徴など")

if st.button("登録"):
    if new_mouse and new_mouse not in df["mouse_id"].values:
        new_row = pd.DataFrame({
            "mouse_id": [new_mouse],
            "remark": [remark],
            "date_added": [datetime.now().strftime("%Y-%m-%d")]
        })
        df = pd.concat([df, new_row], ignore_index=True)
        conn.update(worksheet="Sheet1", data=df)
        st.success(f"マウス {new_mouse} を登録しました！")
        st.experimental_rerun()
    elif new_mouse in df["mouse_id"].values:
        st.warning("すでに登録済みです。")

# --- 削除 ---
delete_mouse = st.selectbox("削除するマウスを選択", [""] + list(df["mouse_id"]))
if st.button("削除"):
    if delete_mouse:
        df = df[df["mouse_id"] != delete_mouse]
        conn.update(worksheet="Sheet1", data=df)
        st.warning(f"マウス {delete_mouse} を削除しました。")
        st.experimental_rerun()

st.divider()

# --- 一覧と写真アップロード ---
st.subheader("📋 登録済みマウス一覧")

if df.empty:
    st.info("まだ登録されていません。")
else:
    today = datetime.now().strftime("%Y-%m-%d")
    base_dir = "mice_data"
    os.makedirs(base_dir, exist_ok=True)
    today_dir = os.path.join(base_dir, today)
    os.makedirs(today_dir, exist_ok=True)

    for _, row in df.iterrows():
        mid = row["mouse_id"]
        with st.expander(f"🐭 マウス {mid}"):
            st.write(f"📅 登録日: {row['date_added']}")
            st.write(f"📝 備考: {row['remark']}")

            mdir = os.path.join(today_dir, mid)
            os.makedirs(mdir, exist_ok=True)
            colL, colR = st.columns(2)

            for side, col in zip(["左", "右"], [colL, colR]):
                with col:
                    up = st.file_uploader(f"{side}耳", type=["jpg","jpeg","png"], key=f"{mid}_{side}")
                    if up:
                        path = os.path.join(mdir, f"{mid}_{side}.jpg")
                        img = Image.open(up)
                        img.save(path)
                        st.image(img, caption=f"{mid}_{side}.jpg", use_container_width=True)
                        st.success(f"{side}耳を保存しました！")

            left = os.path.join(mdir, f"{mid}_左.jpg")
            right = os.path.join(mdir, f"{mid}_右.jpg")
            if os.path.exists(left) and os.path.exists(right):
                st.success("✅ 両耳そろいました！")

st.divider()

# --- ZIPダウンロード ---
st.subheader("📦 本日分をまとめてダウンロード")

if os.path.exists(today_dir) and os.listdir(today_dir):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(today_dir):
            for f in files:
                path = os.path.join(root, f)
                zf.write(path, os.path.relpath(path, today_dir))
    buffer.seek(0)
    st.download_button("📥 今日のZIPをダウンロード", buffer, file_name=f"mice_{today}.zip")
else:
    st.info("今日の写真データはまだありません。")
