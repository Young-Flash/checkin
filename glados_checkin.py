#!/usr/bin/env python3
"""
GLaDOS 自动签到脚本
- 从环境变量读取 cookie 进行签到
- 汇总所有账号的签到结果
- 任一失败则返回非零退出码
"""

import os
import sys
import time
import random
import requests

# ========================================
# 配置：要读取的 Cookie 环境变量名列表
# 新增账号时，在 GitHub Secrets 添加后，把变量名加到这里
# ========================================
COOKIE_ENV_VARS = [
#   "GLADOS_COOKIE", // 这个坏了
    "GLADOS_COOKIE_2",
]

CHECKIN_URL = "https://glados.cloud/api/user/checkin"
HEADERS_TEMPLATE = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9,zh;q=0.8",
    "content-type": "application/json;charset=UTF-8",
    "dnt": "1",
    "origin": "https://glados.cloud",
    "priority": "u=1, i",
    "sec-ch-ua": '"Not;A=Brand";v="24", "Chromium";v="128"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
}


def checkin(cookie_header: str, account_name: str) -> dict:
    """
    执行签到请求
    返回: {"success": bool, "message": str, "code": int|None}
    """
    headers = HEADERS_TEMPLATE.copy()
    headers["cookie"] = cookie_header

    try:
        response = requests.post(
            CHECKIN_URL,
            headers=headers,
            json={"token": "glados.cloud"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        code = data.get("code", -1)
        message = data.get("message", str(data))

        # code 为 0 表示成功，1 表示已经签到过
        if code in (0, 1):
            return {"success": True, "message": message, "code": code}
        else:
            return {"success": False, "message": message, "code": code}

    except requests.exceptions.Timeout:
        return {"success": False, "message": "请求超时", "code": None}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"请求失败: {e}", "code": None}
    except Exception as e:
        return {"success": False, "message": f"未知错误: {e}", "code": None}


def main():
    print("=" * 50)
    print("GLaDOS 自动签到")
    print("=" * 50)
    print()

    results = []

    for i, env_var in enumerate(COOKIE_ENV_VARS):
        cookie_value = os.environ.get(env_var)

        if not cookie_value:
            print(f"⚠️  [{env_var}] 环境变量未设置，跳过")
            results.append({
                "account": env_var,
                "success": False,
                "message": "环境变量未设置",
            })
            continue

        # 环境变量格式: "cookie: koa:sess=xxx; koa:sess.sig=xxx"
        # 需要去掉 "cookie: " 前缀，只保留实际的 cookie 值
        if cookie_value.lower().startswith("cookie:"):
            cookie_header = cookie_value[7:].strip()
        else:
            cookie_header = cookie_value.strip()

        print(f"🔄 [{env_var}] 正在签到...")
        result = checkin(cookie_header, env_var)
        result["account"] = env_var
        results.append(result)

        status = "✅" if result["success"] else "❌"
        print(f"   {status} {result['message']}")

        # 如果不是最后一个账号，则添加随机延迟
        if i < len(COOKIE_ENV_VARS) - 1:
            delay = random.randint(10, 100)
            print(f"⏳ 等待 {delay} 秒后再执行下一个账号...")
            time.sleep(delay)
            print()
        else:
            print()

    # 汇总结果
    print("=" * 50)
    print("签到结果汇总")
    print("=" * 50)

    success_count = 0
    fail_count = 0

    for r in results:
        status = "✅ 成功" if r["success"] else "❌ 失败"
        print(f"  {r['account']}: {status} - {r['message']}")
        if r["success"]:
            success_count += 1
        else:
            fail_count += 1

    print()
    print(f"总计: {len(results)} 个账号, ✅ {success_count} 成功, ❌ {fail_count} 失败")
    print("=" * 50)

    # 如果有任何失败，返回非零退出码
    if fail_count > 0:
        print("\n❌ 有账号签到失败，workflow 将标记为失败")
        sys.exit(1)
    else:
        print("\n✅ 所有账号签到成功！")
        sys.exit(0)


if __name__ == "__main__":
    main()
