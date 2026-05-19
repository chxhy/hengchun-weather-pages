import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

def get_stock_data():
    """抓取台積電 (2330.TW) 今天的 5 分鐘 K 線資料"""
    print("正在獲取台積電 5 分鐘 K 線資料...")
    # interval='5m' 代表 5 分鐘線, period='1d' 代表最近一天
    # 使用 group_by='column' 確保結構較單純
    df = yf.download("2330.TW", period="1d", interval="5m", auto_adjust=True)
    return df

def get_market_summary(date_str):
    """存取證交所 API 獲取當日大盤統計"""
    print(f"正在從證交所獲取 {date_str} 大盤統計...")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={date_str}&type=MS"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data.get('stat') == 'OK':
            summary_list = data.get('data1', [])
            return summary_list
        else:
            return "今日證交所尚未更新資料或為非交易日。"
    except Exception as e:
        return f"無法獲取證交所資料: {str(e)}"

def analyze_trend(df):
    """簡單的收盤走勢分析"""
    if df is None or df.empty:
        return "今日無交易資料（可能為非交易日或開盤前）。"
    
    try:
        # 修正：使用 .iloc[0] 並加上 .item() 或確保轉為浮點數，避免 Series 歧義
        # 針對 yfinance 新版本，我們取 Close 欄位的第一個與最後一個值
        close_prices = df['Close'].values # 轉為 numpy array 避開索引問題
        first_price = float(close_prices[0])
        last_price = float(close_prices[-1])
        
        diff = last_price - first_price
        change_pct = (diff / first_price) * 100
        
        if diff > 0:
            status = f"呈【上升趨勢】，較開盤上漲了 {diff:.2f} 元 ({change_pct:.2f}%)。"
        elif diff < 0:
            status = f"呈【下跌趨勢】，較開盤下跌了 {abs(diff):.2f} 元 ({abs(change_pct):.2f}%)。"
        else:
            status = "今日走勢平穩，最後成交價與開盤價持平。"
        return status
    except Exception as e:
        return f"分析時發生錯誤: {str(e)}"

def generate_html_report(date_today, stock_df, market_info):
    """生成 HTML 報告"""
    filename = f"{date_today}_result.html"
    
    trend_analysis = analyze_trend(stock_df)
    
    # 處理表格顯示，如果沒資料就顯示提示
    if not stock_df.empty:
        stock_table = stock_df.tail(10).to_html(classes='table')
    else:
        stock_table = "<p>無 K 線資料</p>"
    
    market_text = ""
    if isinstance(market_info, list):
        for item in market_info:
            market_text += f"<li>{item[0]}: {item[2]}</li>"
    else:
        market_text = f"<li>{market_info}</li>"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="UTF-8">
        <title>{date_today} 股市匯整報告</title>
        <style>
            body {{ font-family: "Microsoft JhengHei", Arial, sans-serif; margin: 40px; background-color: #f4f4f9; }}
            .container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
            h2 {{ color: #007bff; margin-top: 30px; }}
            .analysis {{ background: #e7f3ff; padding: 15px; border-left: 5px solid #007bff; margin: 20px 0; font-size: 1.1em; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 10px; font-size: 0.9em; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: right; }}
            th {{ background-color: #f2f2f2; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>股市統計報告 - {date_today}</h1>
            
            <h2>一、台積電 (2330.TW) 當日走勢分析</h2>
            <div class="analysis">
                <strong>今日分析結果：</strong> {trend_analysis}
            </div>
            
            <h2>二、大盤統計資訊 (證交所)</h2>
            <ul>
                {market_text}
            </ul>
            
            <h2>三、台積電最新 5 分鐘 K 線明細 (僅顯示末10筆)</h2>
            <div style="overflow-x:auto;">
                {stock_table}
            </div>
            
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                報告產生時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>
    </body>
    </html>
    """
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"報告已成功生成：{filename}")

if __name__ == "__main__":
    # 1. 設定日期
    today_date = datetime.now().strftime('%Y%m%d')
    
    # 2. 獲取台積電資料
    tsmc_df = get_stock_data()
    
    # 3. 獲取大盤統計
    market_data = get_market_summary(today_date)
    
    # 4. 彙整並生成 HTML
    generate_html_report(today_date, tsmc_df, market_data)
