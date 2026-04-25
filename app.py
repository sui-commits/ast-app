import streamlit as st

# --- ページ設定 (スマホ最適化) ---
st.set_page_config(page_title="Empiric Tx Guide", layout="centered", initial_sidebar_state="collapsed")

# --- カスタムCSS (スマホでの視認性向上) ---
st.markdown("""
<style>
    .reportview-container .main .block-container{ padding-top: 2rem; }
    div[data-testid="stExpander"] { border-left: 4px solid #4CAF50; }
</style>
""", unsafe_allow_html=True)

# --- ヘッダー ---
st.title("🦠 Empiric Tx Guide")
st.caption("※本システムは医療従事者向けの参照情報（プロトタイプ）です。患者個別の投与量調整（腎機能等）は別途行い、最終的な処方決定は医師の判断に基づきます。")

# --- Step 1: シンドローム選択 ---
st.subheader("1. 感染フォーカスの選択")
syndrome = st.selectbox(
    "症状・疑われる疾患を選択してください",
    ["選択してください", "市中肺炎 (CAP) - 中等症〜重症", "複雑性尿路感染症 (cUTI) / 腎盂腎炎"]
)

if syndrome != "選択してください":
    # --- Step 2: リスク層別化 (スマホでタップしやすいチェックボックス) ---
    st.subheader("2. 患者リスク評価")
    st.info("該当する項目をタップしてください（複数選択可）")
    
    col1, col2 = st.columns(2)
    with col1:
        risk_mrsa = st.checkbox("MRSA リスク", help="過去のMRSA検出歴, 頻回な入院・抗菌薬投与歴, 透析など")
        risk_pseudo = st.checkbox("緑膿菌 リスク", help="構造的肺疾患(気管支拡張症等), 過去90日以内の抗菌薬使用")
    with col2:
        risk_esbl = st.checkbox("ESBL リスク", help="過去の検出歴, 最近の東南アジア等への渡航歴, 複雑性尿路疾患")
        allergy_pcg = st.checkbox("PCG アレルギー", help="ペニシリン系に対するアナフィラキシー等の重症アレルギー")

    st.divider()

    # --- Step 3: 推論エンジン (ロジック処理) ---
    st.subheader("3. 推奨エンピリック治療")
    
    pathogens = []
    regimen_primary = []
    regimen_alt = []
    rationale = ""

    if syndrome == "市中肺炎 (CAP) - 中等症〜重症":
        pathogens = ["肺炎球菌 (S. pneumoniae)", "インフルエンザ菌 (H. influenzae)", "非定型病原体 (Mycoplasma等)"]
        rationale = "定型菌および非定型菌のダブルカバーを基本とします。"
        
        # ベースライン
        if allergy_pcg:
            regimen_primary = ["LVFX (レボフロキサシン) 500mg/日"]
        else:
            regimen_primary = ["CTRX (セフトリアキソン) + AZM (アジスロマイシン)", "SBT/ABPC (アンピシリン・スルバクタム) + AZM"]

        # リスク加味
        if risk_pseudo and risk_mrsa:
            pathogens.extend(["緑膿菌 (P. aeruginosa)", "MRSA"])
            if allergy_pcg:
                regimen_primary = ["AZT (アズトレオナム) + LVFX + VCM (バンコマイシン)"]
            else:
                regimen_primary = ["CFPM (セフェピム) + VCM", "TAZ/PIPC (タゾバクタム・ピペラシリン) + VCM"]
            rationale = "緑膿菌およびMRSAのカバーが必須です。抗MRSA薬（VCMまたはLZD）を追加し、抗緑膿菌活性のあるβラクタム系を選択します。"
            
        elif risk_pseudo:
            pathogens.append("緑膿菌 (P. aeruginosa)")
            if allergy_pcg:
                regimen_primary = ["LVFX (高用量)"]
            else:
                regimen_primary = ["CFPM (セフェピム) + AZM", "TAZ/PIPC (タゾバクタム・ピペラシリン) + AZM"]
            rationale = "緑膿菌カバーのため、第4世代セフェムまたはTAZ/PIPCへエスカレーションします。"

        elif risk_mrsa:
            pathogens.append("MRSA")
            regimen_primary = [r + " + VCM" for r in regimen_primary]
            rationale = "標準治療に加えてMRSAカバー（VCM等）を追加します。"

    elif syndrome == "複雑性尿路感染症 (cUTI) / 腎盂腎炎":
        pathogens = ["大腸菌 (E. coli)", "Klebsiella属"]
        rationale = "腸内細菌目細菌をターゲットとします。血液培養および尿培養の提出が必須です。"

        # ベースライン
        if allergy_pcg:
            regimen_primary = ["LVFX (レボフロキサシン) または AMK (アミカシン)"]
        else:
            regimen_primary = ["CTRX (セフトリアキソン)", "CMZ (セフメタゾール) ※ESBL非産生想定"]

        # リスク加味
        if risk_esbl:
            pathogens.append("ESBL産生腸内細菌目細菌")
            if allergy_pcg:
                regimen_primary = ["AMK (アミカシン) ※全身状態安定時"]
            else:
                regimen_primary = ["MEPM (メロペネム)", "FMOX (フロモキセフ) ※軽症〜中等症かつ感受性良好な場合"]
            rationale = "ESBL産生菌を想定し、カルバペネム系（MEPM）またはセファマイシン系/オキサセフェム系を第一選択とします。"
            
        if risk_pseudo:
            pathogens.append("緑膿菌 (P. aeruginosa)")
            if allergy_pcg:
                regimen_primary = ["AMK (アミカシン) または LVFX"]
            else:
                regimen_primary = ["CFPM (セフェピム)", "TAZ/PIPC (タゾバクタム・ピペラシリン)"]
            rationale = "緑膿菌カバーを含む広域スペクトルの抗菌薬を選択します。"


    # --- Step 4: 結果の出力 (スマホで見やすいカードUI) ---
    with st.container():
        st.markdown(f"**🎯 想定される起炎菌**")
        st.write(", ".join(pathogens))
        
        st.markdown(f"**💊 推奨第一選択薬**")
        for reg in regimen_primary:
            st.success(reg)
            
        with st.expander("📚 クリニカル・パール / ロジックの根拠", expanded=False):
            st.write(rationale)
            st.caption("※自施設のアンチバイオグラム（大腸菌のLVFX耐性率、ESBL検出率など）に応じて、推奨薬の順位をローカライズしてください。")
