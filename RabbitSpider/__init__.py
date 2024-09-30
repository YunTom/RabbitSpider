import asyncio
import os
import sys
from RabbitSpider.http.request import Request
from RabbitSpider.http.response import Response
from RabbitSpider.rabbit_execute import go, batch_go

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.append(os.path.abspath(os.path.join(os.path.abspath(sys.argv[0]), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(sys.argv[0]), '../..')))
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(sys.argv[0]), '../../..')))
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(sys.argv[0]), '../../../..')))

logo = r"""
    ____             __      __      _    __    _____             _        __              
   / __ \  ____ _   / /_    / /_    (_)  / /_  / ___/    ____    (_)  ____/ /  ___    _____
  / /_/ / / __ `/  / __ \  / __ \  / /  / __/  \__ \    / __ \  / /  / __  /  / _ \  / ___/
 / _, _/ / /_/ /  / /_/ / / /_/ / / /  / /_   ___/ /   / /_/ / / /  / /_/ /  /  __/ / /    
/_/ |_|  \__,_/  /_.___/ /_.___/ /_/   \__/  /____/   / .___/ /_/   \__,_/   \___/ /_/     
                                                     /_/                                   
"""
sys.stdout.write(f'\033[0;35;1m{logo}\033[0m')
