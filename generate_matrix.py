import os
import requests
import random
import string

# --- 設定 ---
USERNAME = os.environ.get("USERNAME")
TOKEN = os.environ.get("GITHUB_TOKEN") 

# 文字セット: 英大文字と数字
CHARS = string.ascii_uppercase + string.digits

def get_contribution_data():
    # トークンがない場合のダミーデータ
    if not TOKEN:
        print("Token not found. Using dummy data.")
        return [{"contributionDays": [{"contributionLevel": "NONE" if random.random() > 0.5 else "FIRST_QUARTILE"} for _ in range(7)]} for _ in range(53)]

    headers = {"Authorization": f"Bearer {TOKEN}"}
    query = """
    query($userName:String!) {
      user(login: $userName) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionLevel
              }
            }
          }
        }
      }
    }
    """
    variables = {"userName": USERNAME}
    response = requests.post("https://api.github.com/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} {response.text}")
    
    data = response.json()
    if "errors" in data:
         raise Exception(f"GraphQL Error: {data['errors']}")

    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

def get_level_from_string(level_str):
    mapping = {
        "NONE": 0,
        "FIRST_QUARTILE": 1,
        "SECOND_QUARTILE": 2,
        "THIRD_QUARTILE": 3,
        "FOURTH_QUARTILE": 4
    }
    return mapping.get(level_str, 0)

def get_color_opacity(level):
    # Level 0の色を #0D440D だと暗すぎるため、#1a5c1a (少し明るい緑) に変更
    # 不透明度は全て 1.0 に統一
    if level == 0: return 1.0, "#1a5c1a" 
    if level == 1: return 1.0, "#2ea043"
    if level == 2: return 1.0, "#3fb950"
    if level == 3: return 1.0, "#5ce66c"
    if level == 4: return 1.0, "#ffffff"
    
    return 1.0, "#1a5c1a"

def generate_svg():
    try:
        weeks_data = get_contribution_data()
    except Exception as e:
        print(e)
        return # エラー時は中断

    width = 840
    height = 130
    cell_w = 15
    cell_h = 15
    
    # 【重要修正】 @keyframes から opacity の行を削除しました
    # これにより、常に文字はハッキリ表示され、光る時だけ白くなります
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
    <style>
        @font-face {{ font-family: 'MatrixCode'; src: local('Consolas'), local('Courier New'), monospace; }}
        .bg {{ fill: #0d1117; }}
        .matrix-char {{
            font-family: 'MatrixCode', monospace;
            font-size: 11px;
            font-weight: bold;
            text-anchor: middle;
            dominant-baseline: middle;
            animation: rain-fall 3s infinite;
        }}
        @keyframes rain-fall {{
            0%   {{ fill: inherit; text-shadow: none; }}
            10%  {{ fill: #ffffff; text-shadow: 0 0 10px #ffffff; }} /* 白く発光 */
            20%  {{ fill: inherit; text-shadow: none; }}
            100% {{ fill: inherit; text-shadow: none; }}
        }}
    </style>
    <rect width="100%" height="100%" class="bg" />
    """

    for w_idx, week in enumerate(weeks_data):
        week_offset = random.random() * 2.0
        
        for d_idx, day in enumerate(week["contributionDays"]):
            level = get_level_from_string(day["contributionLevel"])
            opacity, color = get_color_opacity(level)
            char = random.choice(CHARS)
            
            x = w_idx * cell_w + 15
            y = d_idx * cell_h + 20
            delay = (d_idx * 0.1) + week_offset
            
            # style属性に opacity: 1.0 を明記
            svg_content += f"""
            <text x="{x}" y="{y}" fill="{color}" class="matrix-char" style="opacity: {opacity}; animation-delay: {delay}s;">
                {char}
            </text>
            """

    svg_content += "</svg>"

    os.makedirs("dist", exist_ok=True)
    with open("dist/github-matrix.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("SVG generated successfully.")

if __name__ == "__main__":
    generate_svg()
