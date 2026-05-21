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
# 0. いかついサイバーパンク・ダークUIのカスタム設定 (安全なHTML注入)
# =====================================================================
st.set_page_config(page_title="SYSTEM: AI SCOPER v3.0", layout="wide")

cyber_css = """
<style>
    /* 全体の背景とテキストカラー */
    .stApp {
        background-color: #0d0f12 !important;
        color: #00ffcc !important;
        font-family: 'Courier New', Courier, monospace !important;
    }
    /* メインタイトル */
    h1 {
        color: #ff0055 !important;
        text-shadow: 0 0 10px #ff0055, 0 0 20px #ff0055;
        border-bottom: 2px solid #00ffcc;
        padding-bottom: 10px;
        font-weight: bold !important;
    }
    /* サブテキスト・汎用ラベル文字をくっきり白・明るいグレー化 */
    .stMarkdown p, label, .stSlider p {
        color: #e2e8f0 !important;
    }
    /* ★【修正】API KEY入力欄のラベル文字色を鮮やかに */
    div[data-testid="stTextInput"] label p {
        color: #00ffcc !important;
        font-weight: bold !important;
        text-shadow: 0 0 5px rgba(0, 255, 204, 0.5);
    }
    /* ★【修正】API KEYの入力ボックス本体の背景と入力文字色 */
    div[data-testid="stTextInput"] input {
        background-color: #1a1f26 !important;
        color: #ffffff !important;
        border: 1px solid #00ffcc !important;
    }
    /* ★【修正】チェックボックスカードの文字色をハッキリした白に強制上書き */
    div[data-testid="stCheckbox"] {
        background-color: #1a1f26;
        padding: 8px 15px;
        border-radius: 5px;
        border: 1px solid #00ffcc;
        box-shadow: 0 0 5px rgba(0, 255, 204, 0.2);
        margin-bottom: 5px;
    }
    div[data-testid="stCheckbox"] label span p {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    /* ボタンをいかつくネオン化 */
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
    /* データフレームのサイバー化 */
    .stDataFrame {
        border: 1px solid #ff0055 !important;
        box-shadow: 0 0 10px rgba(255, 0, 85, 0.15);
    }
</style>
"""
st.html(cyber_css)

# =====================================================================
# 1. UIパーツ配置
# =====================================================================
st.title("⚡ AI INFO SCOPER // CORE_SYSTEM v3.0")
st.write("TARGET SYSTEM: AI-POWERED INTELLIGENCE EXTRACTOR (Gemini 2.5 Flash)")

# 画面にAPIキーの入力欄を設置
gemini_key = st.text_input("🔑 ENTER GEMINI API KEY", type="password", help="Google AI Studioで取得した無料のキーを入力してください")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🛠️ EXTRACT TARGETS (抽出対象)")
    get_hp = st.checkbox("🔗 HPリンク (URL)", value=True)
    get_rep = st.checkbox("👤 代表者名 (AI 推論)", value=True)
    get_tel = st.checkbox("📞 TEL番号 (AI 推論)", value=True)
    st.markdown("---")
    st.markdown("※ 無料APIキーの制限を回避するため、4秒に1件のペースで安全に推論を回します。")

with col2:
    st.markdown("### 📥 INGEST FILE (CSVファイル入力)")
    uploaded_file = st.file_uploader("Drop Target CSV File here", type=["csv"])

# =====================================================================
# 2. メインロジック
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
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            chrome_options.binary_location = "/usr/bin/chromium"
            service = Service(executable_path="/usr/bin/chromedriver")
            
            try:
                driver = webdriver.Chrome(service=service, options=chrome_options)
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
                    
                    query = f"{office_name} {address}"
                    search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                    
                    url_found = "見つかりませんでした"
                    rep_found = "見つかりませんでした"
                    tel_found = "見つかりませんでした"
                    
                    try:
                        driver.get(search_url)
                        WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "result"))
                        )
                        search_results = driver.find_elements(By.CLASS_NAME, "result")
                        
                        for result in search_results:
                            class_attr = result.get_attribute("class")
                            if "ad" in class_attr or "badge" in class_attr:
                                continue
                            try:
                                link_element = result.find_element(By.CLASS_NAME, "result__a")
                                raw_url = link_element.get_attribute("href")
                                if "uddg=" in raw_url:
                                    from urllib.parse import parse_qs, urlparse
                                    parsed = urlparse(raw_url)
                                    queries = parse_qs(parsed.query)
                                    if 'uddg' in queries:
                                        url_found = queries['uddg'][0]
                                elif raw_url.startswith("http"):
                                    url_found = raw_url
                                break
                            except:
                                pass
                    except:
                        pass
                    
                    if url_found != "見つかりませんでした" and (get_rep or get_tel):
                        try:
                            driver.get(url_found)
                            time.sleep(1.2)
                            
                            raw_html = driver.execute_script("return document.body.innerText;")
                            truncated_text = raw_html[:30000]
                            
                            prompt = f"""
                            あなたは優秀なデータ抽出AIです。提供されたウェブサイトのテキスト情報を読み、この事務所や組織の「代表者名（個人の氏名のみ）」と「電話番号（固定電話や代表電話など）」を注意深く推論して見つけ出してください。

                            【抽出ルール】
                            1. 「代表取締役」「所長」「代表税理士」「代表弁護士」「院長」などの役職がついている人物の「氏名（漢字）」を特定してください。「総合事務所」や「税理士法人」のような組織名は絶対に名 outreach に含めず、個人の名前のみを抽出してください。
                            2. 電話番号は日本の正しい電話番号（例: 03-XXXX-XXXX, 0120-XXX-XXX）を1つ特定してください。郵便番号やシリアルコードは絶対に除外してください。
                            3. 情報が見つからない場合は、必ず「見つかりませんでした」としてください。

                            【対象テキスト】
                            {truncated_text}

                            【出力フォーマット】
                            必ず以下の、キー名が半角英数字のJSON形式のみで返答してください。余計な説明文やマークダウン（```json など）は一切含めず、生データとしてパースできるようにしてください。
                            {{"representative": "ここに代表者の氏名", "tel": "ここに電話番号"}}
                            """
                            
                            response = model.generate_content(prompt)
                            ai_output = response.text.strip()
                            
                            if ai_output.startswith("```"):
                                ai_output = ai_output.replace("```json", "").replace("```", "").strip()
                            
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
                    time.sleep(4.0)
                
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
