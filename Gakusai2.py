import streamlit as st
import pandas as pd
import os
import io
import re
from PIL import Image, ImageDraw, ImageFont

# ------------------------
# 設定
# ------------------------
LOG_FILE = "tickets_external.csv"
ALL_LOG_FILE = "tickets_external_all.csv"
BASE_IMAGE = "template.png"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ------------------------
# ログ読み込み or 初期化
# ------------------------
def load_log():
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
        if "整理券番号" in df.columns and not df["整理券番号"].isnull().all():
            max_num = pd.to_numeric(df["整理券番号"], errors='coerce').max()
            if pd.isna(max_num):
                next_num = 1
            else:
                next_num = int(max_num) + 1
        else:
            next_num = 1
        return df, next_num
    else:
        df = pd.DataFrame(columns=["整理券番号", "名字"])
        return df, 1

if "next_number" not in st.session_state:
    df, next_number = load_log()
    st.session_state.df = df
    st.session_state.next_number = next_number
else:
    df = st.session_state.df
    next_number = st.session_state.next_number

# ------------------------
# タイトル
# ------------------------
st.title("🎫 学祭アーティストライブ 整理券発行（外部向け）")

# ------------------------
# メンテナンス機能
# ------------------------
st.subheader("🛠 メンテナンス")
with st.expander("📤 ログと整理券番号のメンテナンス"):
    with st.form("maintenance_form"):
        option = st.radio("操作を選んでください", ("何もしない", "ログをリセット", "途中から整理券番号を指定して再開"))
        new_start = st.number_input("再開する整理券番号を入力してください", min_value=1, step=1, value=1, key="restart_number")
        confirm = st.checkbox("本当にこの操作を実行してよろしいですか？")
        maintenance_submit = st.form_submit_button("実行")

    if maintenance_submit:
        if not confirm:
            st.warning("確認にチェックが入っていません")
        else:
            if option == "ログをリセット":
                df = pd.DataFrame(columns=["整理券番号", "名字"])
                df.to_csv(LOG_FILE, index=False)
                st.session_state.df = df
                st.session_state.next_number = 1
                st.success("ログと整理券番号をリセットしました")
            elif option == "途中から整理券番号を指定して再開":
                st.session_state.next_number = new_start
                st.success(f"整理券番号を {new_start} から再開します")

# ------------------------
# 入力フォーム
# ------------------------
st.subheader("🎟 整理券情報入力")

with st.form("ticket_form"):
    name = st.text_input("お名前（名字のみローマ字）")
    submitted = st.form_submit_button("整理券を発行")

if submitted:
    if not re.fullmatch(r"[A-Za-z]+", name):
        st.error("名字はローマ字で入力してください")
    else:
        try:
            # 画像生成
            image = Image.open(BASE_IMAGE).convert("RGB")
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype(FONT_PATH, 36)
            draw.text((50, 60), f"name: {name}", font=font, fill="black")
            draw.text((50, 130), f"number: {next_number}", font=font, fill="black")

            img_buffer = io.BytesIO()
            image.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            # 表示（ここを use_container_width に修正済み）
            st.image(img_buffer, caption=f"整理券番号 {next_number}", use_container_width=True)

            # ログ保存
            new_row = pd.DataFrame([[next_number, name]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(LOG_FILE, index=False)
            # 蓄積ログ
            if os.path.exists(ALL_LOG_FILE):
                df_all = pd.read_csv(ALL_LOG_FILE)
                df_all = pd.concat([df_all, new_row], ignore_index=True)
            else:
                df_all = new_row
            df_all.to_csv(ALL_LOG_FILE, index=False)

            st.session_state.df = df
            st.session_state.next_number += 1

            st.success(f"整理券番号 {next_number} を発行しました🎉")

        except Exception as e:
            st.error(f"発行失敗: {e}")

# ------------------------
# CSV確認・ダウンロード
# ------------------------
st.subheader("📋 整理券ログ")

if st.checkbox("ログを表示する"):
    st.dataframe(df)

if not df.empty:
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding="utf-8")  # ← コンマ区切り
    st.download_button(
        label="📥 整理券ログをダウンロード（CSV）",
        data=csv_buffer.getvalue(),
        file_name="整理券ログ.txt",
        mime="text/csv"
    )

if os.path.exists(ALL_LOG_FILE):
    df_all = pd.read_csv(ALL_LOG_FILE)
    st.subheader("📚 全体ログ（リセットされずに保存され続ける）")
    if st.checkbox("全体ログを表示する"):
        st.dataframe(df_all)
    if not df_all.empty:
        csv_all_buffer = io.StringIO()
        df_all.to_csv(csv_all_buffer, index=False, encoding="utf-8")
        st.download_button(
            label="📥 全体ログをダウンロード（CSV）",
            data=csv_all_buffer.getvalue(),
            file_name="整理券全体ログ.txt",
            mime="text/csv"
        )
