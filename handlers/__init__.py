# Файл __init__.py.py позволяет обращаться к папке как к модулю
# и импортировать из него содержимое

from .handlers import router as router_base
from .callbacks import router as router_callbacks
from .bot_commands import set_my_commands
from .logging_config import set_up_logger

# Просто список/кортеж с роутерами
all_routers = (router_base, router_callbacks)
