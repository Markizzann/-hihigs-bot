import asyncio
from typing import Optional

import yadisk
from db import async_session, User, Folder

class YaDiskManager:
    """Класс бизнес-логики для работы с Яндекс Диском."""

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token
        self.disk = yadisk.AsyncClient(token=token) if token else None

    def __repr__(self) -> str:  # magic method
        return f"YaDiskManager(token={'set' if self.token else 'unset'})"

    async def check_token(self) -> bool:
        """Проверка валидности (пригодности) токена."""
        if not self.disk:
            return False
        return await self.disk.check_token()

    async def save_token(self, user_id: int, token: str) -> None:
        """Сохраняет токен пользователя в базу и обновляет."""
        async with async_session() as session:
            result = await session.get(User, user_id)
            if result:
                result.token = token
            else:
                session.add(User(user_id=user_id, username="anon", token=token))
            await session.commit()
        self.token = token
        self.disk = yadisk.AsyncClient(token=token)

    async def add_folder(self, tutor_id: int, path: str) -> None:
        """Добавляет путь к папке для преподавателя."""
        async with async_session() as session:
            session.add(Folder(tutor_id=tutor_id, path=path))
            await session.commit()

    async def iter_folders(self, tutor_id: int):
        """Асинхронный итератор над папками репетитора (Показывает все папки преподавателя одну за другой)."""
        async with async_session() as session:
            result = await session.execute(
                Folder.__table__.select().where(Folder.tutor_id == tutor_id)
            )
            for row in result.fetchall():
                yield row["path"]
