import streamlit as st
import pandas as pd
from prompts.prompt_builder import get_education_prompt

# ページ設定
st.set_page_config(page_title="Expert AST Guide", layout="centered")

# --- 初期状態のセット ---
if "syndrome" not in st.session_state:
    st.session_state.syndrome = "未選択"

# --- UIデザインの修正 ---
st.markdown("""
<style>
    /* メイン画面の余白 */
    .main .block-container { padding-bottom: 120px; }
    
    /* 画面下部にピッカーボタンを固定 */
    div[data-testid="stPopover"] {
        position: fixed;
        bottom: 20px; left: 5%; width: 90%; z-index: 9999;
    }
    
    /* 擬似テキストフィールド（ポップオーバーのボタン）のデザイン */
    div[data-testid="stPopover"] > button {
        background-color: #e3f2fd; /* 👈 背景を薄い青色に設定 */
        color: #333;
        width: 100%;
        border-radius: 12px;
        border: 1px solid #90caf9;
        padding: 15px;
        font-size: 16px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        display: flex;
        justify-content: flex-start;
    }
    
    /* ポップオーバーの中身（ピッカー部分）のデザイン */
    div[data-testid="stPopoverBody"] {
        background-color: #f8f9fa; /* 👈 ピッカー内の背景色 */
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(filename):
    try:
        df = pd.read_csv(filename, encoding="utf-8-sig", skipinitialspace=True)
        df.columns = df.columns.str.strip()
        df.fillna("", inplace=True)
        return df
    except:
        return None

df = load_data("data.csv")
risk_df = load_data("risks.csv")
risk_help = dict(zip(risk_df['risk_id'], risk_df['description'])) if risk_df is not None else {}

syndrome_list = ["未選択"] + df['syndrome'].unique().tolist()

# --- コンボボックス風ピッカーUI ---
# ポップオーバーのボタン名に現在選択されているフォーカスを表示
with st.popover(f"📌 感染フォーカス: {st.session_state.syndrome}"):
    # ピッカーの中身（キーボードが出ないラジオボタンを使用）
    selected = st.radio(
        "感染フォーカスを選択", 
        syndrome_list, 
        index=syndrome_list.index(st.session_state.syndrome),
        label_visibility="collapsed" # ラベルを隠してすっきり見せる
    )
    
    # 選択が変更されたら画面をリロードして反映
    if selected != st.session_state.syndrome:
        st.session_state.syndrome = selected
        st.rerun()

# --- 以降のロジックは st.session_state.syndrome を使用 ---
if st.session_state.syndrome != "未選択":
    st.subheader(f"📍 ターゲット: {st.session_state.syndrome}")
    st.caption("該当する患者リスクをオンにしてください")
    
    c1, c2 = st.columns(2)
    with c1:
        risk_mrsa = st.toggle("MRSAリスク", help=risk_help.get('risk_mrsa'))
        risk_pseudo = st.toggle("緑膿菌リスク", help=risk_help.get('risk_pseudo'))
        allergy_pcg = st.toggle("PCGアレルギー", help=risk_help.get('allergy_pcg'))
    with c2:
        risk_esbl = st.toggle("ESBLリスク", help=risk_help.get('risk_esbl'))
        risk_lis = st.toggle("リステリアリスク", help=risk_help.get('risk_lis'))
        is_shock = st.toggle("ショック状態", help=risk_help.get('is_shock'))

    # ... (この下のルール判定・結果表示・プロンプト生成は前回と同じです。syndromeの部分だけst.session_state.syndromeになります) ...
