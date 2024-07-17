import asyncio
import os
import sys
from RabbitSpider.http.request import Request
from RabbitSpider.http.response import Response
from RabbitSpider.core.engine import Engine

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.append(os.path.abspath(os.path.join(os.path.abspath(sys.argv[0]), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(sys.argv[0]), '../..')))
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(sys.argv[0]), '../../..')))
