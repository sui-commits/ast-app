import streamlit as st
import pandas as pd

# --- ページ設定 (スマホ最適化) ---
st.set_page_config(page_title="Empiric Tx Guide", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .reportview-container .main .block-container{ padding-top: 2rem; }
    div[data-testid="stExpander"] { border-left: 4px solid #4CAF50; }
</style>
""", unsafe_allow_html=True)

st.title("🦠 Empiric Tx Guide (CSV版)")
st.caption("※CSVファイルからデータを読み込んで表示するバージョンです。")

# --- データの読み込み ---
@st.cache_data
def load_data():
    try:
        # ★改良点: 文字コードのゆらぎを吸収し、列名の前後の空白を自動で削除する
        df = pd.read_csv("data.csv", encoding="utf-8-sig", skipinitialspace=True)
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        return None

df = load_data()

if df is None:
    st.error("エラー: `data.csv` が見つかりません。")
    st.stop()

# ★改良点: 万が一見出しが見つからない場合、何が読み込まれているか画面に表示する
if 'syndrome' not in df.columns:
    st.error(f"エラー: CSVの中に 'syndrome' という見出しが見つかりません。")
    st.info(f"プログラムが認識した現在の見出しは以下の通りです: {list(df.columns)}")
    st.stop()

# --- Step 1: シンドローム選択 ---
st.subheader("1. 感染フォーカスの選択")

syndrome_options = ["選択してください"] + df['syndrome'].tolist()
selected_syndrome = st.selectbox("症状・疑われる疾患を選択してください", syndrome_options)

if selected_syndrome != "選択してください":
    row_data = df[df['syndrome'] == selected_syndrome].iloc[0]
    
    # --- Step 2: 結果の出力 ---
    st.subheader("2. 推奨エンピリック治療")
    
    with st.container():
        st.markdown("**🎯 想定される起炎菌**")
        st.write(row_data['pathogens'])
        
        st.markdown("**💊 推奨第一選択薬**")
        regimens = str(row_data['primary_regimen']).split('/')
        for reg in regimens:
            st.success(reg.strip())
            
        with st.expander("📚 クリニカル・パール / ロジックの根拠", expanded=False):
            st.write(row_data['rationale'])
