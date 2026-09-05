import os
import sys
from RabbitSpider.items.item import BaseItem
from RabbitSpider.http.request import Request
from RabbitSpider.http.response import Response
from RabbitSpider.utils.control import SettingManager
from RabbitSpider.utils.log import LogManager

sys.path.append(os.path.abspath(os.path.join(os.path.abspath(sys.argv[0]), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(sys.argv[0]), '../..')))
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(sys.argv[0]), '../../..')))
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(sys.argv[0]), '../../../..')))

settings = SettingManager()
logger = LogManager(settings)

logo = r"""
    ____             __      __      _    __    _____             _        __              
   / __ \  ____ _   / /_    / /_    (_)  / /_  / ___/    ____    (_)  ____/ /  ___    _____
  / /_/ / / __ `/  / __ \  / __ \  / /  / __/  \__ \    / __ \  / /  / __  /  / _ \  / ___/
 / _, _/ / /_/ /  / /_/ / / /_/ / / /  / /_   ___/ /   / /_/ / / /  / /_/ /  /  __/ / /    
/_/ |_|  \__,_/  /_.___/ /_.___/ /_/   \__/  /____/   / .___/ /_/   \__,_/   \___/ /_/     
                                                     /_/                                   
"""

__all__ = ['Request', 'Response', 'BaseItem', 'settings', 'logger']
__author__ = '一纸'
__email__ = '2395396520@qq.com'
__version__ = '3.0.0'

sys.stdout.write(f'\033[0;35;1m{logo}\033[0m')
