# TODO: набросок кода

# TODO: Не забудь заменить `your_user`, `your_password`, `your_db`, `your_table` и `your_file.csv` на свои реальные
#  данные. Этот код читает CSV файл построчно и вставляет каждую строку в указанную таблицу в базе данных.

from typing import AsyncGenerator, List
import asyncio
import aiofiles
import aiomysql
import csv
import io

async def read_csv(file_path: str) -> AsyncGenerator[List[str], None]:
    async with aiofiles.open(file_path, mode='r') as f:
        # Используя io.StringIO для чтения построчно
        async for line in f:
            # Оборачиваем строку в io.StringIO для использования с csv.reader
            line_io = io.StringIO(str(line))
            reader = csv.reader(line_io)
            for row in reader:
                yield row


async def insert_data_into_db(data: List[str]) -> None:
    conn = await aiomysql.connect(host='localhost', port=3306,
                                    user='your_user', password='your_password',
                                    db='your_db')
    async with conn.cursor() as cur:
        await cur.execute("INSERT INTO your_table (column1, column2) VALUES (%s, %s)", data)
    await conn.commit()
    conn.close()


async def main(file_path: str) -> None:
    async for row in read_csv(file_path):
        await insert_data_into_db(row)



if __name__ == '__main__':
    csv_file = 'your_file.csv'
    asyncio.run(main(file_path=csv_file))

