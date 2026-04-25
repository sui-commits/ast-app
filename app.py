import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="Expert AST Guide", layout="centered")

# --- UIデザイン ---
st.markdown("""
<style>
    .main .block-container { padding-bottom: 180px; }
    .stToggle { padding: 8px; background: #f8f9fa; border-radius: 10px; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(filename):
    try:
        # サンプルデータがない場合を考慮し、読み込み処理を安全に
        df = pd.read_csv(filename, encoding="utf-8-sig", skipinitialspace=True)
        df.columns = df.columns.str.strip()
        df.fillna("", inplace=True)
        return df
    except:
        return None

df = load_data("data.csv")
risk_df = load_data("risks.csv")
risk_help = dict(zip(risk_df['risk_id'], risk_df['description'])) if risk_df is not None else {}

# セレクトボックスを配置（bottom固定デザインを活かす場合はそのままでOK）
syndrome_list = ["未選択"] + (df['syndrome'].unique().tolist() if df is not None else [])
syndrome = st.selectbox("📌 感染フォーカスを選択", syndrome_list)

# --- メインロジック ---
if syndrome != "未選択":
    st.subheader("⚠️ 患者リスク層別化")
    st.caption("該当する項目をオンにしてください")
    
    c1, c2 = st.columns(2)
    with c1:
        # 変数名を下の判定用フラグと一致させる
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
    
    # 修正：toggleの戻り値を正しく参照
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

    # ルール適用
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
                if val not in final_pathogens: final_pathogens.append(val)
            elif action in ['set_regimen', 'override_regimen']:
                final_regimens = [val]
            elif action == 'add_regimen':
                if val not in final_regimens: final_regimens.append(val)

    # --- 結果表示 ---
    st.divider()
    with st.container(border=True):
        st.subheader("💊 推奨エンピリック治療")
        
        st.markdown("**🎯 想定起炎菌:**")
        st.info(" , ".join(final_pathogens) if final_pathogens else "データなし")

        st.markdown("**💉 推奨レジメン:**")
        if final_regimens:
            for r in final_regimens:
                for split_r in r.split(' / '):
                    if split_r.strip():
                        st.success(split_r.strip())
        else:
            st.warning("推奨レジメンが見つかりませんでした。データを確認してください。")

        with st.expander("📖 ロジックの実行軌跡 (Rationale)"):
            for msg in rationales:
                st.markdown(msg)

    # --- LLMプロンプト生成 ---
    st.divider()
    st.subheader("🎓 新人教育用：AI解説プロンプト")
    
    risk_text = "特になし" if not active_risk_names else "、".join(active_risk_names)
    regimen_text = " または ".join(final_regimens)
    pathogen_text = "、".join(final_pathogens)
    
    llm_prompt = f"""あなたは感染症専門医および指導医です。新人医療従事者（若手薬剤師や研修医）に対して、以下のエンピリック治療の選択ロジックを分かりやすく解説してください。

【症例設定】
・疑われる感染フォーカス: {syndrome}
・患者のリスク因子: {risk_text}

【当院システムが提示した推奨レジメン】
・想定される起炎菌: {pathogen_text}
・推奨薬剤: {regimen_text}

【解説してほしいこと】
1. なぜこの起炎菌を想定する必要があるのか（疫学やリスク因子との関連）
2. なぜこの抗菌薬が選択されたのか（スペクトル、組織移行性、ガイドラインの根拠）
3. この治療を行う上でのモニタリングの注意点（副作用、培養結果確認後のデ・エスカレーションのポイント）
4. （もしあれば）代替薬の選択肢と、それを選ばなかった理由

ロジカルにステップ・バイ・ステップで解説してください。"""

    st.code(llm_prompt, language="markdown")
else:
    st.info("👆 上のメニューから「感染フォーカス」を選択してください。")
