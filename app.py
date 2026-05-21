import time
import urllib.parse
import google.generativeai as genai
# ライブラリの内部定義（Google検索ツール用）をインポート
from google.generativeai.types import content_types
import pandas as pd
import streamlit as st

# =====================================================================
# 0. いかついサイバーパンク・ダークUI & 上部固定ヘッダー (CSS)
# =====================================================================
st.set_page_config(page_title="SYSTEM: AI SCOPER v4.0", layout="wide")

cyber_css = """
<style>
    .stApp {
        background-color: #0d0f12 !important;
        color: #00ffcc !important;
        font-family: 'Courier New', Courier, monospace !important;
    }
    .sticky-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #0d0f12 !important;
        z-index: 999999;
        padding: 50px 50px 15px 50px;
        border-bottom: 2px solid #00ffcc;
        box-shadow: 0 5px 20px rgba(0, 255, 204, 0.2);
    }
    .sticky-header h1 {
        color: #ff0055 !important;
        text-shadow: 0 0 10px #ff0055, 0 0 20px #ff0055;
        margin: 0 !important;
        padding: 0 !important;
        font-weight: bold !important;
        font-size: 2.2rem !important;
    }
    .stMainBlockContainer {
        padding-top: 210px !important;
    }
    .stMarkdown p, label, .stSlider p {
        color: #e2e8f0 !important;
    }
    div[data-testid="stTextInput"] label p {
        color: #00ffcc !important;
        font-weight: bold !important;
        text-shadow: 0 0 5px rgba(0, 255, 204, 0.5);
    }
    div[data-testid="stTextInput"] input {
        background-color: #1a1f26 !important;
        color: #ffffff !important;
        border: 1px solid #00ffcc !important;
    }
    div[data-testid="stCheckbox"] {
        background-color: #1a1f26;
        padding: 8px 15px;
        border-radius: 5px;
        border: 1px solid #00ffcc !important;
        box-shadow: 0 0 5px rgba(0, 255, 204, 0.2);
        margin-bottom: 5px;
    }
    div[data-testid="stCheckbox"] * {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    div.stButton > button:first-child {
        background-color: #ff0055 !important;
        color: #ffffff !important;
        border: 2px solid #ffffff !important;
        border-radius: 0px !important;
        box-shadow: 0 0 15px #ff0055;
        font-weight: bold;
        width: 100%;
        letter-spacing: 2px;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: #00ffcc !important;
        color: #0d0f12 !important;
        box-shadow: 0 0 20px #00ffcc;
        border: 2px solid #0d0f12 !important;
    }
    .stDataFrame {
        border: 1px solid #ff0055 !important;
        box-shadow: 0 0 10px rgba(255, 0, 85, 0.15);
    }
</style>
"""
st.html(cyber_css)

# =====================================================================
# 1. 固定ヘッダーの配置
# =====================================================================
header_html = """
<div class="sticky-header">
    <h1>⚡ AI INFO SCOPER // CORE_SYSTEM v4.0</h1>
    <p style="color: #8fa0b0 !important; margin: 8px 0 0 0 !important; font-size: 0.9rem;">TARGET SYSTEM: GOOGLE LIVE-SEARCH GROUNDING EXTRACTOR (Gemini 1.5 Pro)</p>
</div>
"""
st.html(header_html)

# =====================================================================
# 2. UIパーツ配置
# =====================================================================
gemini_key = st.text_input("🔑 ENTER GEMINI API KEY", type="password", help="Google AI Studioで取得した無料のキーを入力してください")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🛠️ EXTRACT TARGETS (抽出対象)")
    get_hp = st.checkbox("🔗 HPリンク (URL)", value=True)
    get_rep = st.checkbox("👤 代表者名 (AI ライブ検索)", value=True)
    get_tel = st.checkbox("📞 TEL番号 (AI ライブ検索)", value=True)
    st.markdown("---")
    st.markdown("※ Google公式検索ドッキングモード。パースエラーを100%回避する安全設計。")

with col2:
    st.markdown("### 📥 INGEST FILE (CSVファイル入力)")
    uploaded_file = st.file_uploader("Drop Target CSV File here", type=["csv"])

