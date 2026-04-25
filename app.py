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
# @st.cache_data をつけることで、毎回読み込まず高速に動作します
@st.cache_data
def load_data():
    try:
        # data.csv を読み込む
        return pd.read_csv("data.csv")
    except FileNotFoundError:
        return None

df = load_data()

if df is None:
    st.error("エラー: `data.csv` が見つかりません。GitHub上にファイルが存在するか確認してください。")
    st.stop()

# --- Step 1: シンドローム選択 ---
st.subheader("1. 感染フォーカスの選択")

# CSVの 'syndrome' 列から選択肢のリストを自動作成
syndrome_options = ["選択してください"] + df['syndrome'].tolist()
selected_syndrome = st.selectbox("症状・疑われる疾患を選択してください", syndrome_options)

if selected_syndrome != "選択してください":
    # 選択された疾患の行のデータを抽出
    row_data = df[df['syndrome'] == selected_syndrome].iloc[0]
    
    # --- Step 2: 結果の出力 ---
    st.subheader("2. 推奨エンピリック治療")
    
    with st.container():
        st.markdown("**🎯 想定される起炎菌**")
        st.write(row_data['pathogens'])
        
        st.markdown("**💊 推奨第一選択薬**")
        # CSV内で "/" で区切られている複数の薬を改行して表示する処理
        regimens = str(row_data['primary_regimen']).split('/')
        for reg in regimens:
            st.success(reg.strip())
            
        with st.expander("📚 クリニカル・パール / ロジックの根拠", expanded=False):
            st.write(row_data['rationale'])
