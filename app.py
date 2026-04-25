import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="Expert AST Guide", layout="centered")

# CSS: スマホ向けの余白調整
st.markdown("""
<style>
    .main .block-container { padding-top: 20px; padding-bottom: 100px; }
    .stToggle { padding: 8px; background: #f8f9fa; border-radius: 10px; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# 2. データの読み込み関数
@st.cache_data
def load_data(filename):
    try:
        df = pd.read_csv(filename, encoding="utf-8-sig", skipinitialspace=True)
        df.columns = df.columns.str.strip()
        df.fillna("", inplace=True)
        return df
    except Exception as e:
        # ファイルがない場合などは None を返す
        return None

df = load_data("data.csv")
risk_df = load_data("risks.csv")
risk_help = dict(zip(risk_df['risk_id'], risk_df['description'])) if risk_df is not None else {}

# --- ★重要: ここで先に syndrome_list を定義する ---
if df is not None:
    syndrome_list = ["未選択"] + df['syndrome'].unique().tolist()
else:
    syndrome_list = ["未選択"]
    st.error("⚠️ data.csv が読み込めませんでした。GitHubにファイルがあるか確認してください。")

# 3. 感染フォーカスの選択（キーボードが出ない UI）
# st.segmented_control を使うことでボタン形式になり、入力モードになりません
syndrome = st.segmented_control(
    "📌 感染フォーカスを選択", 
    syndrome_list, 
    default="未選択"
)

# 4. メインロジック
if syndrome != "未選択" and df is not None:
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

    # アクティブな条件の整理
    active_triggers = ['base']
    active_risk_names = []
    
    if allergy_pcg: 
        active_triggers.append('allergy_pcg'); active_risk_names.append("PCGアレルギー")
    if risk_mrsa: 
        active_triggers.append('risk_mrsa'); active_risk_names.append("MRSAリスク")
    if risk_pseudo: 
        active_triggers.append('risk_pseudo'); active_risk_names.append("緑膿菌リスク")
    if risk_esbl: 
        active_triggers.append('risk_esbl'); active_risk_names.append("ESBLリスク")
    if risk_lis: 
        active_triggers.append('risk_lis'); active_risk_names.append("リステリアリスク")
    if is_shock: 
        active_triggers.append('is_shock'); active_risk_names.append("ショック状態")

    # フィルタリング
    rules = df[df['syndrome'] == syndrome]
    final_pathogens = []
    final_regimens = []
    rationales = []

    for _, row in rules.iterrows():
        trigger = str(row['trigger']).strip()
        if trigger in active_triggers:
            action, val, rat = str(row['action']), str(row['value']), str(row['rationale'])
            if rat: rationales.append(f"• {rat}")
            if action == 'add_pathogen' and val not in final_pathogens: final_pathogens.append(val)
            elif action in ['set_regimen', 'override_regimen']: final_regimens = [val]
            elif action == 'add_regimen' and val not in final_regimens: final_regimens.append(val)

    # 結果表示
    st.divider()
    with st.container(border=True):
        st.subheader("💊 推奨エンピリック治療")
        st.markdown("**🎯 想定起炎菌:**")
        st.info(" , ".join(final_pathogens) if final_pathogens else "不明")

        st.markdown("**💉 推奨レジメン:**")
        if final_regimens:
            for r in final_regimens:
                for split_r in r.split(' / '):
                    if split_r.strip(): st.success(split_r.strip())
        
        with st.expander("📖 ロジックの根拠"):
            for msg in rationales: st.markdown(msg)

    # LLM用プロンプト
    st.divider()
    st.subheader("🎓 教育用プロンプト")
    risk_text = "特になし" if not active_risk_names else "、".join(active_risk_names)
    prompt = f"感染フォーカス: {syndrome}\nリスク: {risk_text}\n起炎菌: {'、'.join(final_pathogens)}\n推奨薬: {' / '.join(final_regimens)}\n\nこれについて若手向けに詳しく解説して。"
    st.code(prompt, language="markdown")

else:
    if df is not None:
        st.info("👆 上のボタンから感染フォーカスを選択してください。")
