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
from webdriver_manager.chrome import ChromeDriverManager

# 画面のタイトル設定
st.title("🏛️ 事務所HPリンク自動抽出ツール")
st.write("A列に事務所名、B列に住所が入ったCSVファイルをアップロードしてください。広告を飛ばして1番上のURLを抽出します。")

# ファイルアップローダーの設置
uploaded_file = st.file_uploader("CSVファイルを選択してください", type=["csv"])

if uploaded_file is not None:
    # CSVの読み込み
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding='shift_jis')
        
    st.success("ファイルの読み込みに成功しました！")
    st.dataframe(df.head()) # 先頭を表示

    # 実行ボタン
    if st.button("URLの抽出を開始する"):
        
        # サーバー側でのブラウザ起動設定（画面なしモード）
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # サーバー環境用のドライバー自動設定
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        hp_links = []
        
        # プログレスバーの設置
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            total_rows = len(df)
            for index, row in df.iterrows():
                office_name = row.iloc[0]
                address = row.iloc[1]
                
                status_text.text(f"検索中 ({index+1}/{total_rows}): {office_name}")
                
                query = f"{office_name} {address} ホームページ"
                search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                
                try:
                    driver.get(search_url)
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "result"))
                    )
                    search_results = driver.find_elements(By.CLASS_NAME, "result")
                    
                    url_found = "見つかりませんでした"
                    for result in search_results:
                        class_attr = result.get_attribute("class")
                        if "ad" in class_attr or "badge" in class_attr:
                            continue # 広告スキップ
                        
                        link_element = result.find_element(By.CLASS_NAME, "result__a")
                        raw_url = link_element.get_attribute("href")
                        
                        if "uddg=" in raw_url:
                            from urllib.parse import parse_qs, urlparse
                            parsed = urlparse(raw_url)
                            queries = parse_qs(parsed.query)
                            if 'uddg' in queries:
                                url_found = queries['uddg'][0]
                                break
                        if raw_url.startswith("http"):
                            url_found = raw_url
                            break
                    hp_links.append(url_found)
                except:
                    hp_links.append("見つかりませんでした")
                
                # 進捗更新
                progress_bar.progress((index + 1) / total_rows)
                time.sleep(1.5) # サーバー負荷軽減
                
            # 結果を結合
            df['HPリンク'] = hp_links
            status_text.text("✨ 抽出が完了しました！")
            st.dataframe(df.head())
            
            # CSVダウンロードボタンの設置（Excel文字化け対策utf-8-sig）
            csv_data = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="加工済みCSVをダウンロード",
                data=csv_data,
                file_name="extracted_office_links.csv",
                mime="text/csv"
            )
            
        finally:
            driver.quit()