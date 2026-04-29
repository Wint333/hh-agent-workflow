import asyncio
import httpx


async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        messages = [
            "我们是AsterCraft Studio，想做一个给客户送礼的纸雕笔记本，主体放山峰和海浪，蓝色为主，高级一点",
            "用途是客户答谢，辅助元素加云纹和水纹，不要卡通风，可以出图",
        ]
        for text in messages:
            resp = await client.post("/api/chat", json={"user_id": "demo-user-001", "text": text})
            print(resp.json())

        stats = await client.get("/api/stats/summary")
        print(stats.json())


if __name__ == "__main__":
    asyncio.run(main())
