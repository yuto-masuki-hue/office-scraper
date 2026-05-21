import json
import time
import urllib.parse
import google.generativeai as genai
import pandas as pd
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# =====================================================================
# 0. いかついサイバーパンク・ダークUI & 上部固定ヘッダー (CSS)
# =====================================================================
st.set_page_config(page_title="SYSTEM: AI SCOPER v3.0", layout="wide")

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
    <h1>⚡ AI INFO SCOPER // CORE_SYSTEM v3.0</h1>
    <p style="color: #8fa0b0 !important; margin: 8px 0 0 0 !important; font-size: 0.9rem;">TARGET SYSTEM: AI-POWERED INTELLIGENCE EXTRACTOR (Gemini 1.5 Pro)</p>
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
    get_rep = st.checkbox("👤 代表者名 (AI 推論)", value=True)
    get_tel = st.checkbox("📞 TEL番号 (AI 推論)", value=True)
    st.markdown("---")
    st.markdown("※ Google検索エンジンの集約データを1.5 Proでダイレクトに精査します。")

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

    if not gemini_key and (get_rep or get_tel):
        st.warning("⚠️ 処理を開始するには、上に GEMINI API KEY を入力してください。")
    elif not (get_hp or get_rep or get_tel):
        st.warning("⚠️ 少なくとも1つの抽出対象を選択してください。")
    else:
        if st.button("▶ EXECUTE AI EXTRACTION"):
            
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-pro")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            # Googleのボット検知を完璧に回避する最新UA偽装
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
            
            chrome_options.binary_location = "/usr/bin/chromium"
            service = Service(executable_path="/usr/bin/chromedriver")
            
            try:
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.set_page_load_timeout(10)
                driver.implicitly_wait(3)
            except Exception as e:
                st.error(f"SYSTEM_CRITICAL: ブラウザ起動失敗. CRITICAL_ERROR: {e}")
                st.stop()
            
            hp_links = [] if get_hp else None
            representatives = [] if get_rep else None
            tel_numbers = [] if get_tel else None
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                total_rows = len(df)
                for index, row in df.iterrows():
                    office_name = row.iloc[0]
                    address = row.iloc[1]
                    
                    status_text.markdown(f"`[AI PROCESSING] ({index+1}/{total_rows})` ── Target: **{office_name}**")
                    
                    # 【戦略変更】検索キーワードに「代表」「TEL」を最初から組み込み、Googleの検索結果画面に情報を露出させる
                    query = f"{office_name} {address} 代表 TEL"
                    search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=ja"
                    
                    url_found = "見つかりませんでした"
                    rep_found = "見つかりませんでした"
                    tel_found = "見つかりませんでした"
                    
                    try:
                        driver.get(search_url)
                        # Google検索結果コンテナの出現を待つ
                        WebDriverWait(driver, 4).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.g, div.yuRUbf, #search"))
                        )
                        
                        # 1. ★【超高速＆確実化】個別HPへの移動を廃止し、Googleの検索結果テキストをそのまま丸ごと引っこ抜く！
                        search_page_text = driver.find_element(By.TAG_NAME, "body").text
                        
                        # 2. HPリンクのURLだけは検索結果のAタグからスマートに抽出
                        links = driver.find_elements(By.CSS_SELECTOR, "div.g a, div.yuRUbf a, a[data-ved]")
                        for link in links:
                            raw_url = link.get_attribute("href")
                            if raw_url and raw_url.startswith("http") and not any(x in raw_url for x in ["google.com", "youtube.com", "twitter.com", "facebook.com", "instagram.com", "map.yahoo"]):
                                url_found = raw_url
                                break
                                
                        # 3. ★【AI脳へ連携】Googleが要約したテキストから、代表名とTEL番号を完璧に推論させる
                        if get_rep or get_tel:
                            prompt = f"""
                            あなたはプロのデータ抽出AIです。提供されたGoogleの検索結果テキスト（スニペット情報）を分析し、ターゲットである「{office_name}」の「代表者名（個人の氏名のみ）」と「電話番号」を正確に特定してください。

                            【抽出ルール】
                            1. 「代表取締役」「所長」「代表税理士」「代表弁護士」「院長」「理事長」などの役職がついている人物の「氏名（漢字）」を特定してください。
                            ※重要：法人名、組織名、地名、メニュー名（例: 総合事務所、税理士法人、経営理念、札幌など）は、絶対に名前に含めないでください。人間の名前がわからない場合は「見つかりませんでした」としてください。
                            2. 電話番号は日本の正しい形式（例: 011-727-5303, 0120-951-761）を1つ特定してください。郵便番号やシリアルコードは除外してください。

                            【対象のGoogle検索結果テキスト】
                            {search_page_text[:15000]}

                            【出力フォーマット】
                            必ず以下の、キー名が半角英数字のJSON形式のみで返答してください。余計な説明文やマークダウン（```json など）は一切含めず、生データとしてパースできるようにしてください。
                            {{"representative": "ここに代表者の氏名", "tel": "ここに電話番号"}}
                            """
                            
                            response = model.generate_content(prompt)
                            ai_output = response.text.strip()
                            
                            if ai_output.startswith("```"):
                                ai_output = ai_output.replace("```json", "").replace("```", "").strip()
                            
                            # 安全なJSON展開
                            data_json = json.loads(ai_output)
                            if get_rep:
                                rep_found = data_json.get("representative", "見つかりませんでした")
                            if get_tel:
                                tel_found = data_json.get("tel", "見つかりませんでした")
                                
                    except Exception as e:
                        pass
                    
                    if get_hp: hp_links.append(url_found)
                    if get_rep: representatives.append(rep_found)
                    if get_tel: tel_numbers.append(tel_found)
                    
                    progress_bar.progress((index + 1) / total_rows)
                    time.sleep(4.5) # 無料枠のAPI制限を安全に回避するためのウエイト
                
                if get_hp: df['HPリンク'] = hp_links
                if get_rep: df['代表者名'] = representatives
                if get_tel: df['TEL番号'] = tel_numbers
                
                status_text.markdown("### 🟢 EXTRACTION COMPLETE. OUTPUT GENERATED BY AI.")
                st.dataframe(df)
                
                csv_string = df.to_csv(index=False, encoding='utf-8-sig')
                csv_bytes = csv_string.encode('utf-8-sig')
                
                st.download_button(
                    label="⚡ DOWNLOAD EXTRACTED PACK",
                    data=csv_bytes,
                    file_name="cyber_extracted_info.csv",
                    mime="text/csv"
                )
                
            finally:
                driver.quit()
