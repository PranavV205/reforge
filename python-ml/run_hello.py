import asyncio
import os

from temporalio.client import Client

from workflows.hello import HelloWorkflow

TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "ml-tasks")


async def main():
    client = await Client.connect(TEMPORAL_HOST)
    result = await client.execute_workflow(
        HelloWorkflow.run,
        "reforge",
        id="hello-workflow",
        task_queue=TASK_QUEUE,
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
