from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram import Router

router = Router()

async def set_my_commands(bot):
    commands = [
        BotCommand(command="start", description="Старт и выбор роли"),
        BotCommand(command="status", description="Узнать текущий статус"),
        BotCommand(command="help", description="Справка по командам"),
        BotCommand(command="token", description="Сохранить токен Яндекс.Диска"),
        BotCommand(command="upload", description="Загрузить файл на Я.Диск"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())
