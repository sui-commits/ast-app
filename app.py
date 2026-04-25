import streamlit as st
import pandas as pd

st.set_page_config(page_title="Rule-Engine AST Guide", layout="centered")
st.markdown("<style>.stCheckbox { padding: 5px; background: #f0f2f6; border-radius: 5px; margin-bottom: 5px; }</style>", unsafe_allow_html=True)

@st.cache_data
def load_rules():
    try:
        df = pd.read_csv("data.csv", encoding="utf-8-sig", skipinitialspace=True)
        df.columns = df.columns.str.strip()
        # 空白セルを空文字にしておく
        df.fillna("", inplace=True)
        return df
    except:
        return None

st.title("🦠 Rule-Engine Tx Guide")
st.caption("順次評価型ルールエンジンで駆動するエンピリック治療支援")

df = load_rules()
if df is None:
    st.error("data.csv が読み込めません。")
    st.stop()

# 選択肢の生成（重複を除外してリスト化）
syndrome_list = ["未選択"] + df['syndrome'].unique().tolist()
syndrome = st.selectbox("感染フォーカス", syndrome_list)

if syndrome != "未選択":
    st.subheader("患者リスク層別化")
    c1, c2 = st.columns(2)
    with c1:
        risk_mrsa = st.checkbox("MRSAリスク")
        risk_pseudo = st.checkbox("緑膿菌リスク")
        allergy_pcg = st.checkbox("PCGアレルギー")
    with c2:
        risk_esbl = st.checkbox("ESBLリスク")
        risk_lis = st.checkbox("リステリアリスク")
        is_shock = st.checkbox("敗血症性ショック")

    # --- ルールエンジンの評価プロセス ---
    
    # 1. 現在発火しているトリガーのリストを作成
    active_triggers = ['base']
    if allergy_pcg: active_triggers.append('allergy_pcg')
    if risk_mrsa: active_triggers.append('risk_mrsa')
    if risk_pseudo: active_triggers.append('risk_pseudo')
    if risk_esbl: active_triggers.append('risk_esbl')
    if risk_lis: active_triggers.append('risk_lis')
    if is_shock: active_triggers.append('is_shock')

    # 2. 該当疾患のルールだけを抽出
    rules = df[df['syndrome'] == syndrome]

    # 結果を格納する変数
    final_pathogens = []
    final_regimens = []
    rationales = []

    # 3. ルールを上から順番に評価し、アクションを実行
    for _, row in rules.iterrows():
        trigger = str(row['trigger']).strip()
        
        # このルールのトリガーが発火条件に含まれているか？
        if trigger in active_triggers:
            action = str(row['action']).strip()
            val = str(row['value']).strip()
            rat = str(row['rationale']).strip()

            # 根拠・コメントの保存
            if rat:
                rationales.append(f"✓ {rat}")

            # アクションの実行（操作命令のパース）
            if action == 'add_pathogen':
                final_pathogens.append(val)
            elif action == 'set_regimen' or action == 'override_regimen':
                # レジメンを丸ごと書き換え
                final_regimens = [val]
            elif action == 'add_regimen':
                # レジメンを追加（併用）
                if val not in final_regimens:
                    final_regimens.append(val)

    # --- 結果の出力 ---
    st.divider()
    st.subheader("推奨エンピリック治療")
    
    st.markdown("**🎯 想定起炎菌:**")
    st.write(" , ".join(final_pathogens))

    st.markdown("**💊 推奨レジメン:**")
    for r in final_regimens:
        # スラッシュ区切りを見やすく分割して表示
        for split_r in r.split('/'):
            st.success(split_r.strip())

    with st.expander("📖 ロジックの実行軌跡 / Rationale", expanded=True):
        for msg in rationales:
            st.markdown(msg)
