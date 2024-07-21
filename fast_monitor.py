import os
from croniter import croniter
from crontab import CronTab
import uvicorn, subprocess
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import FastAPI, Response, status
from typing import Optional
from datetime import datetime
from RabbitSpider.core.scheduler import Scheduler
from RabbitSpider.utils.control import SettingManager
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import create_engine, Table, MetaData, select, update, insert, delete, func

settings = SettingManager({'RABBIT_HOST': '60.204.154.131',
                           'RABBIT_PORT': 5672,
                           'RABBIT_USERNAME': 'yuntom',
                           'RABBIT_PASSWORD': '123456',
                           'RABBIT_VIRTUAL_HOST': '/'})

scheduler = Scheduler(settings)

engine = create_engine('mysql+pymysql://root:123456@60.204.154.131:3306/monitor')
table = Table('monitor_table', MetaData(), autoload_with=engine)

Session = sessionmaker(bind=engine)
session = Session()


class TaskData(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    task_count: Optional[int] = None
    total: Optional[int] = None
    status: Optional[int] = None
    create_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    next_time: Optional[datetime] = None
    crontab: Optional[str] = None
    pid: Optional[int] = None,
    mode: Optional[str] = None
    dir: Optional[str] = None

    class Config:
        from_attributes = True


class CreateData(BaseModel):
    name: Optional[str] = None
    mode: Optional[str] = None
    task_count: Optional[int] = None
    crontab: Optional[str] = None
    dir: Optional[str] = None
    status: Optional[int] = None
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源访问
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有头部
)


# 运行中任务
@app.get('/get/task')
async def get_task():
    resp = []
    connection, channel = await scheduler.connect()
    stmt = select(table).where(table.columns.status == 1)
    results = session.execute(stmt)
    session.commit()
    for result in results:
        item = TaskData.model_validate(result).model_dump()
        try:
            item['total'] = await scheduler.get_message_count(channel, item['name'])
        except Exception:
            item['total'] = 0
        resp.append(item)
    await connection.close(), await channel.close()
    return resp


# 异常任务
@app.get('/get/danger')
async def get_danger():
    resp = []
    connection, channel = await scheduler.connect()
    stmt = select(table).where(table.columns.status == 0)
    results = session.execute(stmt)
    session.commit()
    for result in results:
        item = TaskData.model_validate(result).model_dump()
        item['total'] = await scheduler.get_message_count(channel, item['name'])
        resp.append(item)
    await connection.close(), await channel.close()
    return resp


# 已完成的任务
@app.get('/get/done')
async def get_done():
    stmt = select(table).where(table.columns.status == 2)
    results = session.execute(stmt)
    session.commit()
    resp = jsonable_encoder([TaskData.model_validate(result).model_dump() for result in results])
    return resp


@app.get('/get/count')
async def get_count():
    resp = {}
    stmt = select(func.count(table.columns.name)).where(table.columns.next_time.is_(None),
                                                        table.columns.stop_time.is_(None))
    results = session.execute(stmt)
    resp['success_totals'] = results.scalar()

    stmt = select(func.count(table.columns.name)).where(table.columns.stop_time.isnot(None))
    results = session.execute(stmt)
    resp['danger_totals'] = results.scalar()

    stmt = select(func.count(table.columns.name)).where(table.columns.next_time.isnot(None))
    results = session.execute(stmt)
    resp['info_totals'] = results.scalar()
    return resp


# 更新任务状态
@app.post('/post/task')
async def post_task(item: TaskData):
    args = {key: value for key, value in item.model_dump().items() if
            value is not None or key == 'stop_time' or key == 'next_time'}
    if item.status == 2:
        stmt = select(table.columns.crontab).where(table.columns.name == item.name, table.columns.mode == item.mode)
        result = engine.connect().execute(stmt).first()
        if result and result[0]:
            args['next_time'] = croniter(result[0], datetime.now()).get_next(datetime).strftime(
                '%Y-%m-%d %H:%M:%S')
        else:
            stmt = delete(table).where(table.columns.pid == item.pid)
            session.execute(stmt)
            session.commit()
            return
    if item.mode == 'w':
        stmt = insert(table).values(**item.model_dump())
        session.execute(stmt)
        session.commit()
    elif engine.connect().execute(select(table).where(table.columns.pid == item.pid)).first():
        stmt = update(table).where(table.columns.pid == item.pid).values(args)
        session.execute(stmt)
        session.commit()
    elif engine.connect().execute(
            select(table).where(table.columns.name == item.name, item.mode == table.columns.mode)).first():
        stmt = update(table).where(table.columns.name == item.name, item.mode == table.columns.mode).values(args)
        session.execute(stmt)
        session.commit()
    else:
        stmt = insert(table).values(**item.model_dump())
        session.execute(stmt)
        session.commit()


@app.post('/create/task')
async def create_task(item: CreateData):
    if item.mode != 'w':
        stmt = select(table).where(table.columns.name == item.name, table.columns.mode != 'w')
        result = engine.connect().execute(stmt).first()
        if result or item.name not in os.listdir(item.dir):
            return Response(status_code=status.HTTP_410_GONE)
        if item.crontab:
            cron = CronTab(user='root')
            job = cron.new(command=f'cd {item.dir};python3 {item.name} mode={item.mode} task_count={item.task_count}',
                           comment=f'{item.name}')
            job.setall(f'{item.crontab}')
            cron.write()
            args = {key: value for key, value in item.model_dump().items() if value is not None}
            args['next_time'] = croniter(item.crontab, datetime.now()).get_next(datetime).strftime(
                '%Y-%m-%d %H:%M:%S')
            stmt = insert(table).values(args)
            session.execute(stmt)
            session.commit()
            return
    subprocess.Popen(rf'cd {item.dir};python3 {item.name} mode={item.mode} task_count={item.task_count}', shell=True)


@app.post('/delete/queue')
async def delete_queue(item: TaskData):
    connection, channel = await scheduler.connect()
    subprocess.Popen(f'kill -9 {item.pid}', shell=True).wait()
    cron = CronTab(user='root')
    job = cron.find_comment(item.name)
    cron.remove(job)
    cron.write()
    stmt = delete(table).where(table.columns.pid == item.pid)
    session.execute(stmt)
    session.commit()
    await connection.close()
    await channel.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
