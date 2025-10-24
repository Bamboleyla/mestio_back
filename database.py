import asyncpg
from fastapi import HTTPException
import os
import logging

logging.basicConfig(level=logging.INFO)


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        dsn = os.getenv("DATABASE_URL")
        logging.info(f"Attempting to connect to database with DSN: {dsn}")
        try:
            self.pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=5,
                max_size=20,
                ssl=False,
            )
            logging.info("Database connection pool created successfully.")
        except Exception as e:
            logging.error(f"Failed to create database pool: {str(e)}")
            raise

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def execute_procedure(self, procedure_name: str, *args):
        async with self.pool.acquire() as connection:
            try:
                # Формируем вызов хранимой процедуры
                placeholders = ", ".join([f"${i+1}" for i in range(len(args))])
                query = f"SELECT * FROM {procedure_name}({placeholders})"

                result = await connection.fetch(query, *args)
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def fetch_one(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

    async def fetch_all(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)


# Глобальный экземпляр базы данных
db = Database()
