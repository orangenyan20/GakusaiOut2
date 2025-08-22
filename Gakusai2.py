import streamlit as st
import pandas as pd
import os
import io
import re
from PIL import Image, ImageDraw, ImageFont

# ------------------------
# 設定
# ------------------------
BASE_IMAGE = "template.png"  # 背景画像
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LOG_FILE = "external_tickets.csv"

# ------------------------
# ログ読み込み or 初期化
# ------------------------
def load_log():
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
        max_num = pd.to_numeric(df["整理券番号"], errors='coerce').max()
        next_num = int(max_num) + 1 if not pd.isna(max_num) else 1
        return df, next_num
    else:
        df = pd.DataFrame(columns=["整理券番号", "名前(ローマ字)"])
        return df, 1

if "ext_next_number" not in st.session_state:
    df, next_number = load_log()
    st.session_state.ext_df = df
    st.session_state.ext_next_number = next_number
else:
    df = st.session_state.ext_df
    next_number = st.session_state.ext_next_number

# ------------------------
# UI
# ------------------------
st.title("🎫 学祭 整理券発行（外部向け）")

st.markdown("整理券を発行すると画面に表示されます。スマホで撮影して保管してください📸")

with st.form("external_ticket_form"):
    name_romaji = st.text_input("名字（ローマ字）を入力してください（例：Yamada）")
    submitted = st.form_submit_button("整理券を発行する")

if submitted:
    if not re.fullmatch(r"[A-Za-z]+", name_romaji.strip()):
        st.error("ローマ字は英字のみで入力してください（例：Tanaka）")
    else:
        try:
            # 画像生成
            image = Image.open(BASE_IMAGE).convert("RGB")
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype(FONT_PATH, 40)
            draw.text((50, 60), f"No. {next_number}", font=font, fill="black")
            draw.text((50, 130), f"Name: {name_romaji}", font=font, fill="black")

            img_buffer = io.BytesIO()
            image.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            # 表示
            st.image(img_buffer, caption="この画像を保存またはスクリーンショットしてください📷", use_column_width=True)

            # ログ保存
            new_row = pd.DataFrame([[next_number, name_romaji]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(LOG_FILE, index=False)

            st.session_state.ext_df = df
            st.session_state.ext_next_number += 1

            st.success(f"整理券 No.{next_number} を発行しました！")

        except Exception as e:
            st.error(f"画像生成に失敗しました: {e}")

# ------------------------
# 管理用メンテナンス機能
# ------------------------
st.subheader("🛠 メンテナンス（管理者用）")
with st.expander("整理券番号・ログ管理"):
    # ログリセット
    with st.form("reset_form"):
        reset_confirm = st.checkbox("本当にログをリセットしてよろしいですか？")
        reset_button = st.form_submit_button("ログをリセットする")
        if reset_button:
            if reset_confirm:
                df = pd.DataFrame(columns=["整理券番号", "名前(ローマ字)"])
                df.to_csv(LOG_FILE, index=False)
                st.session_state.ext_df = df
                st.session_state.ext_next_number = 1
                st.success("ログをリセットしました。番号は 1 から再開します。")
            else:
                st.warning("確認チェックが必要です。")

    # 番号指定再開
    with st.form("restart_form"):
        restart_num = st.number_input("再開する整理券番号を入力してください", min_value=1, step=1, value=1)
        restart_button = st.form_submit_button("番号を指定して再開する")
        if restart_button:
            st.session_state.ext_next_number = restart_num
            st.success(f"整理券番号を {restart_num} から再開します")

# ------------------------
# 管理用ログ確認
# ------------------------
with st.expander("📋 発行済みログ（管理者用）"):
    if not df.empty:
        st.dataframe(df)

        txt_buffer = io.BytesIO()
        df.to_csv(txt_buffer, sep='\t', index=False, encoding="utf-8")
        txt_buffer.seek(0)
        st.download_button(
            label="📥 整理券ログをダウンロード（タブ区切り）",
            data=txt_buffer,
            file_name="外部整理券ログ.txt",
            mime="text/plain"
        )
    else:
        st.info("まだ整理券は発行されていません。")
