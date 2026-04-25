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
    /* メイン画面の余白を調整 */
    .main .block-container { padding-top: 2rem; padding-bottom: 50px; }
    
    /* 📌 ポップオーバーを通常の配置（上部）に変更 */
    div[data-testid="stPopover"] {
        width: 100%;
        margin-bottom: 20px;
    }
    
    /* 擬似テキストフィールド（ポップオーバーのボタン）のデザイン */
    div[data-testid="stPopover"] > button {
        background-color: #e3f2fd;
        color: #333;
        width: 100%;
        border-radius: 12px;
        border: 1px solid #90caf9;
        padding: 15px;
        font-size: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        display: flex;
        justify-content: flex-start;
    }
    
    /* ポップオーバーの中身 */
    div[data-testid="stPopoverBody"] {
        background-color: #f8f9fa;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(filename):
    try:
        # UTF-8-SIGで読み込み、不要な空白を除去
        df = pd.read_csv(filename, encoding="utf-8-sig", skipinitialspace=True)
        df.columns = df.columns.str.strip()
        df.fillna("", inplace=True)
        return df
    except:
        return None

# データの読み込み
df = load_data("data.csv")
risk_df = load_data("risks.csv")
risk_help = dict(zip(risk_df['risk_id'], risk_df['description'])) if risk_df is not None else {}

# 感染フォーカスリストの作成
if df is not None:
    syndrome_list = ["未選択"] + df['syndrome'].unique().tolist()
else:
    syndrome_list = ["未選択"]
    st.error("data.csv が読み込めませんでした。ファイルを確認してください。")

# --- 1. 感染フォーカス選択 (一番上に配置) ---
with st.popover(f"📌 感染フォーカスを選択: {st.session_state.syndrome}"):
    selected = st.radio(
        "感染フォーカスを選択", 
        syndrome_list, 
        index=syndrome_list.index(st.session_state.syndrome) if st.session_state.syndrome in syndrome_list else 0,
        label_visibility="collapsed"
    )
    
    if selected != st.session_state.syndrome:
        st.session_state.syndrome = selected
        st.rerun()

# --- 2. ルールエンジン & UI表示 (デフォルトで表示) ---
st.subheader(f"📍 ターゲット: {st.session_state.syndrome}")
st.caption("該当する患者リスクをオンにしてください")

# リスク選択トグル
c1, c2 = st.columns(2)
with c1:
    risk_mrsa = st.toggle("MRSAリスク", help=risk_help.get('risk_mrsa'))
    risk_pseudo = st.toggle("緑膿菌リスク", help=risk_help.get('risk_pseudo'))
    allergy_pcg = st.toggle("PCGアレルギー", help=risk_help.get('allergy_pcg'))
with c2:
    risk_esbl = st.toggle("ESBLリスク", help=risk_help.get('risk_esbl'))
    risk_lis = st.toggle("リステリアリスク", help=risk_help.get('risk_lis'))
    is_shock = st.toggle("ショック状態", help=risk_help.get('is_shock'))

# --- ルール判定ロジック ---
active_triggers = ['base']
active_risk_names = []

if allergy_pcg: 
    active_triggers.append('allergy_pcg'); active_risk_names.append("ペニシリンアレルギー")
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
rules = df[df['syndrome'] == st.session_state.syndrome] if df is not None else pd.DataFrame()

final_pathogens = []
final_regimens = []
rationales = []

if not rules.empty:
    # 🌟 ステップ1: まず 'base' (基本ルール) だけを先にすべて適用する
    for _, row in rules[rules['trigger'] == 'base'].iterrows():
        action = str(row['action']).strip()
        val = str(row['value']).strip()
        rat = str(row['rationale']).strip()

        if rat: rationales.append(f"• {rat}")
        if action == 'add_pathogen':
            final_pathogens.append(val)
        elif action in ['set_regimen', 'override_regimen']:
            final_regimens = [val]
        elif action == 'add_regimen' and val not in final_regimens:
            final_regimens.append(val)

    # 🌟 ステップ2: 次に 'base' 以外のリスク・アレルギールールを適用する
    for _, row in rules[rules['trigger'] != 'base'].iterrows():
        trigger = str(row['trigger']).strip()
        if trigger in active_triggers:
            action = str(row['action']).strip()
            val = str(row['value']).strip()
            rat = str(row['rationale']).strip()

            if rat: rationales.append(f"• {rat}")
            if action == 'add_pathogen':
                final_pathogens.append(val)
            elif action in ['set_regimen', 'override_regimen']:
                final_regimens = [val]
            elif action == 'add_regimen' and val not in final_regimens:
                final_regimens.append(val)

    # 🌟 ステップ3: 禁忌薬剤の強制フィルタリング（最終安全チェック）
    if allergy_pcg:
        # 除外したいペニシリン系薬剤のキーワード（部分一致で弾きます）
        forbidden_drugs = ["PCG", "TAZ/PIPC", "ABPC", "SBT/ABPC", "PIPC"]
        
        safe_regimens = []
        for r in final_regimens:
            # 薬剤名(r)の中に forbidden_drugs の文字列が含まれていないか確認
            if not any(forbidden in r for forbidden in forbidden_drugs):
                safe_regimens.append(r)
            else:
                # 削除した場合は理由を Rationale に追記して見える化する
                rationales.append(f"⚠️ 【禁忌回避】ペニシリンアレルギーのため候補から「{r}」を強制除外しました。")
        
        final_regimens = safe_regimens

# --- 結果表示 (推奨エンピリック治療カード) ---
st.divider()

with st.container(border=True):
    st.subheader("💊 推奨エンピリック治療")
    
    st.markdown("**🎯 想定起炎菌:**")
    pathogen_display = " , ".join(final_pathogens) if final_pathogens else "選択待ち..."
    st.info(pathogen_display)

    st.markdown("**💉 推奨レジメン:**")
    if final_regimens:
        for r in final_regimens:
            # スラッシュ区切りなどで複数の候補がある場合の表示分割
            for split_r in r.split(' / '):
                if split_r.strip():
                    st.success(split_r.strip())
    else:
        st.warning("条件に合致する安全なレジメンデータがありません。代替薬を確認してください。")

    with st.expander("📖 ロジックの実行軌跡 (Rationale)"):
        if rationales:
            for msg in rationales:
                st.markdown(msg)
        else:
            st.markdown("実行された個別ルールはありません。")

# --- 新人教育用 AIプロンプト生成 ---
st.divider()
st.subheader("🎓 新人教育用：AI解説プロンプト")
st.caption("右上にあるコピーボタンを押し、Gemini等に貼り付けてください。")

risk_text = "特になし" if not active_risk_names else "、".join(active_risk_names)
regimen_text = " または ".join(final_regimens) if final_regimens else "代替薬を検討中"
pathogen_text = "、".join(final_pathogens) if final_pathogens else "不明"

llm_prompt = get_education_prompt(st.session_state.syndrome, risk_text, pathogen_text, regimen_text)
st.code(llm_prompt, language="markdown")
