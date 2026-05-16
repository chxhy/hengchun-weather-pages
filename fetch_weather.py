import os
import json
import requests
from datetime import datetime

# ==========================================
# 1. 資安防護：從環境變數讀取氣象局 API 金鑰
# ==========================================
API_KEY = os.getenv("CWA_API_KEY")
if not API_KEY:
    raise ValueError("找不到 CWA_API_KEY 環境變數，請確認 GitHub Secrets 設定！")

# 恆春鎮 3 天逐小時預報 API URL (F-D0047-033)
URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-033?Authorization={API_KEY}&format=JSON"

try:
    response = requests.get(URL)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    print(f"資料抓取失敗: {e}")
    exit(1)

# ==========================================
# 2. 解析資料 (精準鎖定恆春鎮的前 12 筆逐小時預報)
# ==========================================
# 尋找恆春鎮的資料
locations = data['records']['Locations'][0]['Location']
hengchun_data = None
for loc in locations:
    if loc['LocationName'] == '恆春鎮':
        hengchun_data = loc
        break

if not hengchun_data:
    print("找不到恆春鎮的氣象資料")
    exit(1)

# 提取溫度 (T) 與 相對濕度 (RH) 的時間序列
weather_elements = hengchun_data['WeatherElement']
temp_times = []
rh_times = []

for elem in weather_elements:
    if elem['ElementName'] == 'T':  # 溫度
        temp_times = elem['Time'][:12]  # 只取前 12 筆
    elif elem['ElementName'] == 'RH':  # 相對濕度
        rh_times = elem['Time'][:12]

# 整理成前端好讀的 JSON 陣列格式
labels = []
temp_values = []
rh_values = []
table_rows_html = ""

for t_data, r_data in zip(temp_times, rh_times):
    # 格式化時間 (例如: 2026-05-20 09:00)
    raw_time = t_data['StartTime']
    dt = datetime.strptime(raw_time[:16], "%Y-%m-%dT%H:%M")
    formatted_time = dt.strftime("%m/%d %H:%M")
    
    temp = t_data['ElementValue'][0]['Temperature']
    rh = r_data['ElementValue'][0]['RelativeHumidity']
    
    labels.append(formatted_time)
    temp_values.append(int(temp))
    rh_values.append(int(rh))
    
    # 建立表格的 HTML 欄位
    table_rows_html += f"<tr><td>{formatted_time}</td><td>{temp} °C</td><td>{rh} %</td></tr>"

# ==========================================
# 3. 產生美化的暖色系 HTML 報表
# ==========================================
current_time_str = datetime.now().strftime("%Y%m%d%H%M")
filename = f"{current_time_str}_hengchun_weather.html"

# 使用暖色系 (Warm Tones: 溫暖橘、淺米白、深梅紅) 與 Chart.js 繪製折線圖
html_template = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>恆春鎮天氣預報報表</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #FFFDF9; /* 溫暖淺米白 */
            color: #4A3728; /* 深暖咖 */
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .container {{
            max-width: 800px;
            width: 100%;
            background: #FFFFFF;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(218, 165, 32, 0.15);
            border-top: 6px solid #E67E22; /* 溫暖橘橘條 */
        }}
        h2 {{
            color: #D35400;
            text-align: center;
            margin-bottom: 5px;
        }}
        .timestamp {{
            text-align: center;
            color: #7F8C8D;
            font-size: 0.9em;
            margin-bottom: 30px;
        }}
        .chart-container {{
            position: relative;
            margin: auto;
            height: 350px;
            width: 100%;
            margin-bottom: 40px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background-color: #FFF9F2;
        }}
        th, td {{
            padding: 12px;
            text-align: center;
            border-bottom: 1px solid #F3E5D8;
        }}
        th {{
            background-color: #E67E22;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #FFEEDD;
        }}
    </style>
</head>
<body>

<div class="container">
    <h2>恆春鎮天氣預報 (未來 12 小時)</h2>
    <div class="timestamp">報表生成時間：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
    
    <div class="chart-container">
        <canvas id="weatherChart"></canvas>
    </div>

    <table>
        <thead>
            <tr>
                <th>時間 (時間區段起點)</th>
                <th>溫度 (°C)</th>
                <th>相對濕度 (%)</th>
            </tr>
        </thead>
        <tbody>
            {table_rows_html}
        </tbody>
    </table>
</div>

<script>
const ctx = document.getElementById('weatherChart').getContext('2d');
const weatherChart = new Chart(ctx, {{
    type: 'line',
    data: {{
        labels: {json.dumps(labels)},
        datasets: [
            {{
                label: '溫度 (°C)',
                data: {json.dumps(temp_values)},
                borderColor: '#E67E22',
                backgroundColor: 'rgba(230, 126, 34, 0.1)',
                borderWidth: 3,
                yAxisID: 'y-temp',
                tension: 0.3,
                pointRadius: 4
            }},
            {{
                label: '相對濕度 (%)',
                data: {json.dumps(rh_values)},
                borderColor: '#3498DB',
                backgroundColor: 'rgba(52, 152, 219, 0.05)',
                borderWidth: 3,
                yAxisID: 'y-rh',
                tension: 0.3,
                pointRadius: 4,
                borderDash: [5, 5]
            }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
            'y-temp': {{
                type: 'linear',
                position: 'left',
                title: {{ display: true, text: '溫度 (°C)', color: '#E67E22' }}
            }},
            'y-rh': {{
                type: 'linear',
                position: 'right',
                grid: {{ drawOnChartArea: false }},
                title: {{ display: true, text: '相對濕度 (%)', color: '#3498DB' }}
            }}
        }}
    }}
}});
</script>

</body>
</html>
"""

# 將產出的網頁儲存（未來會透過自動化推送到雲端網頁）
with open(filename, "w", encoding="utf-8") as f:
    f.write(html_template)

# 同時複製一份為 index.html，方便 GitHub Pages 作為預設首頁顯示最新報表
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"報表成功產出: {filename} 與 index.html")