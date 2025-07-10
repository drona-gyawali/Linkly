# yo chai script ho just check garna ko lagi ki hamro db chaliraxa kinai vanerw
import asyncio

from linkly.database import get_db


async def main():
    async with get_db() as db:
        collections = await db.list_collection_names()
        print("Connected to MongoDB")
        print("Collections:", collections)


if __name__ == "__main__":
    asyncio.run(main())
