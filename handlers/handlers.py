import logging
import secrets
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from db import async_session
from db.models import User
from script.classes import YaDiskManager
from handlers.keyboard import main_keyboard_start

router = Router()
yd_manager = YaDiskManager()


@router.callback_query(F.data == "continue_button")
async def callback_continue(callback: types.CallbackQuery):
    await callback.message.answer(text="Успешно вызван callback!")
    if hasattr(callback, "answer"):
        try:
            await callback.answer()  # type: ignore[func-returns-value]
        except TypeError:
            callback.answer()

class RegisterStates(StatesGroup):
    choosing_role = State()
    entering_tutor_code = State()

@router.message(Command("start"))
async def process_start_command(message: types.Message, state: FSMContext | None = None):
    if state:
        await state.clear()
    await message.reply(
        f"ID{message.from_user.id}, User: {message.from_user.username}",
        reply_markup=main_keyboard_start,
    )
    if state:
        await state.set_state(RegisterStates.choosing_role)

@router.message(Command("status"))
async def process_status_command(message: types.Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == message.from_user.id))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("Вы не зарегистрированы. Нажмите /start")
            return

        if user.tutorcode:
            await message.answer(
                f"Вы — преподаватель:\n"
                f"ID: {user.user_id}\n"
                f"Username: @{user.username or 'не задан'}\n"
                f"Код для студентов: `{user.tutorcode}`",
                parse_mode="Markdown"
            )
        elif user.subscribe:
            # получаем данные преподавателя
            result = await session.execute(select(User).where(User.user_id == user.subscribe))
            teacher = result.scalar_one_or_none()

            if teacher:
                await message.answer(
                    f"Вы — слушатель:\n"
                    f"ID: {user.user_id}\n"
                    f"Username: @{user.username or 'не задан'}\n"
                    f"Подписан на преподавателя: @{teacher.username or 'не задан'}"
                )
            else:
                await message.answer(
                    f"Вы — слушатель, но преподаватель с ID {user.subscribe} не найден."
                )
        else:
            await message.answer("Невозможно определить ваш статус.")

        if user.token:
            await message.answer(f"Ваш токен Яндекс Диска: {user.token}")
        else:
            await message.answer("Токен Яндекс Диска не задан. Используйте /register")


@router.message(Command("register"))
async def process_register_command(message: types.Message):
    instructions = (
        "Процесс получения токена Яндекс Диска:\n"
        "1. Перейдите по ссылке https://oauth.yandex.ru/client/new\n"
        "2. Создайте приложение, выберите 'Веб-сервисы' и укажите Redirect URI https://oauth.yandex.ru/verification_code\n"
        "3. Отметьте права доступа к диску, затем получите client_id.\n"
        "4. Перейдите по ссылке https://oauth.yandex.ru/authorize?response_type=token&client_id=<ВАШ client_id>\n"
        "5. Полученный токен отправьте командой /token <ваш_токен>"
    )
    await message.answer(instructions)


@router.message(Command("token"))
async def process_token_command(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Укажите токен после команды /token")
        return
    token = parts[1].strip()
    await yd_manager.save_token(message.from_user.id, token)
    if await yd_manager.check_token():
        await message.answer("Токен сохранен и проверен")
    else:
        await message.answer("Не удалось проверить токен")


@router.message(Command("upload"))
async def process_upload_command(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Укажите путь к папке после команды /upload")
        return
    folder = parts[1].strip()
    await yd_manager.add_folder(message.from_user.id, folder)
    await message.answer(f"Папка {folder} добавлена в отслеживаемые")
    async with async_session() as session:
        result = await session.execute(select(User.user_id).where(User.subscribe == message.from_user.id))
        students = [row[0] for row in result.fetchall()]
    for stud in students:
        try:
            await message.bot.send_message(stud, f"Преподаватель начал отслеживать папку: {folder}")
        except Exception:
            logging.warning(f"Не удалось уведомить пользователя {stud}")


@router.message(Command("help"))
async def process_help_command(message: types.Message):
    help_text = (
        "🤖 *Список команд бота:*\n\n"
        "/start — начать работу, выбрать роль (студент/преподаватель)\n"
        "/status — узнать ваш текущий статус и настройки\n"
        "/help — показать это справочное сообщение\n\n"
        "📁 *Для преподавателей:*\n"
        "/token — сохранить OAuth-токен Яндекс.Диска\n"
        "/upload — загрузить присланный файл на ваш Я.Диск\n"
    )
    await message.answer(help_text, parse_mode="Markdown")

@router.callback_query(F.data == "button_student")
async def handle_student(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите код преподавателя (введите текстом):")
    await state.set_state(RegisterStates.entering_tutor_code)
    await callback.answer()

@router.message(RegisterStates.entering_tutor_code)
async def process_tutor_code(message: types.Message, state: FSMContext):
    code = message.text.strip()

    async with async_session() as session:
        result = await session.execute(select(User).where(User.tutorcode == code))
        tutor = result.scalar_one_or_none()

        if tutor:
            existing = await session.execute(select(User).where(User.user_id == message.from_user.id))
            user_obj = existing.scalar_one_or_none()

            if user_obj:
                user_obj.subscribe = tutor.user_id
                user_obj.tutorcode = None
            else:
                session.add(User(
                    user_id=message.from_user.id,
                    username=message.from_user.username or "no_username",
                    subscribe=tutor.user_id
                ))

            await session.commit()
            await message.answer(f"Вы зарегистрированы как слушатель преподавателя @{tutor.username}")
            await state.clear()
        else:
            await message.answer("Неверный код. Попробуйте снова:")


@router.callback_query(F.data == "button_tutor")
async def handle_tutor(callback: types.CallbackQuery, state: FSMContext):
    user = callback.from_user
    tutorcode = f"TUT{user.id}"
    username_value = user.username or "no_username"

    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user.id))
        existing = result.scalar_one_or_none()

        if existing:
            existing.tutorcode = tutorcode
            existing.subscribe = None
        else:
            session.add(User(
                user_id=user.id,
                username=username_value,
                tutorcode=tutorcode
            ))
            await session.commit()

    await callback.message.answer(
        f"Вы выбрали роль: *Преподаватель*.\n\n"
        f"Ваш ID: `{user.id}`\n"
        f"Username: @{user.username or '—'}\n"
        f"Код преподавателя: `TUT{user.id}`",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message()
async def echo_message(message: types.Message):
    await message.answer(f"Вы написали: {message.text}")
