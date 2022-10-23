import asyncio

import aiohttp


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://127.0.0.1:8080/adv/1") as resp:
            print(await resp.text())

        # async with session.post("http://127.0.0.1:8080/adv/", json={"title": "test_title 55555 ", "desc": "description", "owner":"user1"}) as resp:
        #     print(await resp.text())

asyncio.run(main())