import streamlit as st

# --- ページ設定 (スマホ最適化) ---
st.set_page_config(page_title="Empiric Tx Guide", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .reportview-container .main .block-container{ padding-top: 2rem; }
    div[data-testid="stExpander"] { border-left: 4px solid #4CAF50; }
</style>
""", unsafe_allow_html=True)

st.title("🦠 Empiric Tx Guide")
st.caption("※本システムは医療従事者向けの参照情報（プロトタイプ）です。患者個別の投与量調整は別途行い、最終的な処方決定は医師の判断に基づきます。")

# --- Step 1: シンドローム選択 ---
st.subheader("1. 感染フォーカスの選択")
syndrome = st.selectbox(
    "症状・疑われる疾患を選択してください",
    [
        "選択してください", 
        "市中肺炎 (CAP) - 中等症〜重症", 
        "複雑性尿路感染症 (cUTI) / 腎盂腎炎",
        "皮膚軟部組織感染症 (SSTI) / 蜂窩織炎",
        "腹腔内感染症 (IAI) / 胆嚢炎・憩室炎など",
        "細菌性髄膜炎 (市中感染)",
        "発熱性好中球減少症 (FN)",
        "カテーテル関連血流感染症 (CRBSI)"
    ]
)

if syndrome != "選択してください":
    # --- Step 2: リスク層別化 ---
    st.subheader("2. 患者リスク評価")
    st.info("該当する項目をタップしてください（複数選択可）")
    
    col1, col2 = st.columns(2)
    with col1:
        risk_mrsa = st.checkbox("MRSA リスク", help="過去のMRSA検出歴, 頻回な入院・抗菌薬投与歴, 透析など")
        risk_pseudo = st.checkbox("緑膿菌 リスク", help="構造的肺疾患, 糖尿病性足潰瘍, 過去90日以内の抗菌薬使用")
        risk_listeria = st.checkbox("リステリア リスク", help="50歳以上、細胞性免疫不全（ステロイド使用、悪性腫瘍など）、妊婦")
    with col2:
        risk_esbl = st.checkbox("ESBL リスク", help="過去の検出歴, 最近の海外渡航歴, 複雑性尿路疾患")
        allergy_pcg = st.checkbox("PCG アレルギー", help="ペニシリン系に対するアナフィラキシー等の重症アレルギー")
        risk_shock = st.checkbox("血行動態不安定", help="敗血症性ショック、バイタルサインの著明な異常")

    st.divider()

    # --- Step 3: 推論エンジン (ロジック処理) ---
    st.subheader("3. 推奨エンピリック治療")
    
    pathogens = []
    regimen_primary = []
    rationale = ""

    # 1. 市中肺炎 (CAP)
    if syndrome == "市中肺炎 (CAP) - 中等症〜重症":
        pathogens = ["肺炎球菌", "インフルエンザ菌", "非定型病原体"]
        rationale = "定型菌および非定型菌のダブルカバーを基本とします。"
        
        if allergy_pcg:
            regimen_primary = ["LVFX (レボフロキサシン) 500mg/日"]
        else:
            regimen_primary = ["CTRX (セフトリアキソン) + AZM", "SBT/ABPC (アンピシリン・スルバクタム) + AZM"]

        if risk_pseudo and risk_mrsa:
            pathogens.extend(["緑膿菌", "MRSA"])
            regimen_primary = ["CFPM (セフェピム) + VCM", "TAZ/PIPC (タゾバクタム・ピペラシリン) + VCM"] if not allergy_pcg else ["AZT + LVFX + VCM"]
            rationale = "緑膿菌・MRSAカバーのため広域化します。"
        elif risk_pseudo:
            pathogens.append("緑膿菌")
            regimen_primary = ["CFPM + AZM", "TAZ/PIPC + AZM"] if not allergy_pcg else ["LVFX (高用量)"]
        elif risk_mrsa:
            pathogens.append("MRSA")
            regimen_primary = [r + " + VCM" for r in regimen_primary]

    # 2. 複雑性尿路感染症 (cUTI)
    elif syndrome == "複雑性尿路感染症 (cUTI) / 腎盂腎炎":
        pathogens = ["大腸菌", "Klebsiella属"]
        rationale = "腸内細菌目細菌をターゲットとします。血液培養・尿培養の提出が必須です。"

        if allergy_pcg:
            regimen_primary = ["LVFX (レボフロキサシン) または AMK (アミカシン)"]
        else:
            regimen_primary = ["CTRX (セフトリアキソン)", "CMZ (セフメタゾール) ※ESBL非産生想定"]

        if risk_esbl:
            pathogens.append("ESBL産生菌")
            regimen_primary = ["MEPM (メロペネム)"] if not allergy_pcg else ["AMK (アミカシン) ※全身状態安定時"]
            rationale = "ESBL産生を想定し、カルバペネム系等を第一選択とします。"
        if risk_pseudo:
            pathogens.append("緑膿菌")
            regimen_primary = ["CFPM", "TAZ/PIPC"] if not allergy_pcg else ["AMK または LVFX"]

    # 3. 皮膚軟部組織感染症 (SSTI)
    elif syndrome == "皮膚軟部組織感染症 (SSTI) / 蜂窩織炎":
        pathogens = ["化膿レンサ球菌", "黄色ブドウ球菌 (MSSA)"]
        rationale = "レンサ球菌およびMSSAをターゲットとした狭域スペクトルを基本とします。"

        if allergy_pcg:
            regimen_primary = ["CLDM (クリンダマイシン)", "VCM (バンコマイシン) ※重症時"]
        else:
            regimen_primary = ["CEZ (セファゾリン)", "SBT/ABPC (アンピシリン・スルバクタム) ※動物咬傷が疑われる場合"]

        if risk_mrsa:
            pathogens = ["化膿レンサ球菌", "黄色ブドウ球菌 (MRSA)"]
            regimen_primary = ["VCM (バンコマイシン)", "DAP (ダプトマイシン)"]
            rationale = "MRSAカバーが必須となるため、抗MRSA薬を選択します。"

    # 4. 腹腔内感染症 (IAI)
    elif syndrome == "腹腔内感染症 (IAI) / 胆嚢炎・憩室炎など":
        pathogens = ["腸内細菌目細菌 (大腸菌等)", "嫌気性菌 (Bacteroides等)", "腸球菌"]
        rationale = "グラム陰性桿菌および嫌気性菌のカバーが必須です。"

        if allergy_pcg:
            regimen_primary = ["LVFX (レボフロキサシン) + MNZ (メトロニダゾール)"]
        else:
            regimen_primary = ["CMZ (セフメタゾール)", "CTRX (セフトリアキソン) + MNZ", "SBT/ABPC (アンピシリン・スルバクタム)"]

        if risk_esbl:
            pathogens.append("ESBL産生菌")
            regimen_primary = ["MEPM (メロペネム)"]
            rationale = "ESBL産生菌を想定し、カルバペネム系を選択します。"
        if risk_pseudo:
            pathogens.append("緑膿菌")
            regimen_primary = ["TAZ/PIPC (タゾバクタム・ピペラシリン)", "CFPM (セフェピム) + MNZ"]

    # 5. 細菌性髄膜炎
    elif syndrome == "細菌性髄膜炎 (市中感染)":
        pathogens = ["肺炎球菌 (PRSP含む)", "髄膜炎菌", "インフルエンザ菌"]
        rationale = "血液培養採取後、直ちに抗菌薬とデキサメタゾンを投与してください。髄液移行性を考慮し、最大用量での投与が必要です。"
        
        if allergy_pcg:
            regimen_primary = ["MEPM (メロペネム) 6g/日 + VCM (バンコマイシン)"]
        else:
            regimen_primary = ["CTRX (セフトリアキソン) 4g/日 + VCM (バンコマイシン)"]

        if risk_listeria:
            pathogens.append("リステリア (L. monocytogenes)")
            if allergy_pcg:
                rationale += " ※リステリアのリスクがありますが、PCGアレルギーのためST合剤（トリメトプリム・スルファメトキサゾール）の追加や脱感作を専門医と相談してください。"
            else:
                regimen_primary = [r + " + ABPC (アンピシリン) 12g/日" for r in regimen_primary]
                rationale += " リステリアをカバーするためABPCを追加します。"

    # 6. 発熱性好中球減少症 (FN)
    elif syndrome == "発熱性好中球減少症 (FN)":
        pathogens = ["緑膿菌", "腸内細菌目細菌", "黄色ブドウ球菌", "表皮ブドウ球菌"]
        rationale = "迅速な抗緑膿菌活性を持つ殺菌的抗菌薬の投与が原則です。血液培養は最低2セット（中心静脈カテーテルと末梢血）採取してください。"
        
        if allergy_pcg:
            regimen_primary = ["AZT (アズトレオナム) + VCM (バンコマイシン)", "AMK (アミカシン) + VCM ※腎機能注意"]
        else:
            regimen_primary = ["CFPM (セフェピム)", "TAZ/PIPC (タゾバクタム・ピペラシリン)", "MEPM (メロペネム) ※ESBL既往や重症時"]

        if risk_mrsa or risk_shock:
            pathogens.append("MRSA")
            if not allergy_pcg:
                regimen_primary = [r + " + VCM (または LZD)" for r in regimen_primary]
            rationale += " 血行動態不安定、またはMRSAリスクがあるため、グラム陽性菌カバー（VCM等）を初期から追加します。"

    # 7. カテーテル関連血流感染症 (CRBSI)
    elif syndrome == "カテーテル関連血流感染症 (CRBSI)":
        pathogens = ["コアグラーゼ陰性ブドウ球菌 (CNS)", "黄色ブドウ球菌 (MRSA/MSSA)", "Candida属", "腸内細菌目細菌"]
        rationale = "カテーテルの抜去を検討し、MRSAを含むグラム陽性球菌を確実にカバーします。"
        
        regimen_primary = ["VCM (バンコマイシン)", "DAP (ダプトマイシン)"]
        
        if risk_shock or risk_pseudo:
            pathogens.append("緑膿菌などのグラム陰性桿菌")
            if allergy_pcg:
                regimen_primary = [r + " + AZT (アズトレオナム) または AMK" for r in regimen_primary]
            else:
                regimen_primary = [r + " + CFPM (セフェピム) または MEPM" for r in regimen_primary]
            rationale += " 重症またはグラム陰性桿菌のリスクがあるため、抗緑膿菌活性を持つβラクタム系を追加し、広域カバーとします。"

    # --- Step 4: 結果の出力 ---
    with st.container():
        st.markdown(f"**🎯 想定される起炎菌**")
        st.write(", ".join(pathogens))
        
        st.markdown(f"**💊 推奨第一選択薬**")
        for reg in regimen_primary:
            st.success(reg)
            
        with st.expander("📚 クリニカル・パール / ロジックの根拠", expanded=False):
            st.write(rationale)
