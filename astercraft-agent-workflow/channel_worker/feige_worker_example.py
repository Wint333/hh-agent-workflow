"""
示例渠道 Worker。

真实环境中可以用 Playwright 对接飞鸽/抖店页面。
这里保留一个最小轮询结构，方便审核者理解 outbox 的使用方式。
"""

import asyncio
import httpx


API_BASE = "http://127.0.0.1:8000/api"


async def send_to_channel(task: dict) -> None:
    # 替换为真实的飞鸽 DOM 输入与发送逻辑。
    print(f"[SEND] user={task['user_id']} type={task['type']} content={task['content']}")


async def main() -> None:
    async with httpx.AsyncClient(timeout=20) as client:
        while True:
            resp = await client.get(f"{API_BASE}/outbox/pending", params={"limit": 10})
            resp.raise_for_status()
            tasks = resp.json()

            for task in tasks:
                await send_to_channel(task)
                ack = await client.post(f"{API_BASE}/outbox/ack/{task['id']}")
                ack.raise_for_status()

            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
