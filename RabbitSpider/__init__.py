import os
import sys
from RabbitSpider.items.item import BaseItem
from RabbitSpider.http.request import Request
from RabbitSpider.http.response import Response
from RabbitSpider.rabbit_execute import go, batch_go


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

__all__ = ['Request', 'Response', 'BaseItem', 'go', 'batch_go']
__author__ = '一纸'
__email__ = '2395396520@qq.com'
__version__ = '2.7.7'

sys.stdout.write(f'\033[0;35;1m{logo}\033[0m')
