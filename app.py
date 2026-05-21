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
# 0. 画像リファレンス準拠：ウォーム＆クリーンな北欧ニュアンスUI (CSS調整)
# =====================================================================
st.set_page_config(page_title="Data Extractor Pro", layout="wide")

soft_light_css = """
<style>
    /* 全体の背景（優しいライトアイボリー） */
    .stApp {
        background-color: #edeae6 !important;
        color: #3c3c3c !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    
    /* メインタイトル */
    h1 {
        color: #1e293b !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        padding-bottom: 5px;
    }
    
    /* サブテキスト */
    .stMarkdown p {
        color: #64748b !important;
    }

    /* チェックボックスを縦型カプセルカードに大改造 */
    div[data-testid="stCheckbox"] {
        background-color: #f8f6f2;
        border-radius: 30px !important; /* 丸みのあるカプセル形状 */
        padding: 25px 15px !important;
        text-align: center;
        border: 2px solid transparent;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        transition: all 0.25s ease;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    /* 各カプセル個別のニュアンスカラー枠線（ホバー時） */
    div[data-testid="stCheckbox"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.06);
        background-color: #ffffff;
    }

    /* Streamlit標準のチェックボックス位置調整 */
    div[data-testid="stCheckbox"] label {
        justify-content: center;
        font-weight: 600 !important;
        color: #475569 !important;
    }

    /* アップローダーエリアのカスタム */
    div[data-testid="stFileUploader"] {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 20px;
        border: 2px dashed #cbd5e1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
    }

    /* メイン実行ボタン（あたたかみのあるマスタードオレンジ） */
    div.stButton > button:first-child {
        background-color: #ffb733 !important;
        color: #1e293b !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 14px 30px;
        font-weight: 700;
        font-size: 1.1rem;
        width: 100%;
        box-shadow: 0 4px 12px rgba(255, 183, 51, 0.3);
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #ffa500 !important;
        transform: scale(1.01);
        box-shadow: 0 6px 16px rgba(255, 165, 0, 0.4);
    }

    /* ダウンロードボタン（落ち着いたアースカラー） */
    .download-wrapper button {
        background-color: #6b7280 !important;
        color: #ffffff !important;
        border-radius: 20px !important;
    }

    /* データフレームのクリーン化 */
    .stDataFrame {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.02);
    }
</style>
"""
st.html(soft_light_css)

# =====================================================================
# 1. UIパーツ配置
# =====================================================================
st.title("☀️ 事務所情報一括インテリジェンス・エクスプローラー")
st.write("CSVデータをインプットし、WEB上の公開情報から必要な項目をバックグラウンドで自動集計します。")

st.markdown("### 🛠️ 抽出項目の選択（カプセルをタップしてON/OFF）")

# 画像のような横並びの美しいカードレイアウトを作成
capsule_col1, capsule_col2, capsule_col3 = st.columns(3)

with capsule_col1:
    # マスタード系
    st.markdown("<div style='text-align:center; font-size:2rem; margin-bottom:-15px;'>🔗</div>", unsafe_html=True)
    get_hp = st.checkbox("HPリンク (URL)", value=True, key="chk_hp")

with capsule_col2:
    # テラコッタ・サーモン系
    st.markdown("<div style='text-align:center; font-size:2rem; margin-bottom:-15px;'>👤</div>", unsafe_html=True)
    get_rep = st.checkbox("代表者名", value=True, key="chk_rep")

with capsule_col3:
    # アースグリーン系
    st.markdown("<div style='text-align:center; font-size:2rem; margin-bottom:-15px;'>📞</div>", unsafe_html=True)
    get_tel = st.checkbox("TEL番号", value=True, key="chk_tel")

st.markdown("---")

col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("### 📥 ファイル読み込み")
    uploaded_file = st.file_uploader("対象のCSVファイルをここにドラッグ＆ドロップしてください", type=["csv"])

with col_right:
    st.markdown("### ⚙️ システム実行")
    st.write("設定完了後、下のボタンを押してください。")
    execute_ready = uploaded_file is not None and (get_hp or get_rep or get_tel)
    
    # 状態ガード付きボタン
    if execute_ready:
        button_clicked = st.button("▶ プロジェクトを開始する (BEGIN)")
    else:
        st.button("ファイルを選択してください", disabled=True)
        button_clicked = False

# =====================================================================
# 2. メインロジック
# =====================================================================
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding='shift_jis')
        
    st.success("データの読み込みが完了しました。")
    st.dataframe(df.head(3))

    if button_clicked:
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
            st.error(f"ブラウザの初期化に失敗しました。エラー詳細: {e}")
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
                
                status_text.markdown(f"🔄 データを抽出中 ({index+1}/{total_rows}) ── 対象: **{office_name}**")
                
                keywords = []
                if get_rep: keywords.append("代表")
                if get_tel: keywords.append("TEL")
                if get_hp and not keywords: keywords.append("ホームページ")
                
                query = f"{office_name} {address} " + " ".join(keywords)
                search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                
                url_found = "見つかりませんでした" if get_hp else None
                rep_found = "見つかりませんでした" if get_rep else None
                tel_found = "見つかりませんでした" if get_tel else None
                
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
                        
                        if get_hp and url_found == "見つかりませんでした":
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
                            except:
                                pass
                        
                        if get_tel or get_rep:
                            try:
                                snippet_text = result.find_element(By.CLASS_NAME, "result__snippet").text
                                
                                if get_tel and tel_found == "見つかりませんでした":
                                    tel_match = re.search(r'\(?\d{2,5}\)?[-ー\s]?\d{1,4}[-ー\s]?\d{3,4}', snippet_text)
                                    if tel_match:
                                        tel_found = tel_match.group()
                                
                                if get_rep and rep_found == "見つかりませんでした":
                                    rep_match = re.search(r'(?:代表|所長|代表社員|理事長|院長)(?:：|:\s*|明氏)?([一-龠]{2,4})', snippet_text)
                                    if rep_match:
                                        rep_found = rep_match.group(1)
                            except:
                                pass
                                
                except:
                    pass
                
                if get_hp: hp_links.append(url_found)
                if get_rep: representatives.append(rep_found)
                if get_tel: tel_numbers.append(tel_found)
                
                progress_bar.progress((index + 1) / total_rows)
                time.sleep(1.2)
            
            if get_hp: df['HPリンク'] = hp_links
            if get_rep: df['代表者名'] = representatives
            if get_tel: df['TEL番号'] = tel_numbers
            
            status_text.markdown("### 🟢 情報の抽出が完了しました。")
            st.dataframe(df)
            
            csv_string = df.to_csv(index=False, encoding='utf-8-sig')
            csv_bytes = csv_string.encode('utf-8-sig')
            
            # ラッパーを噛ませてスタイル適用
            st.markdown('<div class="download-wrapper">', unsafe_html=True)
            st.download_button(
                label="📥 抽出完了データをダウンロード (CSV)",
                data=csv_bytes,
                file_name="extracted_office_info.csv",
                mime="text/csv"
            )
            st.markdown('</div>', unsafe_html=True)
            
        finally:
            driver.quit()
