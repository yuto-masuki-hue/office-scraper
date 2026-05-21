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
    <p style="color: #8fa0b0 !important; margin: 8px 0 0 0 !important; font-size: 0.9rem;">TARGET SYSTEM: HYBRID DEEP AI SCRAPER ENGINE (Gemini 1.5 Pro)</p>
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
    get_rep = st.checkbox("👤 代表者名 (AI 階層巡回)", value=True)
    get_tel = st.checkbox("📞 TEL番号 (AI 階層巡回)", value=True)
    st.markdown("---")
    st.markdown("※ 自社サイト内の「概要・挨拶」下層ページも自動巡回してAIに一括連携します。")

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
            model = genai.GenerativeModel(model_name="gemini-1.5-pro")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
            
            chrome_options.binary_location = "/usr/bin/chromium"
            service = Service(executable_path="/usr/bin/chromedriver")
            
            try:
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.set_page_load_timeout(12)
                driver.implicitly_wait(4)
            except Exception as e:
                st.error(f"SYSTEM_CRITICAL: ブラウザ起動失敗. CRITICAL_ERROR: {e}")
                st.stop()
            
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
                    
                    status_text.markdown(f"`[PROCESSING] ({index+1}/{total_rows})` ── Target: **{office_name}**")
                    
                    query = f"{office_name} {address}"
                    search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                    
                    url_found = "見つかりませんでした"
                    rep_found = "見つかりませんでした"
                    tel_found = "見つかりませんでした"
                    
                    try:
                        driver.get(search_url)
                        WebDriverWait(driver, 4).until(
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
                                
                                clean_url = raw_url
                                if "uddg=" in raw_url:
                                    from urllib.parse import parse_qs, urlparse
                                    parsed = urlparse(raw_url)
                                    queries = parse_qs(parsed.query)
                                    if 'uddg' in queries:
                                        clean_url = queries['uddg'][0]
                                
                                if clean_url.startswith("http"):
                                    if any(p in clean_url for p in [
                                        "kaikei-home.com", "ezeirisi.jp", "map.yahoo.co.jp", "zeiri4.com", 
                                        "google.com", "youtube.com", "twitter.com", "facebook.com", "instagram.com",
                                        "houjin.jp", "i-sozoku.com", "mapion.co.jp"
                                    ]):
                                        continue
                                        
                                    url_found = clean_url
                                    break
                            except:
                                pass
                    except:
                        pass
                    
                    # 2. 【大改修】JavaScript経由でinnerTextを安全・確実に100%引き出す
                    if url_found != "見つかりませんでした" and (get_rep or get_tel):
                        try:
                            try:
                                driver.get(url_found)
                                time.sleep(2.0) # 読み込み待ちを2秒に固定
                            except:
                                pass
                            
                            # ★【修正】空文字バグを100%防ぐため、JavaScriptでブラウザ内部の全innerTextを強制ダンプ
                            top_text = driver.execute_script("return document.body.innerText;")
                            combined_text = f"--- TOP PAGE --- \n {top_text} \n"
                            
                            target_pages = []
                            links = driver.find_elements(By.TAG_NAME, "a")
                            for link in links:
                                try:
                                    link_text = link.text.strip()
                                    link_url = link.get_attribute("href")
                                    if any(k in link_text for k in ["概要", "挨拶", "プロフィール", "紹介", "アクセス", "案内", "組織", "基本", "会社"]):
                                        if link_url and link_url.startswith("http") and link_url != url_found:
                                            target_pages.append(link_url)
                                except:
                                    pass
                            
                            target_pages = list(dict.fromkeys(target_pages))[:3]
                            for page in target_pages:
                                try:
                                    driver.get(page)
                                    time.sleep(1.5)
                                    # 下層ページも同様にJavaScript経由で確実に文字を回収
                                    sub_text = driver.execute_script("return document.body.innerText;")
                                    combined_text += f"\n --- SUB PAGE ({page}) --- \n {sub_text} \n"
                                except:
                                    pass
                            
                            truncated_text = combined_text[:30000]
                            
                            prompt = f"""
                            以下のウェブサイトから抽出された複数ページのテキスト情報（トップページおよび概要・挨拶等の下層ページ）を統合的に読み解き、この組織の「代表者名（個人の氏名のみ）」と「電話番号」を特定して指定の形式で出力してください。

                            【超厳格ルール】
                            1. 「代表取締役」「所長」「代表税理士」「代表弁護士」「院長」「理事長」などの役職がついている、組織のトップである人物の「個人の氏名（漢字）」を特定してください。
                            ※「総合事務所」や「税理士法人」のような法人名・組織名・メニュー単語は、絶対に代表者名として出力せず、人間の名前のみを抜き出してください。
                            2. 電話番号は日本の正しい形式（例: 011-727-5303）を1つ特定してください。
                            3. 情報がどこにも見当たらない場合のみ、「見つかりませんでした」としてください。

                            【対象Webサイト統合テキスト】
                            {truncated_text}

                            【出力フォーマット】
                            余計な前置きや説明は一切省き、必ず以下の3行の箇取りの形「だけ」で回答してください。
                            URL: (無視してください)
                            NAME: (ここに代表者氏名)
                            TEL: (ここに電話番号)
                            """
                            
                            response = model.generate_content(prompt)
                            ai_output = response.text.strip()
                            
                            for line in ai_output.splitlines():
                                line_str = line.strip()
                                if line_str.startswith("NAME:"):
                                    rep_found = line_str.replace("NAME:", "").strip()
                                elif line_str.startswith("TEL:"):
                                    tel_found = line_str.replace("TEL:", "").strip()
                                
                        except Exception as e:
                            pass
                    
                    if get_hp: hp_links.append(url_found)
                    if get_rep: representatives.append(rep_found)
                    if get_tel: tel_numbers.append(tel_found)
                    
                    progress_bar.progress((index + 1) / total_rows)
                    time.sleep(4.5)
                
                if get_hp: df['HPリンク'] = hp_links
                if get_rep: df['代表者名'] = representatives
                if get_tel: df['TEL番号'] = tel_numbers
                
                status_text.markdown("### 🟢 EXTRACTION COMPLETE. OUTPUT GENERATED BY HYBRID ENGINE.")
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
