from traceback import extract_stack
from asyncio import sleep


async def say_func_name() -> str:
    await sleep(0)  # Имитируем асинхронную операцию
    stack = extract_stack()
    return f"Function Name: {stack[-2][2]}"
