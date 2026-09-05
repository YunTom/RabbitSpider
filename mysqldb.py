from typing import AsyncGenerator, List, Dict, Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)


class AsyncMySQLDB:
    def __init__(
            self,
            host: str,
            user: str,
            password: str,
            database: str,
            port: int = 3306,
            pool_size: int = 5,
            max_overflow: int = 10,
            echo: bool = False,
    ):
        self.engine = create_async_engine(
            f"mysql+aiomysql://{user}:{password}@{host}:{port}/{database}",
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=1200,
            pool_timeout=180,
            pool_pre_ping=True,
            echo=echo,
            future=True,
        )

        self.async_session = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def query(
            self,
            sql: str,
            batch_size: int = 1000,
            **params
    ) -> AsyncGenerator[Dict[str, Any], None]:

        async with self.async_session() as session:
            stmt = text(sql).execution_options(stream_results=True)
            result = await session.stream(stmt, params)

            async for row in result.mappings().yield_per(batch_size):
                yield row

    async def get(self, sql: str, **params) -> Dict[str, Any] | None:
        async with self.async_session() as session:
            result = await session.execute(text(sql), params)
            return result.mappings().first()

    async def execute(self, sql: str, **params) -> int:
        async with self.async_session() as session:
            async with session.begin():
                result = await session.execute(text(sql), params)
                return result.rowcount

    async def insert(self, table_name: str, item: Dict[str, Any]) -> int:
        fields = ", ".join(item.keys())
        placeholders = ", ".join([f":{k}" for k in item.keys()])

        sql = f"INSERT INTO {table_name} ({fields}) VALUES ({placeholders})"

        async with self.async_session() as session:
            async with session.begin():
                try:
                    await session.execute(text(sql), item)
                    return 1
                except IntegrityError:
                    return 0

    async def insert_many(
            self,
            table_name: str,
            items: List[Dict[str, Any]],
    ) -> int:

        if not items:
            return 0

        fields = ", ".join(items[0].keys())
        placeholders = ", ".join([f":{k}" for k in items[0].keys()])

        sql = f"INSERT INTO {table_name} ({fields}) VALUES ({placeholders})"

        async with self.async_session() as session:
            async with session.begin():
                result = await session.execute(text(sql), items)
                return result.rowcount or len(items)

    async def update(
            self,
            table_name: str,
            updates: Dict[str, Any],
            conditions: Dict[str, Any],
    ) -> int:

        set_clause = ", ".join([f"{k} = :set_{k}" for k in updates])
        where_clause = " AND ".join([f"{k} = :where_{k}" for k in conditions])

        params = {
            **{f"set_{k}": v for k, v in updates.items()},
            **{f"where_{k}": v for k, v in conditions.items()},
        }

        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

        async with self.async_session() as session:
            async with session.begin():
                result = await session.execute(text(sql), params)
                return result.rowcount

    async def delete(
            self,
            table_name: str,
            conditions: Dict[str, Any],
    ) -> int:

        where_clause = " AND ".join([f"{k} = :{k}" for k in conditions])
        sql = f"DELETE FROM {table_name} WHERE {where_clause}"

        async with self.async_session() as session:
            async with session.begin():
                result = await session.execute(text(sql), conditions)
                return result.rowcount

    async def close(self):
        await self.engine.dispose()
