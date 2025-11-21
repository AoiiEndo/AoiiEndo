import os
import requests
import random
import string

# --- 設定 ---
USERNAME = os.environ.get("USERNAME") # GitHub Actionsから渡されるユーザー名
TOKEN = os.environ.get("GITHUB_TOKEN") # GitHub Actionsのトークン

if not USERNAME or not TOKEN:
    raise Exception("環境変数 USERNAME または GITHUB_TOKEN が設定されていません。")

# 文字セット: 英大文字と数字
CHARS = string.ascii_uppercase + string.digits

def get_contribution_data():
    """GitHub GraphQL APIから過去1年間のコントリビューションを取得"""
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
    """APIの文字列レベルを0-4の数値に変換"""
    mapping = {
        "NONE": 0,
        "FIRST_QUARTILE": 1,
        "SECOND_QUARTILE": 2,
        "THIRD_QUARTILE": 3,
        "FOURTH_QUARTILE": 4
    }
    return mapping.get(level_str, 0)

def get_color_opacity(level):
    if level == 0: return 0.5, "#0D440D" 
    if level == 1: return 0.7, "#1E6E1E"
    if level == 2: return 0.85, "#2EA043"
    if level == 3: return 0.95, "#3FB950"
    if level == 4: return 1.0,  "#00FF00"
    
    return 0.5, "#0D440D"

def generate_svg():
    weeks_data = get_contribution_data()
    
    width = 840
    height = 130
    cell_w = 15
    cell_h = 15
    
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
            animation: rain-fall 2s infinite;
        }}
        @keyframes rain-fall {{
            0%   {{ opacity: 0.3; text-shadow: none; }}
            10%  {{ opacity: 1.0; text-shadow: 0 0 8px #00ff00; fill: #ffffff; }}
            20%  {{ opacity: 0.3; text-shadow: none; fill: inherit; }}
            100% {{ opacity: 0.3; text-shadow: none; }}
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
            delay = (d_idx * 0.15) + week_offset
            
            svg_content += f"""
            <text x="{x}" y="{y}" fill="{color}" class="matrix-char" style="animation-delay: {delay}s;">
                {char}
            </text>
            """

    svg_content += "</svg>"

    # distディレクトリに出力（ディレクトリがなければ作成）
    os.makedirs("dist", exist_ok=True)
    with open("dist/github-matrix.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("SVG generated successfully.")

if __name__ == "__main__":
    generate_svg()
