# -*- coding: utf-8 -*-
import os, requests, re, shutil
from collections import defaultdict

# --- 科技感配置区 ---
TOKEN = os.environ.get('G_T')
OWNER = "swiftdd"
NAME = "Synapse"  # 你的科技感仓库名
# ------------------

def get_discussions():
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    query = """
    query($owner: String!, $name: String!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        discussions(first: 100, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
          pageInfo { hasNextPage, endCursor }
          nodes {
            title, url, body, createdAt
            category { name }
          }
        }
      }
    }
    """
    all_data, cursor = [], None
    while True:
        vars = {"owner": OWNER, "name": NAME, "cursor": cursor}
        resp = requests.post(url, json={"query": query, "variables": vars}, headers=headers).json()
        if 'data' not in resp: 
            print(f"Error: {resp}")
            break
        nodes = resp['data']['repository']['discussions']['nodes']
        all_data.extend(nodes)
        page_info = resp['data']['repository']['discussions']['pageInfo']
        if not page_info['hasNextPage']: break
        cursor = page_info['endCursor']
    return all_data

def sync():
    # 目录重置
    for d in ["BACKUP", "wiki_temp"]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)

    data = get_discussions()
    categories = defaultdict(list)

    for item in data:
        title, body, cat = item['title'], item['body'], item['category']['name']
        date = item['createdAt'].split('T')[0]
        clean_t = re.sub(r'[\/\\:\*\?"<>\|]', '', title).strip().replace(" ", "-")
        
        # A. 系统备份
        cat_path = os.path.join("BACKUP", cat)
        if not os.path.exists(cat_path): os.makedirs(cat_path)
        f_name = f"{date}-{clean_t}.md"
        with open(os.path.join(cat_path, f_name), "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n> System-Link: {item['url']}\n\n{body}")

        # B. Wiki 神经连接同步
        w_name = f"[{cat}] {date}-{clean_t}.md"
        with open(os.path.join("wiki_temp", w_name), "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n> **Nodes**: {cat} | **Timestamp**: {date}\n\n---\n\n{body}")

        # C. 路径映射
        rel_p = f"BACKUP/{cat}/{f_name}".replace(" ", "%20")
        categories[cat].append(f"- [{title}]({rel_p}) — `{date}`")

    # 3. 构造科技感界面
    content = f"# 🌐 {NAME} / Thought Protocol\n\n"
    content += f"> **Status**: System Online | **Identity**: {OWNER}\n\n"
    content += f"[[ 🧠 Wiki-Cortex ]](https://github.com/{OWNER}/{NAME}/wiki)  |  [[ 💬 Input-Stream ]](https://github.com/{OWNER}/{NAME}/discussions)\n\n---\n"
    
    for cat_name in sorted(categories.keys()):
        posts = categories[cat_name]
        content += f"### 📂 SECTION_{cat_name.upper()} ({len(posts)})\n"
        content += "\n".join(posts[:5]) + "\n"
        if len(posts) > 5:
            content += f"\n<details>\n<summary>▶ EXPAND_DATA_STREAM ({len(posts)-5})</summary>\n\n" + "\n".join(posts[5:]) + "\n\n</details>\n"
        content += "\n"

    with open("README.md", "w", encoding="utf-8") as f: f.write(content)
    with open("index.md", "w", encoding="utf-8") as f: f.write("---\nlayout: default\n---\n\n" + content)
    open(".nojekyll", "w").close()

    print(f"Done. Processed {len(data)} nodes.")

if __name__ == "__main__":
    sync()
