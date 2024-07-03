from typing import Optional
import asyncio
import pandas as pd
from sqlalchemy import create_engine
from model import *
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


class DatabaseService():
    role_dict = {'user': 1, 'admin': 2, 'banned': 3}

    def __init__(self, user: str, password: str):
        self.user = user
        self.password = password

    async def create_engine(self):
        self.engine = create_async_engine("postgresql+asyncpg://" + self.user + ":" + self.password + "@localhost/practice")

    def create_db(self):
        Base.metadata.create_all(create_engine("postgresql+asyncpg://" + self.user + ":" + self.password + "@localhost/practice"))

    async def add_roles(self):
        async with AsyncSession(self.engine) as session:
            user = Role(role_name="user")
            admin = Role(role_name="admin")
            banned = Role(role_name="banned")
            await session.add_all([user, admin, banned])
            await session.commit()

    async def add_user(self, username: str, role: str, token_balance=5):
        async with AsyncSession(self.engine) as session:
            user = User(
                username=username,
                role_id=self.role_dict[role],
                token_balance=token_balance)
            await session.add(user)
            await session.commit()

    async def add_request(self, user_id: int, video_url: str, video_information: str, message_id: int, characteristics: str, summary: str):
        async with AsyncSession(self.engine) as session:
            request = Request(
                user_id=user_id,
                video_url=video_url,
                video_information=video_information,
                message_id=message_id,
                characteristics=characteristics,
                summary=summary)
            await session.add(request)
            await session.commit()

    #unique user_id
    async def add_token_request(self, user_id: int, amount: int):
        async with AsyncSession(self.engine) as session:
            token_request = TokenRequest(
                user_id=user_id,
                amount=amount)
            await session.add(token_request)
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
            request = await session.query(Request).filter(Request.video_url == video_url).order_by(Request.datetime.desc()).first()
            return request

    async def get_request_by_user_id(self, user_id: int) -> Request:
        async with AsyncSession(self.engine) as session:
            request = await session.query(Request).filter(Request.user_id == user_id).order_by(Request.datetime.desc()).first()
            return request

    #by user_id
    async def get_requests(self) -> list[Request]:
        async with AsyncSession(self.engine) as session:
            requests = await session.query(Request).all()
            return requests

    async def get_favourite_requests(self) -> list[Request]:
        async with AsyncSession(self.engine) as session:
            requests = await session.query(Request).filter(Request.is_favourite).all()
            return requests

    async def get_token_requests(self) -> list[TokenRequest]:
        async with AsyncSession(self.engine) as session:
            token_requests = await session.query(TokenRequest).all()
            return token_requests

    async def get_token_request(self, token_request_id) -> TokenRequest:
        async with AsyncSession(self.engine) as session:
            token_request = await session.get(TokenRequest, token_request_id)
            return token_request

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

    async def change_favourite(self, request_id: int, is_favourite: bool):
        async with Session(self.engine) as session:
            request = await session.get(Request, request_id)
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




#service = DatabaseService("root", "123")
#service.create_db()
#service.add_user("fazylov_v", "admin", 100)
#service.add_user("chel", "banned", 0)
#print(service.get_user_by_id(1).__repr__())
#print(service.get_request_by_user_id(1))
#print(service.get_user(1))