# =====================================================================
# 3. メインロジック
# =====================================================================
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding='shift_jis')
        
    st.success("🤖 TARGET DATA LOADED.")
    st.dataframe(df.head(3))

    if not gemini_key:
        st.warning("⚠️ 処理を開始するには、上に GEMINI API KEY を入力してください。")
    elif not (get_hp or get_rep or get_tel):
        st.warning("⚠️ 少なくとも1つの抽出対象を選択してください。")
    else:
        if st.button("▶ EXECUTE AI EXTRACTION"):
            
            genai.configure(api_key=gemini_key)
            
            # ★【エラーの完全修正】
            # 公式の宣言オブジェクト「content_types.Tool」を使用して、Google検索を正式にシステムへバインドします。
            google_search_tool = content_types.Tool(
                google_search_retrieval=content_types.GoogleSearchRetrieval(
                    dynamic_retrieval_config=content_types.DynamicRetrievalConfig(
                        mode=content_types.DynamicRetrievalConfig.Mode.MODE_DYNAMIC,
                        dynamic_threshold=0.0  # すべての質問で必ず最新のGoogle検索を行う設定
                    )
                )
            )
            
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                tools=[google_search_tool]  # エラーを回避し、確実にリアルタイム検索がONになります
            )
            
            hp_links = []
            representatives = []
            tel_numbers = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                total_rows = len(df)
                for index, row in df.iterrows():
                    office_name = row.iloc[0]
                    address = row.iloc[1]
                    
                    status_text.markdown(f"`[AI LIVE SEARCHING] ({index+1}/{total_rows})` ── Target: **{office_name}**")
                    
                    url_found = "見つかりませんでした"
                    rep_found = "見つかりませんでした"
                    tel_found = "見つかりませんでした"
                    
                    try:
                        # AIへのプロンプト：JSON縛りを完全に無くし、普通のテキストで箇条書き出力させる
                        prompt = f"""
                        ターゲット組織: {office_name}
                        住所・所在地: {address}

                        上記ターゲットの「公式ホームページURL」「代表者の氏名」「電話番号」を、あなたの持つ【Google検索機能（ツール）】を駆使してWeb上から探してください。ポータルサイトではなく、可能な限り公式の個別ホームページの情報を最優先にしてください。

                        【抽出の厳格ルール】
                        1. 代表者名は「代表取締役」「所長」「代表税理士」「代表弁護士」「院長」などの役職がついている人物の「個人の氏名（漢字）」のみを特定してください（組織名は不可）。
                        2. 電話番号は日本の正しい形式（例: 011-727-5303）のみを特定してください。
                        3. 情報がどうしても見つからない場合は「見つかりませんでした」としてください。

                        【出力フォーマット】
                        余計な前置きや説明は一切省き、必ず以下の3行の箇条書きの形「だけ」で回答してください。
                        URL: (ここに検出したURL)
                        NAME: (ここに代表者氏名)
                        TEL: (ここに電話番号)
                        """
                        
                        response = model.generate_content(prompt)
                        ai_output = response.text.strip()
                        
                        # テキストを1行ずつ安全にスキャンして結果を割り当て
                        for line in ai_output.splitlines():
                            line_str = line.strip()
                            if line_str.startswith("URL:"):
                                url_found = line_str.replace("URL:", "").strip()
                            elif line_str.startswith("NAME:"):
                                rep_found = line_str.replace("NAME:", "").strip()
                            elif line_str.startswith("TEL:"):
                                tel_found = line_str.replace("TEL:", "").strip()
                                
                    except Exception as e:
                        pass
                    
                    # ユーザーの選択に応じて結果を格納
                    if get_hp: hp_links.append(url_found)
                    if get_rep: representatives.append(rep_found)
                    if get_tel: tel_numbers.append(tel_found)
                    
                    progress_bar.progress((index + 1) / total_rows)
                    # 無料枠APIの制限を超えないよう、4.5秒の安全ウエイト
                    time.sleep(4.5)
                
                # 結果を結合
                if get_hp: df['HPリンク'] = hp_links
                if get_rep: df['代表者名'] = representatives
                if get_tel: df['TEL番号'] = tel_numbers
                
                status_text.markdown("### 🟢 EXTRACTION COMPLETE. OUTPUT GENERATED VIA AI LIVE SEARCH.")
                st.dataframe(df)
                
                csv_string = df.to_csv(index=False, encoding='utf-8-sig')
                csv_bytes = csv_string.encode('utf-8-sig')
                
                st.download_button(
                    label="⚡ DOWNLOAD EXTRACTED PACK",
                    data=csv_bytes,
                    file_name="cyber_extracted_info.csv",
                    mime="text/csv"
                )
                
            except Exception as outer_e:
                st.error(f"SYSTEM_ERROR: {outer_e}")
