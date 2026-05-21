import re
import time
import urllib.parse
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
st.set_page_config(page_title="SYSTEM: INFO SCOPER v2.0", layout="wide")

cyber_css = """
<style>
    .stApp {
        background-color: #0d0f12 !important;
        color: #00ffcc !important;
        font-family: 'Courier New', Courier, monospace !important;
    }
    h1 {
        color: #ff0055 !important;
        text-shadow: 0 0 10px #ff0055, 0 0 20px #ff0055;
        border-bottom: 2px solid #00ffcc;
        padding-bottom: 10px;
        font-weight: bold !important;
    }
    .stMarkdown p {
        color: #8fa0b0 !important;
    }
    div[data-testid="stCheckbox"] {
        background-color: #1a1f26;
        padding: 8px 15px;
        border-radius: 5px;
        border: 1px solid #00ffcc;
        box-shadow: 0 0 5px rgba(0, 255, 204, 0.2);
        margin-bottom: 5px;
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
# 1. UIパーツ配置
# =====================================================================
st.title("⚡ INFO EXTRACTOR // CORE_SYSTEM v2.0")
st.write("TARGET SYSTEM: DATA INGESTION & INTELLIGENCE EXTRACTOR")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🛠️ EXTRACT TARGETS (抽出対象の選択)")
    get_hp = st.checkbox("🔗 HPリンク (URL)", value=True)
    get_rep = st.checkbox("👤 代表者名 (REPRESENTATIVE)", value=True)
    get_tel = st.checkbox("📞 TEL番号 (TELEPHONE)", value=True)
    
    st.markdown("---")
    st.markdown("※ 最低1つ以上のモジュールを有効化してください。")

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
        
    st.success("🤖 TARGET DATA LOADED SUCCESSFULLY.")
    st.dataframe(df.head(3))

    if not (get_hp or get_rep or get_tel):
        st.warning("⚠️ エラー: 少なくとも1つの抽出対象を選択してください。")
    else:
        if st.button("▶ EXECUTE SYSTEM EXTRACTION"):
            
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
                    
                    status_text.markdown(f"`[PROCESSING] ({index+1}/{total_rows})` ── Target: **{office_name}**")
                    
                    # 1. 検索エンジンから本物のHPリンク（URL）を抽出
                    query = f"{office_name} {address}"
                    search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                    
                    url_found = "見つかりませんでした"
                    rep_found = "見つかりませんでした"
                    tel_found = "見つかりませんでした"
                    
                    try:
                        driver.get(search_url)
                        WebDriverWait(driver, 5).until(
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
                    
                    # 2. ターゲットサイトのディープスキャン（改修版）
                    if url_found != "見つかりませんでした" and (get_rep or get_tel):
                        try:
                            driver.get(url_found)
                            time.sleep(2.0)  # 遅延読み込み（JS対応）のため少し長めに待機
                            
                            target_pages = [url_found]
                            
                            # 下層ページのリンクを全スキャン
                            links = driver.find_elements(By.TAG_NAME, "a")
                            for link in links:
                                try:
                                    link_text = link.text.strip()
                                    link_url = link.get_attribute("href")
                                    if any(k in link_text for k in ["概要", "挨拶", "プロフィール", "紹介", "アクセス", "案内", "組織", "基本", "会社"]):
                                        if link_url and link_url.startswith("http") and link_url not in target_pages:
                                            target_pages.append(link_url)
                                except:
                                    pass
                            
                            target_pages = list(dict.fromkeys(target_pages))[:4] # 最大4ページまで追跡拡張
                            
                            for page in target_pages:
                                if page != url_found:
                                    driver.get(page)
                                    time.sleep(1.5) # ページ遷移後もしっかり待機
                                
                                # 【ココが重要】HTMLタグも含めた生データを引っぺがし、余分なHTMLコードだけHTMLタグ除去
                                raw_html = driver.execute_script("return document.body.innerHTML;")
                                # HTMLのタグを除去しつつ、改行やタブ、連続する空白を極限まで圧縮して1列のプレーンテキストにする
                                clean_text = re.sub(r'<[^>]+>', ' ', raw_html)
                                clean_text = re.sub(r'\s+', ' ', clean_text)
                                
                                # ── 電話番号の徹底抽出 ──
                                if get_tel and tel_found == "見つかりませんでした":
                                    # 市外局番やハイフンのあらゆる組み合わせに対応
                                    tel_match = re.search(r'(?:TEL|tel|電話番号|🕿|☎)?\s*[:：\s]*\(?(\d{2,5})\)?[-ー\s]?(\d{1,4})[-ー\s]?(\d{3,4})', clean_text)
                                    if tel_match:
                                        # 綺麗にハイフンで成形して格納
                                        tel_found = f"{tel_match.group(1)}-{tel_match.group(2)}-{tel_match.group(3)}"
                                
                                # ── 代表者名の徹底抽出 ──
                                if get_rep and rep_found == "見つかりませんでした":
                                    # 改行やスペースが圧縮されたテキストに対して機能する、最新の正規表現パターン
                                    rep_patterns = [
                                        r'(?:代表取締役|代表社員|代表弁護士|代表税理士|代表司法書士|代表行政書士|所長|理事長|院長|代表|共同代表)\s*[:：]?\s*([一-龠]{2,4})\s*([一-龠]{2,4})?',
                                        r'([一-龠]{2,4})\s*([一-龠]{2,4})?\s*(?:代表取締役|代表社員|代表弁護士|代表税理士|所長|理事長|院長)',
                                        r'(?:代表者|氏名|名\s*前)\s*[:：]?\s*([一-龠]{2,4})\s*([一-龠]{2,4})?'
                                    ]
                                    for pattern in rep_patterns:
                                        rep_match = re.search(pattern, clean_text)
                                        if rep_match:
                                            last_name = rep_match.group(1)
                                            # 苗字と名前の間のスペースを埋める
                                            first_name = rep_match.group(2) if rep_match.group(2) else ""
                                            full_name = (last_name + first_name).strip()
                                            
                                            # 役職名自体を誤検知（例: 代表取締役 所長 のような連続）するのを防ぐガード
                                            if full_name not in ["代表取締役", "代表社員", "代表弁護士", "代表税理士", "所長", "理事長", "院長"]:
                                                rep_found = full_name
                                                break
                                                
                                # 情報が揃ったらこの事務所の巡回は終了
                                if (not get_tel or tel_found != "見つかりませんでした") and (not get_rep or rep_found != "見つかりませんでした"):
                                    break
                                    
                        except:
                            pass
                    
                    if get_hp: hp_links.append(url_found)
                    if get_rep: representatives.append(rep_found)
                    if get_tel: tel_numbers.append(tel_found)
                    
                    progress_bar.progress((index + 1) / total_rows)
                    time.sleep(1.0)
                
                if get_hp: df['HPリンク'] = hp_links
                if get_rep: df['代表者名'] = representatives
                if get_tel: df['TEL番号'] = tel_numbers
                
                status_text.markdown("### 🟢 EXTRACTION COMPLETE. OUTPUT GENERATED.")
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
