import asyncio
from typing import Optional

import yadisk
from db import async_session, User, Folder


class YaDiskManager:
    """Business logic class for working with Yandex Disk."""

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token
        self.disk = yadisk.AsyncClient(token=token) if token else None

    def __repr__(self) -> str:  # magic method
        return f"YaDiskManager(token={'set' if self.token else 'unset'})"

    async def check_token(self) -> bool:
        """Validate stored token."""
        if not self.disk:
            return False
        return await self.disk.check_token()

    async def save_token(self, user_id: int, token: str) -> None:
        """Save token for user in DB and reinitialize client."""
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
        """Register folder path for tutor."""
        async with async_session() as session:
            session.add(Folder(tutor_id=tutor_id, path=path))
            await session.commit()

    async def iter_folders(self, tutor_id: int):
        """Async iterator over folders of a tutor."""
        async with async_session() as session:
            result = await session.execute(
                Folder.__table__.select().where(Folder.tutor_id == tutor_id)
            )
            for row in result.fetchall():
                yield row["path"]

