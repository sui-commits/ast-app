import streamlit as st
import pandas as pd
from prompts.prompt_builder import get_education_prompt

# ページ設定
st.set_page_config(page_title="Expert AST Guide", layout="centered")

# --- UIデザイン: スマホ向けの安全なCSS ---
st.markdown("""
<style>
    .main .block-container { padding-bottom: 80px; }
    
    /* ラジオボタンを「横スクロールのボタン風」にして押しやすくする */
    div[data-testid="stRadio"] > div {
        flex-direction: row;
        overflow-x: auto;
        flex-wrap: nowrap;
        padding-bottom: 10px;
    }
    /* ボタンの見た目 */
    div[data-testid="stRadio"] label {
        white-space: nowrap;
        background-color: #e3f2fd; /* 薄い青色 */
        padding: 10px 15px;
        border-radius: 8px;
        margin-right: 5px;
        border: 1px solid #90caf9;
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

if df is None:
    st.error("⚠️ data.csv が読み込めません。")
    st.stop()

syndrome_list = ["未選択"] + df['syndrome'].unique().tolist()

# --- メイン画面 ---
st.title("Expert AST Guide")

# キーボードが出ない横並びのボタン（st.radio）
syndrome = st.radio("📌 感染フォーカスを選択", syndrome_list, horizontal=True)

if syndrome != "未選択":
    st.subheader("⚠️ 患者リスク層別化")
    st.caption("該当する項目をオンにしてください")
    
    c1, c2 = st.columns(2)
    with c1:
        risk_mrsa = st.toggle("MRSAリスク", help=risk_help.get('risk_mrsa'))
        risk_pseudo = st.toggle("緑膿菌リスク", help=risk_help.get('risk_pseudo'))
        allergy_pcg = st.toggle("PCGアレルギー", help=risk_help.get('allergy_pcg'))
    with c2:
        risk_esbl = st.toggle("ESBLリスク", help=risk_help.get('risk_esbl'))
        risk_lis = st.toggle("リステリアリスク", help=risk_help.get('risk_lis'))
        is_shock = st.toggle("ショック状態", help=risk_help.get('is_shock'))

    # --- ルールエンジン ---
    active_triggers = ['base']
    active_risk_names = []
    
    if allergy_pcg: 
        active_triggers.append('allergy_pcg')
        active_risk_names.append("ペニシリンアレルギーあり")
    if risk_mrsa: 
        active_triggers.append('risk_mrsa')
        active_risk_names.append("MRSAリスクあり")
    if risk_pseudo: 
        active_triggers.append('risk_pseudo')
        active_risk_names.append("緑膿菌・グラム陰性菌リスクあり")
    if risk_esbl: 
        active_triggers.append('risk_esbl')
        active_risk_names.append("ESBL産生菌リスクあり")
    if risk_lis: 
        active_triggers.append('risk_lis')
        active_risk_names.append("リステリアリスクあり")
    if is_shock: 
        active_triggers.append('is_shock')
        active_risk_names.append("敗血症性ショック")

    rules = df[df['syndrome'] == syndrome]
    final_pathogens = []
    final_regimens = []
    rationales = []

    for _, row in rules.iterrows():
        trigger = str(row['trigger']).strip()
        if trigger in active_triggers:
            action = str(row['action']).strip()
            val = str(row['value']).strip()
            rat = str(row['rationale']).strip()

            if rat:
                rationales.append(f"• {rat}")

            if action == 'add_pathogen':
                final_pathogens.append(val)
            elif action == 'set_regimen' or action == 'override_regimen':
                final_regimens = [val]
            elif action == 'add_regimen':
                if val not in final_regimens:
                    final_regimens.append(val)

    # --- 結果表示 ---
    st.divider()
    with st.container(border=True):
        st.subheader("💊 推奨エンピリック治療")
        
        st.markdown("**🎯 想定起炎菌:**")
        pathogen_display = " , ".join(final_pathogens) if final_pathogens else "データなし"
        st.info(pathogen_display)

        st.markdown("**💉 推奨レジメン:**")
        if final_regimens:
            for r in final_regimens:
                # 【重要】スラッシュではなく、カンマ(,)で薬剤を分けるロジックに変更！
                for split_r in r.split(','):
                    if split_r.strip():
                        st.success(split_r.strip())
        else:
            st.warning("該当するレジメンデータがありません")

        with st.expander("📖 ロジックの実行軌跡 (Rationale)"):
            if rationales:
                for msg in rationales:
                    st.markdown(msg)
            else:
                st.markdown("実行軌跡はありません。")

    # --- AIプロンプト生成 ---
    st.divider()
    st.subheader("🎓 新人教育用：AI解説プロンプト")
    st.caption("コピーしてGemini等に貼り付けてください")
    
    risk_text = "特になし" if not active_risk_names else "、".join(active_risk_names)
    regimen_text = " または ".join(final_regimens) if final_regimens else "不明"
    pathogen_text = "、".join(final_pathogens) if final_pathogens else "不明"
    
    llm_prompt = get_education_prompt(syndrome, risk_text, pathogen_text, regimen_text)
    st.code(llm_prompt, language="markdown")
