import streamlit as st
import pandas as pd
from prompts.prompt_builder import get_education_prompt

# ページ設定 (スマホ最適化)
st.set_page_config(page_title="Expert AST Guide", layout="centered")

# --- UIデザイン: 最初の固定表示CSSにリセット ---
st.markdown("""
<style>
    .main .block-container { padding-bottom: 180px; }
    div[data-testid="stSelectbox"] {
        position: fixed;
        bottom: 30px; left: 5%; width: 90%; z-index: 9999;
        background-color: white; padding: 8px; border-radius: 15px;
        box-shadow: 0 -8px 20px rgba(0,0,0,0.15);
    }
    .stToggle { padding: 8px; background: #f8f9fa; border-radius: 10px; margin-bottom: 5px; }
    .stTooltipIcon { color: #007bff; }
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

# データの読み込み
df = load_data("data.csv")
risk_df = load_data("risks.csv")

if df is None:
    st.error("⚠️ data.csv が読み込めません。")
    st.stop()

# リスクIDをキーにして説明文を引ける辞書を作る
risk_help = dict(zip(risk_df['risk_id'], risk_df['description'])) if risk_df is not None else {}

syndrome_list = ["未選択"] + df['syndrome'].unique().tolist()
# 最も安定している通常のselectboxに戻しました
syndrome = st.selectbox("📌 感染フォーカスを選択", syndrome_list)

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

    # --- ルールエンジンの評価プロセス ---
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
        active_risk_names.append("リステリアリスクあり（高齢・免疫不全など）")
    if is_shock: 
        active_triggers.append('is_shock')
        active_risk_names.append("敗血症性ショック（血行動態不安定）")

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

    # --- UIの改善: 結果をカードデザインで囲む ---
    st.divider()
    
    with st.container(border=True):
        st.subheader("💊 推奨エンピリック治療")
        
        st.markdown("**🎯 想定起炎菌:**")
        pathogen_display = " , ".join(final_pathogens) if final_pathogens else "データなし"
        st.info(pathogen_display)

        st.markdown("**💉 推奨レジメン:**")
        if final_regimens:
            for r in final_regimens:
                if r.strip():
                    # 👈 TAZ/PIPCが分割されないよう、スラッシュ( / )での分割処理を削除しています
                    st.success(r.strip()) 
        else:
            st.warning("該当するレジメンデータがありません")

        with st.expander("📖 ロジックの実行軌跡 (Rationale)"):
            if rationales:
                for msg in rationales:
                    st.markdown(msg)
            else:
                st.markdown("実行軌跡はありません。")

    # --- 新人教育用 LLMプロンプト生成機能 ---
    st.divider()
    st.subheader("🎓 新人教育用：AI解説プロンプト")
    st.caption("以下の枠内の右上にあるコピーボタンを押し、Gemini等に貼り付けると、医学的な解説を出力します。")
    
    risk_text = "特になし" if not active_risk_names else "、".join(active_risk_names)
    regimen_text = " または ".join(final_regimens) if final_regimens else "不明"
    pathogen_text = "、".join(final_pathogens) if final_pathogens else "不明"
    
    llm_prompt = get_education_prompt(syndrome, risk_text, pathogen_text, regimen_text)
    st.code(llm_prompt, language="markdown")
