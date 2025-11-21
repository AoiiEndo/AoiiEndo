import os
import requests
import random
import string

# --- 設定 ---
USERNAME = os.environ.get("USERNAME")
TOKEN = os.environ.get("GITHUB_TOKEN") 

if not USERNAME: USERNAME = "AoiiEndo" # ローカルテスト用

CHARS = string.ascii_uppercase + string.digits

def get_contribution_data():
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
    # 不透明度は全て 1.0 (OpacityはCSSから排除済み)
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
        return

    width = 840
    height = 130
    cell_w = 15
    cell_h = 15
    
    # 【重要修正】 CSS変数 (--matrix-color) を使用
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
            /* 変数で定義された色を初期値として使う */
            fill: var(--matrix-color);
            animation: rain-fall 3s infinite;
        }}
        @keyframes rain-fall {{
            /* 0% は元の色 (var(--matrix-color)) */
            0%   {{ fill: var(--matrix-color); text-shadow: none; }}
            
            /* 10% で白く光る */
            10%  {{ fill: #ffffff; text-shadow: 0 0 10px #ffffff; }}
            
            /* 20% で元の色に戻る (inheritではなく変数を使う！) */
            20%  {{ fill: var(--matrix-color); text-shadow: none; }}
            
            /* 最後まで元の色を維持 */
            100% {{ fill: var(--matrix-color); text-shadow: none; }}
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
            
            # 【重要修正】 style属性に --matrix-color: {color} を埋め込む
            # これによりCSSアニメーション側でこの色が参照可能になる
            svg_content += f"""
            <text x="{x}" y="{y}" class="matrix-char" style="--matrix-color: {color}; animation-delay: {delay}s;">
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
