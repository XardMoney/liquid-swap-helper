from settings import SEMAPHORE_LIMIT
import asyncio

from worker import Worker


if __name__ == "__main__":
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
    worker = Worker(semaphore)
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    except Exception:
        pass

    asyncio.run(worker.start())
