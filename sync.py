# -*- coding: utf-8 -*-
import os, requests, re, shutil
from collections import defaultdict

# --- 系统配置区 ---
TOKEN = os.environ.get('G_T') or os.environ.get('DEPLOY_TOKEN')
OWNER = "swiftdd"
NAME = "Synapse" 
# ------------------

def get_discussions():
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        discussions(first: 100, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes {
            title, url, body, createdAt
            category { name }
          }
        }
      }
    }
    """
    try:
        vars = {"owner": OWNER, "name": NAME}
        resp = requests.post(url, json={"query": query, "variables": vars}, headers=headers).json()
        if 'errors' in resp: return []
        return resp['data']['repository']['discussions']['nodes']
    except:
        return []

def sync():
    for d in ["BACKUP", "wiki_temp"]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)

    data = get_discussions()
    categories = defaultdict(list)

    for item in data:
        title, body, cat = item['title'], item['body'], item['category']['name']
        date = item['createdAt'].split('T')[0]
        clean_t = re.sub(r'[\/\\:\*\?"<>\|]', '', title).strip().replace(" ", "-")
        
        cat_path = os.path.join("BACKUP", cat)
        if not os.path.exists(cat_path): os.makedirs(cat_path)
        f_name = f"{date}-{clean_t}.md"
        with open(os.path.join(cat_path, f_name), "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n> System-Link: {item['url']}\n\n{body or ''}")

        w_name = f"[{cat}] {date}-{clean_t}.md"
        with open(os.path.join("wiki_temp", w_name), "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n> **Category**: {cat} | **Date**: {date}\n\n---\n\n{body or ''}")

        rel_p = f"BACKUP/{cat}/{f_name}".replace(" ", "%20")
        categories[cat].append(f"- [{title}]({rel_p}) — `{date}`")

    # 构建 Markdown 内容
    content = f"# 🌐 {NAME} / Thought Protocol\n\n"
    content += f"> **Status**: Online | **Identity**: {OWNER}\n\n"
    content += f"[[ 🧠 Wiki-Cortex ]](https://github.com/{OWNER}/{NAME}/wiki) | [[ 💬 Input-Stream ]](https://github.com/{OWNER}/{NAME}/discussions)\n\n---\n"
    
    if not categories:
        content += "\n> [!CAUTION]\n> NO NEURAL NODES DETECTED.\n"
    else:
        for cat_name in sorted(categories.keys()):
            posts = categories[cat_name]
            content += f"### 📂 SECTION_{cat_name.upper()} ({len(posts)})\n"
            content += "\n".join(posts[:5]) + "\n"
            if len(posts) > 5:
                content += f"\n<details>\n<summary>▶ EXPAND_DATA_STREAM</summary>\n\n" + "\n".join(posts[5:]) + "\n\n</details>\n"
            content += "\n"

    # 生成 index.md
    with open("index.md", "w", encoding="utf-8") as f: f.write(content)
    # 【必须增加这一行】生成 README.md (给 GitHub 仓库首页用)
    with open("README.md", "w", encoding="utf-8") as f: f.write(content)
    # 生成 .nojekyll 防止 GitHub Pages 过滤文件
    open(".nojekyll", "w").close()

    # --- 核心：自动生成 index.html 渲染器 ---
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{OWNER} | {NAME}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-dark.min.css">
    <style>
        body {{ background-color: #0d1117; margin: 0; }}
        .markdown-body {{ box-sizing: border-box; min-width: 200px; max-width: 980px; margin: 0 auto; padding: 45px; }}
        @media (max-width: 767px) {{ .markdown-body {{ padding: 15px; }} }}
    </style>
</head>
<body class="markdown-body">
    <div id="content">Loading Neural Data...</div>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        fetch('index.md').then(r => r.text()).then(text => {{
            document.getElementById('content').innerHTML = marked.parse(text);
        }});
    </script>
</body>
</html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_template)
    
    print("Success: All nodes and rendering index generated.")

if __name__ == "__main__":
    sync()
