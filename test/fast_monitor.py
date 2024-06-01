import uvicorn
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import FastAPI
from typing import Optional
from datetime import datetime
from RabbitSpider.core.scheduler import Scheduler
from RabbitSpider.utils.control import SettingManager
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import create_engine, Table, MetaData, select, update, insert, delete

settings = SettingManager()

scheduler = Scheduler(settings.get('RABBIT_USERNAME'),
                      settings.get('RABBIT_PASSWORD'),
                      settings.get('RABBIT_HOST'),
                      settings.get('RABBIT_PORT'),
                      settings.get('RABBIT_VIRTUAL_HOST'))

engine = create_engine('mysql+pymysql://root:123456@127.0.0.1:3306/monitor')
table = Table('monitor_table', MetaData(), autoload_with=engine)

Session = sessionmaker(bind=engine)
session = Session()


class TaskData(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    sync: Optional[int] = None
    total: Optional[int] = None
    status: Optional[int] = None
    sleep: Optional[int] = None
    stop_time: Optional[datetime] = None
    next_time: Optional[datetime] = None

    class Config:
        from_attributes = True


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源访问
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有头部
)


@app.get('/get/task')
async def get_task():
    resp = []
    connection, channel = await scheduler.connect()
    stmt = select(table).where(table.columns.next_time.is_(None))
    results = session.execute(stmt)
    session.commit()
    for result in results:
        item = TaskData.model_validate(result).model_dump()
        item['total'] = await scheduler.get_message_count(channel, item['name'])
        resp.append(item)
    connection.close(), channel.close()
    return resp


# 已完成的任务
@app.get('/get/done')
async def get_done():
    stmt = select(table).where(table.columns.next_time.isnot(None))
    results = session.execute(stmt)
    session.commit()
    resp = jsonable_encoder([TaskData.model_validate(result).model_dump() for result in results])
    return resp


@app.post('/post/task')
async def start_task(item: TaskData):
    stmt = select(table).where(table.columns.name == item.name)
    result = engine.connect().execute(stmt).first()
    if result:
        stmt = update(table).where(table.columns.name == item.name).values(
            {key: value for key, value in item.model_dump().items() if
             value is not None or key == 'stop_time' or key == 'next_time' or key == 'sleep'})
        session.execute(stmt)
        session.commit()
    else:
        stmt = insert(table).values(**item.model_dump())
        session.execute(stmt)
        session.commit()


@app.post('/delete/queue')
async def delete_queue(item: TaskData):
    connection, channel = await scheduler.connect()
    await scheduler.delete_queue(channel, item.name)
    stmt = delete(table).where(table.columns.name == item.name)
    session.execute(stmt)
    session.commit()
    await connection.close()
    await channel.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
