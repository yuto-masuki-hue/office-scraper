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
st.set_page_config(page_title="SYSTEM: AI SCOPER v4.5", layout="wide")

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
    div[data-testid="stTextInput"] label p, div[data-testid="stSelectbox"] label p {
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
    <h1>⚡ AI INFO SCOPER // CORE_SYSTEM v4.5</h1>
    <p style="color: #8fa0b0 !important; margin: 8px 0 0 0 !important; font-size: 0.9rem;">TARGET SYSTEM: HYBRID DEEP AI SCRAPER & REVERSE INTELLIGENCE ENGINE</p>
</div>
"""
st.html(header_html)

# =====================================================================
# 2. UIパーツ配置
# =====================================================================
gemini_key = st.text_input("🔑 ENTER GEMINI API KEY", type="password", help="Google AI Studioで取得した無料のキーを入力してください")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🛠️ EXTRACT TARGETS (抽出対象の選択)")
    get_hp = st.checkbox("🔗 HPリンク (URL)", value=True)
    get_office = st.checkbox("🏢 所属事務所名 (名前から推測)", value=False)
    get_rep = st.checkbox("👤 代表者名 (HP内から巡回)", value=True)
    get_tel = st.checkbox("📞 TEL番号 (HP内から巡回)", value=True)
    st.markdown("---")
    st.markdown("※ 分割処理・プレビュー自動上書きシステム稼働中。")

with col2:
    st.markdown("### 📥 INGEST FILE (CSVファイル入力)")
    uploaded_file = st.file_uploader("Drop Target CSV File here", type=["csv"])

# =====================================================================
# 3. メインロジック
# =====================================================================
if uploaded_file is not None:
    df = None
    encodings_to_try = ['utf-8-sig', 'utf-8', 'cp932', 'shift_jis']
    
    for enc in encodings_to_try:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=enc)
            break
        except Exception:
            continue
            
    if df is None:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='cp932', errors='ignore')
        except Exception as csv_e:
            st.error(f"SYSTEM_CRITICAL: CSVデコード完全失敗。ファイルを修復してください: {csv_e}")
            st.stop()
        
    st.success("🤖 TARGET DATA LOADED.")
    
    # ★【新機能】どの列を検索キーワードとして使うかの動的セレクター
    csv_columns = list(df.columns)
    st.markdown("### 🔍 SEARCH SOURCE SETTING (検索ソース列の指定)")
    
    col_src1, col_src2 = st.columns(2)
    with col_src1:
        primary_search_col = st.selectbox("第一検索ソース（事務所名、または個人名などが入った列）", options=csv_columns, index=0)
    with col_src2:
        # 住所列がない単一キーワード検索の場合を考慮し「使用しない」の選択肢を用意
        secondary_options = ["(使用しない)"] + csv_columns
        secondary_search_col = st.selectbox("第二検索ソース（住所や地域などの掛け合わせ列）", options=secondary_options, index=min(1, len(secondary_options)-1))

    # 新規出力列の初期化マウント
    if get_hp and 'HPリンク' not in df.columns: df['HPリンク'] = "未処理"
    if get_office and '所属事務所名' not in df.columns: df['所属事務所名'] = "未処理"
    if get_rep and '代表者名' not in df.columns: df['代表者名'] = "未処理"
    if get_tel and 'TEL番号' not in df.columns: df['TEL番号'] = "未処理"
    
    # 分割処理用の範囲指定スライダー
    total_records = len(df)
    st.markdown(f"### 🎛️ RANGE SELECTOR (総件数: {total_records}件)")
    start_row, end_row = st.slider(
        "処理する行の範囲を選択してください",
        min_value=1,
        max_value=total_records,
        value=(1, min(300, total_records)),
        step=1
    )
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    st.markdown("### 📊 LIVE DATA PREVIEW (リアルタイム更新中)")
    preview_table_holder = st.empty()
    preview_table_holder.dataframe(df.iloc[start_row-1:end_row])

    if not gemini_key:
        st.warning("⚠️ 処理を開始するには、上に GEMINI API KEY を入力してください。")
    elif not (get_hp or get_office or get_rep or get_tel):
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
            
            try:
                sub_range = range(start_row - 1, end_row)
                total_sub_rows = len(sub_range)
                
                for loop_idx, index in enumerate(sub_range):
                    row = df.iloc[index]
                    
                    # ★【指定された列の値】をもとに検索キーワードを動的に合体
                    val1 = str(row[primary_search_col]).strip()
                    val2 = str(row[secondary_search_col]).strip() if secondary_search_col != "(使用しない)" else ""
                    
                    search_keyword = f"{val1} {val2}".strip()
                    
                    status_text.markdown(f"`[PROCESSING] ({loop_idx+1}/{total_sub_rows})` ── 全体No.{index+1}: **{search_keyword}**")
                    
                    query = search_keyword
                    search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                    
                    url_found = "見つかりませんでした"
                    office_found = "見つかりませんでした"
                    rep_found = "見つかりませんでした"
                    tel_found = "見つかりませんでした"
                    
                    # 1. 検索エンジンから本物の公式HPのみをスカウト
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
                    
                    # 2. 階層深掘りテキスト抽出 & AI複合推論
                    if url_found != "見つかりませんでした" and (get_office or get_rep or get_tel):
                        try:
                            try:
                                driver.get(url_found)
                                time.sleep(2.0)
                            except:
                                pass
                            
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
                                    sub_text = driver.execute_script("return document.body.innerText;")
                                    combined_text += f"\n --- SUB PAGE ({page}) --- \n {sub_text} \n"
                                except:
                                    pass
                            
                            truncated_text = combined_text[:30000]
                            
                            # プロンプト：事務所名の逆引き推測ルールを追加
                            prompt = f"""
                            以下のウェブサイトから抽出された複数ページのテキスト情報を統合的に読み解き、指定された情報を特定して箇条書きの形式のみで出力してください。

                            検索のヒント・手がかりとなったキーワード: {search_keyword}

                            【超厳格抽出ルール】
                            1. [OFFICE] このサイトを運営している、またはキーワードの人物が所属している「正式な事務所名・法人名（例: 税理士法人エルム会計、〇〇法律事務所など）」を特定してください。
                            2. [NAME] 「代表取締役」「所長」「代表税理士」「代表弁護士」などの役職がついている、組織のトップである人物の「個人の氏名（漢字）」を特定してください。
                            ※会社名や単語（例: 総合事務所、経営理念など）は、絶対にNAME（代表者名）として出力せず、人間の名前のみを抜き出してください。
                            3. [TEL] 電話番号は日本の正しい形式（例: 011-727-5303）を1つ特定してください。
                            4. 情報がどこにも見当たらない項目は「見つかりませんでした」としてください。

                            【対象Webサイト統合テキスト】
                            {truncated_text}

                            【出力フォーマット】
                            余計な前置きや説明は一切省き、必ず以下の3行の箇条書きの形「だけ」で回答してください。
                            OFFICE: (ここに所属事務所名・法人名)
                            NAME: (ここに代表者氏名)
                            TEL: (ここに電話番号)
                            """
                            
                            response = model.generate_content(prompt)
                            ai_output = response.text.strip()
                            
                            for line in ai_output.splitlines():
                                line_str = line.strip()
                                if line_str.startswith("OFFICE:"):
                                    office_found = line_str.replace("OFFICE:", "").strip()
                                elif line_str.startswith("NAME:"):
                                    rep_found = line_str.replace("NAME:", "").strip()
                                elif line_str.startswith("TEL:"):
                                    tel_found = line_str.replace("TEL:", "").strip()
                                
                        except Exception as e:
                            pass
                    
                    # 該当行へリアルタイム書き込み
                    if get_hp: df.at[index, 'HPリンク'] = url_found
                    if get_office: df.at[index, '所属事務所名'] = office_found
                    if get_rep: df.at[index, '代表者名'] = rep_found
                    if get_tel: df.at[index, 'TEL番号'] = tel_found
                    
                    # プレビューテーブルをリアルタイム上書き更新
                    preview_table_holder.dataframe(df.iloc[start_row-1:end_row])
                    progress_bar.progress((loop_idx + 1) / total_sub_rows)
                    time.sleep(4.5)
                
                status_text.markdown(f"### 🟢 RANGE ({start_row} - {end_row}) COMPLETE. DATA INTEGRATED.")
                
                final_csv_bytes = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="⚡ DOWNLOAD FULL/INTEGRATED CSV PACK",
                    data=final_csv_bytes,
                    file_name="cyber_extracted_info_integrated.csv",
                    mime="text/csv",
                    key="final_btn"
                )
                
            finally:
                driver.quit()
