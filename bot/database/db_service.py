import json
from typing import Optional, Tuple, Sequence, List
import asyncio
import pandas as pd
import requests.compat
from sqlalchemy import create_engine, select, Result, ScalarResult


# from bot.database.model import Request
from model import *
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
class DatabaseService():
    role_dict = {'user': 1, 'admin': 2, 'banned': 3}

    def __init__(self, user: str, password: str):
        self.engine = None
        self.user = user
        self.password = password
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine, class_=AsyncSession
        )

    async def create_engine(self):
        try:
            self.engine = create_async_engine(
                "postgresql+asyncpg://" + self.user + ":" + self.password + "@localhost/practice")
        except Exception as e:
            print(f"Error creating engine: {e}")

    # async def create_db(self):
    #     try:
    #         Base.metadata.create_all(self.engine)
    #         print("Tables created successfully.")
    #     except Exception as e:
    #         print(f"Error creating tables: {e}")
    # def create_sync_engine(self):
    #     # Создаем синхронный движок
    #     sync_engine = create_engine("postgresql+psycopg2://" + self.user + ":" + self.password + "@localhost/practice")
    #     return sync_engine
    #
    # def create_db(self):
    #     try:
    #         # Используем синхронный движок для создания таблиц
    #         sync_engine = self.create_sync_engine()
    #         Base.metadata.create_all(sync_engine)
    #         print("Tables created successfully.")
    #     except Exception as e:
    #         print(f"Error creating tables: {e}")
    async def add_roles(self):
        async with AsyncSession(self.engine) as session:
            user = Role(role_name="user")
            admin = Role(role_name="admin")
            banned = Role(role_name="banned")
            session.add_all([user, admin, banned])
            await session.commit()

    async def add_user(self, user_id: int, username: str, role: str, token_balance=5):
        async with AsyncSession(self.engine) as session:
            user = User(
                id = user_id,
                username=username,
                role_id=self.role_dict[role],
                token_balance=token_balance)
            session.add(user)
            await session.commit()

    async def add_request(self, user_id: int, video_url: str, video_information: dict, message_id: int,
                          characteristics: dict, summary: str):
        async with AsyncSession(self.engine) as session:
            # Проверяем количество реквестов у пользователя
            requests_count = await session.execute(
                select(func.count(Request.id)).where(Request.user_id == user_id))
            requests_count = requests_count.scalar()
            if requests_count >= 20:
                # Находим самый поздний реквест
                latest_request = await session.execute(
                    select(Request).where(Request.user_id == user_id).order_by(Request.datetime.asc()))
                latest_request = latest_request.scalars().first()
                count = 19
                # Проверяем, является ли он избранным
                while latest_request.is_favourite:
                    # Находим предпоследний реквест
                    latest_request = await session.execute(
                        select(Request).where(Request.user_id == user_id).order_by(
                            Request.datetime.asc()).offset(count))
                    latest_request = latest_request.scalars().first()
                    count -= 1
                await session.delete(latest_request)
            video_information_str = json.dumps(video_information)
            request = Request(
                user_id=user_id,
                video_url=video_url,
                video_information=video_information_str,
                message_id=message_id,
                characteristics=characteristics,
                summary=summary)
            session.add(request)
            await session.commit()

    #unique user_id
    async def add_token_request(self, user_id: int, amount: int):
        async with AsyncSession(self.engine) as session:
            token_request = TokenRequest(
                user_id=user_id,
                amount=amount)
            session.add(token_request)
            await session.commit()

    async def get_user(self, user_id: int) -> User:
        async with AsyncSession(self.engine) as session:
            user = await session.get(User, user_id)
            return user

    async def get_tokens_and_role(self, user_id: int) -> (int, str):
        async with AsyncSession(self.engine) as session:
            user = await session.get(User, user_id)
            role_name = ''
            for k, v in self.role_dict:
                if user.role_id == v:
                    role_name = k

            return user.token_balance, role_name

    async def get_users(self) -> list[User]:
        async with AsyncSession(self.engine) as session:
            users = await session.query(User).all()
            return users

    async def get_request(self, request_id: int) -> Request:
        async with AsyncSession(self.engine) as session:
            request = await session.get(Request, request_id)
            return request

    async def get_request_by_url(self, video_url: str) -> Request:
        async with AsyncSession(self.engine) as session:
            statement = select(Request).where(Request.video_url == video_url).order_by(Request.datetime.desc())
            result = await session.execute(statement)
            request = result.scalars().first()
            return request

    async def get_request_by_user_id(self, user_id: int) -> Request:
        async with AsyncSession(self.engine) as session:
            request = await session.query(Request).filter(Request.user_id == user_id).order_by(
                Request.datetime.desc()).first()
            return request

    #by user_id
    async def get_requests(self) -> list[Request]:
        async with AsyncSession(self.engine) as session:
            requests = await session.query(Request).all()
            return requests
    async def get_request_by_id_20(self, user_id: int) -> list[Request]:
        async with AsyncSession(self.engine) as session:
            requests = await session.execute(select(Request).where(Request.user_id == user_id).order_by(Request.datetime.desc()).limit(20))
            requests = list(requests.scalars().all())
            return requests
            # return [list(row) for row in requests]

    async def get_user_favourites(self, user_id: int) -> list[Request]:
        async with AsyncSession(self.engine) as session:
            requests = await session.execute((select(Request).where(Request.user_id == user_id,
                                                                                      Request.is_favourite).order_by(Request.datetime.desc())).limit(5))
            requests = list(requests.scalars().all())
            return requests
    async def get_user_favourite_by_m_id(self, user_id: int, message_id) -> list[Request]:
        async with AsyncSession(self.engine) as session:
            requests = await session.execute((select(Request.video_information).where(Request.message_id == message_id,
                                                                                      Request.is_favourite)))
            requests = list(requests.scalars().all())
            return requests

    #добавила по айди
    async def get_favourite_requests(self, user_id) -> list[Request]:
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(Request).where(Request.is_favourite, Request.user_id == user_id))
            requests = result.scalars().all()
            return requests

    async def get_token_request(self, token_request_id) -> TokenRequest:
        async with AsyncSession(self.engine) as session:
            token_request = await session.get(TokenRequest, token_request_id)
            return token_request

    async def get_token_requests(self) -> list[TokenRequest]:
        async with AsyncSession(self.engine) as session:
            token_requests = await session.query(TokenRequest).all()
            return token_requests

    async def get_user_requests(self, user_id: int) -> pd.DataFrame:
        async with self.engine.connect() as conn:
            query = f"""
                SELECT 
                    date(datetime) AS request_date,
                    COUNT(*) AS request_count
                FROM public.requests
                WHERE user_id = {user_id}
                AND datetime >= CURRENT_DATE - INTERVAL '7 day' 
                GROUP BY request_date
                ORDER BY request_date;
            """
            df = await pd.read_sql(query, conn)
        return df
    async def add_tokens(self, user_id: int, amount: int):
        async with AsyncSession(self.engine) as session:
            user = await session.get(User, user_id)
            user.token_balance = amount
            await session.commit()

    async def can_request(self, user_id: int) -> bool:
        async with AsyncSession(self.engine) as session:
            user = await session.get(User, user_id)
            if user.token_balance > 0:
                return True
            return False

    async def minus_token(self, user_id: int):
        async with AsyncSession(self.engine) as session:
            user = await session.get(User, user_id)
            user.token_balance -= 1
            await session.commit()

    async def change_role(self, user_id: int, role: str):
        async with AsyncSession(self.engine) as session:
            user = await session.get(User, user_id)
            user.role_id = self.role_dict[role]
            await session.commit()

    async def check_add_favourite(self, request_id: int):
        async with AsyncSession(self.engine) as session:
            amount = await session.query()

    async def change_last_request_favourite(self, user_id: int, video_url: str, is_favourite: bool):
        async with Session(self.engine) as session:
            request = request = await session.execute(select(Request).where(Request.user_id == user_id,
                Request.video_url == video_url).order_by(Request.datetime.desc()).one())
            request.is_favourite = is_favourite
            await session.commit()

    async def change_favourite_flag(self, message_id: int, is_favourite: bool):
        async with AsyncSession(self.engine) as session:
            request = await session.execute(select(Request).where(Request.message_id == message_id))
            request = request.scalars().one()
            request.is_favourite = is_favourite
            await session.commit()

    async def delete_user(self, user_id: int):
        async with Session(self.engine) as session:
            user = await session.get(User, user_id)
            await session.delete(user)
            await session.commit()

    async def delete_token_request(self, token_request_id: int):
        async with Session(self.engine) as session:
            token_request = await session.get(TokenRequest, token_request_id)
            await session.delete(token_request)
            await session.commit()

    async def accept_token_request(self, token_request_id: int):
        token_request = await self.get_token_request(token_request_id)
        amount = token_request.amount
        user_id = token_request.user_id
        await self.add_tokens(user_id, amount)
        await self.delete_token_request(token_request_id)

    async def reject_token_request(self, token_request_id: int):
        await self.delete_token_request(token_request_id)



# async def main():
#     user = 'postgres'
#     password = '20i16t04s'
#
#     db_service = DatabaseService(user=user, password=password)
#
#     # # Создаем синхронный движок и таблицы
#     # db_service.create_db()
#
#     # Создаем асинхронный движок для дальнейших операций
#     await db_service.create_engine()
#     await db_service.add_roles()
#     await db_service.change_favourite_flag(3942, False)
#     print(await db_service.get_user_favourite_by_m_id(938091580, 3942))

#if __name__ == '__main__':
 #   asyncio.run(main())


# Создание базы данных (синхронный вызов)
# db_service.create_db()



    # rec = Request()
# rec = service.get_request_by_url("https://www.youtube.com/watch?v=nIkH6C3_CX8")
# print(rec.characteristics["characteristics"])
#
# service.create_db()
# service.add_user("fazylov_v", "admin", 100)
# service.add_user("chel", "banned", 0)
# print(service.get_user_by_id(1).__repr__())
# print(service.get_request_by_user_id(1))
# print(service.get_user(1))

