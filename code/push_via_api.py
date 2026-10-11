# -*- coding: utf-8 -*-
"""
通过 GitHub 官方 API (api.github.com) 建仓并上传项目全部文件。
适用场景：本机 github.com 无法直连，但 api.github.com 可访问（浏览器登录困难时）。
用法：
    set GITHUB_TOKEN=ghp_xxxx        (Windows CMD)
    $env:GITHUB_TOKEN="ghp_xxxx"     (PowerShell)
    python code/push_via_api.py
只用 Python 标准库，不需要额外安装依赖。
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
REPO = "nlp-tone-thesis"
DESC = "管理层语调NLP测度构建五步流水线：毕业论文模拟稿+可复现代码+测度结果+数据说明"
SKIP_DIRS = {".git", "__pycache__", ".idea"}


def req(method, path, token, data=None):
    url = path if path.startswith("http") else API + path
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, method=method)
    r.add_header("Authorization", f"token {token}")
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("User-Agent", "nlp-tone-thesis-uploader")
    if body:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def main():
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        print("缺少令牌。请先设置环境变量 GITHUB_TOKEN 再运行本脚本。")
        print('  PowerShell:  $env:GITHUB_TOKEN="ghp_xxxx"; python code/push_via_api.py')
        print('  生成地址:    https://github.com/settings/tokens  (勾选 repo 权限)')
        sys.exit(1)

    code, me = req("GET", "/user", token)
    if code != 200:
        print("令牌验证失败:", code, me.get("message"))
        sys.exit(1)
    login = me["login"]
    print(f"已认证账号: {login}")

    code, res = req("POST", "/user/repos", token,
                    {"name": REPO, "description": DESC, "private": False,
                     "auto_init": False})
    if code == 201:
        print(f"仓库创建成功: https://github.com/{login}/{REPO}")
    elif code == 422:
        print(f"仓库已存在，直接上传文件: https://github.com/{login}/{REPO}")
    else:
        print("创建仓库失败:", code, res.get("message"))
        sys.exit(1)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root).replace("\\", "/")
            files.append((rel, p))
    files.sort()

    ok, fail = 0, []
    for rel, p in files:
        with open(p, "rb") as fh:
            content = base64.b64encode(fh.read()).decode()
        # 若文件已存在，需要带上 sha 才能更新
        code, cur = req("GET", f"/repos/{login}/{REPO}/contents/{urllib.parse.quote(rel)}", token)
        payload = {"message": f"upload {rel}", "content": content}
        if code == 200:
            payload["sha"] = cur["sha"]
        code, res = req("PUT", f"/repos/{login}/{REPO}/contents/{urllib.parse.quote(rel)}",
                        token, payload)
        if code in (200, 201):
            ok += 1
            print(f"  ✓ {rel}")
        else:
            fail.append(rel)
            print(f"  ✗ {rel} -> {code} {res.get('message')}")

    print(f"\n完成：成功 {ok} 个文件" + (f"，失败 {fail}" if fail else ""))
    print(f"仓库地址: https://github.com/{login}/{REPO}")


if __name__ == "__main__":
    main()
