# -*- coding: utf-8 -*-
import os, requests, re, shutil
from collections import defaultdict

# --- 系统配置区 ---
TOKEN = os.environ.get('G_T')
OWNER = "swiftdd"
NAME = "Synapse"  # 确保与你创建的仓库名一致
# ------------------

def get_discussions():
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    # GraphQL 查询：只抓取最新生成的讨论
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
        if 'errors' in resp:
            print(f"GraphQL Errors: {resp['errors']}")
            return []
        return resp['data']['repository']['discussions']['nodes']
    except Exception as e:
        print(f"Connection failed: {e}")
        return []

def sync():
    # 1. 环境初始化
    for d in ["BACKUP", "wiki_temp"]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)

    data = get_discussions()
    categories = defaultdict(list)

    # 2. 转换讨论流为物理节点
    for item in data:
        title, body, cat = item['title'], item['body'], item['category']['name']
        date = item['createdAt'].split('T')[0]
        clean_t = re.sub(r'[\/\\:\*\?"<>\|]', '', title).strip().replace(" ", "-")
        
        # A. 物理备份 (BACKUP/分类/日期-标题.md)
        cat_path = os.path.join("BACKUP", cat)
        if not os.path.exists(cat_path): os.makedirs(cat_path)
        f_name = f"{date}-{clean_t}.md"
        with open(os.path.join(cat_path, f_name), "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n> System-Link: {item['url']}\n\n{body or ''}")

        # B. Wiki 缓存
        w_name = f"[{cat}] {date}-{clean_t}.md"
        with open(os.path.join("wiki_temp", w_name), "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n> **Category**: {cat} | **Date**: {date}\n\n---\n\n{body or ''}")

        # C. 分类统计
        rel_p = f"BACKUP/{cat}/{f_name}".replace(" ", "%20")
        categories[cat].append(f"- [{title}]({rel_p}) — `{date}`")

    # 3. 构建 README 科技感仪表盘
    content = f"# 🌐 {NAME} / Thought Protocol\n\n"
    content += f"> **Status**: Online | **Identity**: {OWNER}\n\n"
    content += f"[[ 🧠 Wiki-Cortex ]](https://github.com/{OWNER}/{NAME}/wiki) | [[ 💬 Input-Stream ]](https://github.com/{OWNER}/{NAME}/discussions)\n\n---\n"
    
    if not categories:
        content += "\n> [!CAUTION]\n> NO NEURAL NODES DETECTED. INITIALIZE VIA DISCUSSIONS.\n"
    else:
        for cat_name in sorted(categories.keys()):
            posts = categories[cat_name]
            content += f"### 📂 SECTION_{cat_name.upper()} ({len(posts)})\n"
            content += "\n".join(posts[:5]) + "\n"
            if len(posts) > 5:
                content += f"\n<details>\n<summary>▶ EXPAND_DATA_STREAM ({len(posts)-5} MORE)</summary>\n\n" + "\n".join(posts[5:]) + "\n\n</details>\n"
            content += "\n"

    # 4. 生成文件
    with open("README.md", "w", encoding="utf-8") as f: f.write(content)
    with open("index.md", "w", encoding="utf-8") as f: f.write("---\nlayout: default\n---\n\n" + content)
    open(".nojekyll", "w").close()
    
    print(f"Synced {len(data)} nodes.")

if __name__ == "__main__":
    sync()
