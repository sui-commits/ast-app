import streamlit as st
import pandas as pd

# ページ設定 (スマホ最適化)
st.set_page_config(page_title="Rule-Engine AST Guide", layout="centered")

# カスタムCSS (余白調整とカードデザイン)
st.markdown("""
<style>
    .reportview-container .main .block-container{ padding-top: 1rem; }
    /* トグルの微調整 */
    .stCheckbox { margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_rules():
    try:
        df = pd.read_csv("data.csv", encoding="utf-8-sig", skipinitialspace=True)
        df.columns = df.columns.str.strip()
        df.fillna("", inplace=True)
        return df
    except:
        return None

st.title("🦠 Empiric Tx Guide")
st.caption("順次評価型ルールエンジン / 新人教育サポート機能付き")

df = load_rules()
if df is None:
    st.error("data.csv が読み込めません。")
    st.stop()

syndrome_list = ["未選択"] + df['syndrome'].unique().tolist()
syndrome = st.selectbox("📌 感染フォーカスを選択", syndrome_list)

if syndrome != "未選択":
    st.subheader("⚠️ 患者リスク層別化")
    st.caption("該当する項目をオンにしてください")
    
    # UI改善: チェックボックスからiPhoneライクなトグルスイッチに変更
    c1, c2 = st.columns(2)
    with c1:
        risk_mrsa = st.toggle("MRSAリスク")
        risk_pseudo = st.toggle("緑膿菌リスク")
        allergy_pcg = st.toggle("PCGアレルギー")
    with c2:
        risk_esbl = st.toggle("ESBLリスク")
        risk_lis = st.toggle("リステリアリスク")
        is_shock = st.toggle("敗血症性ショック")

    # --- ルールエンジンの評価プロセス ---
    active_triggers = ['base']
    active_risk_names = [] # プロンプト出力用リスト
    
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
        st.info(" , ".join(final_pathogens))

        st.markdown("**💉 推奨レジメン:**")
        for r in final_regimens:
            for split_r in r.split(' / '):
                if split_r.strip():
                    st.success(split_r.strip())

        with st.expander("📖 ロジックの実行軌跡 (Rationale)"):
            for msg in rationales:
                st.markdown(msg)

    # --- 新人教育用 LLMプロンプト生成機能 ---
    st.divider()
    st.subheader("🎓 新人教育用：AI解説プロンプト")
    st.caption("以下の枠内の右上にあるコピーボタンを押し、Gemini等に貼り付けると、医学的な解説を出力します。")
    
    # 選択状況に応じたテキストの動的生成
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

専門的な用語は使いつつも、クリニカル・リーズニングの思考プロセスが伝わるようにロジカルにステップ・バイ・ステップで解説してください。"""

    # コピーしやすいように st.code を使用
    st.code(llm_prompt, language="markdown")
