import json
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine
from model import *
from sqlalchemy.orm import Session

class DatabaseService():
    role_dict = {'user': 1, 'admin': 2, 'banned': 3}

    def __init__(self, user: str, password: str):
        self.engine = create_engine("postgresql+psycopg2://" + "postgres" + ":" +"Xfq8ybR*" + "@localhost/practice")

    def create_db(self):
        Base.metadata.create_all(self.engine)

    def add_roles(self):
        with Session(self.engine) as session:
            user = Role(role_name="user")
            admin = Role(role_name="admin")
            banned = Role(role_name="banned")
            session.add_all([user, admin, banned])
            session.commit()

    def add_user(self, user_id, username: str, role: str, token_balance=5):
        with Session(self.engine) as session:
            user = User(
                id = user_id,
                username=username,
                role_id=self.role_dict[role],
                token_balance=token_balance)
            session.add(user)
            session.commit()

    def add_request(self, user_id: int, video_url: str, video_information: dict, message_id: int, characteristics: dict, summary: str):
        with Session(self.engine) as session:
            video_information_str = json.dumps(video_information)
            request = Request(
                user_id=user_id,
                video_url=video_url,
                video_information=video_information,
                message_id=message_id,
                characteristics=characteristics,
                summary=summary)
            session.add(request)
            session.commit()

    #unique user_id
    def add_token_request(self, user_id: int, amount: int):
        with Session(self.engine) as session:
            token_request = TokenRequest(
                user_id=user_id,
                amount=amount)
            session.add(token_request)
            session.commit()

    def get_user(self, user_id: int) -> User:
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            return user

    def get_tokens_and_role(self, user_id: int) -> (int, str):
        with Session(self.engine) as session:
            user = session.get(User, user_id)

            role_name = ''
            for k, v in self.role_dict:
                if user.role_id == v:
                    role_name = k

            return user.token_balance, role_name

    def get_users(self) -> list[User]:
        with Session(self.engine) as session:
            users = session.query(User).all()
            return users

    def get_request(self, request_id: int) -> Request:
        with Session(self.engine) as session:
            request = session.get(Request, request_id)
            return request

    def get_request_by_url(self, video_url: str) -> Request:
        with Session(self.engine) as session:
            request = session.query(Request).filter(Request.video_url == video_url).order_by(Request.datetime.desc()).first()
            return request

    def get_request_by_user_id(self, user_id: int) -> Request:
        with Session(self.engine) as session:
            request = session.query(Request).filter(Request.user_id == user_id).order_by(Request.datetime.desc()).first()
            return request

    #by user_id
    def get_requests(self) -> list[Request]:
        with Session(self.engine) as session:
            requests = session.query(Request).all()
            return requests

    def get_favourite_requests(self) -> list[Request]:
        with Session(self.engine) as session:
            requests = session.query(Request).filter(Request.is_favourite).all()
            return requests

    def get_token_requests(self) -> list[TokenRequest]:
        with Session(self.engine) as session:
            token_requests = session.query(TokenRequest).all()
            return token_requests

    def get_token_request(self, token_request_id) -> TokenRequest:
        with Session(self.engine) as session:
            token_request = session.get(TokenRequest, token_request_id)
            return token_request

    def get_user_requests(self, user_id: int) -> pd.DataFrame:
        with self.engine.connect() as conn:
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
            df = pd.read_sql(query, conn)
        return df

    def add_tokens(self, user_id: int, amount: int):
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            user.token_balance = amount
            session.commit()

    def can_request(self, user_id: int) -> bool:
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            if user.token_balance > 0:
                return True
            return False

    def minus_token(self, user_id: int):
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            user.token_balance -= 1
            session.commit()

    def change_role(self, user_id: int, role: str):
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            user.role_id = self.role_dict[role]
            session.commit()

    def check_add_favourite(self, request_id: int):
        with Session(self.engine) as session:
            amount = session.query()

    def change_favourite(self, request_id: int, is_favourite: bool):
        with Session(self.engine) as session:
            request = session.get(Request, request_id)
            request.is_favourite = is_favourite
            session.commit()

    def delete_user(self, user_id: int):
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            session.delete(user)
            session.commit()

    def delete_token_request(self, token_request_id: int):
        with Session(self.engine) as session:
            token_request = session.get(TokenRequest, token_request_id)
            session.delete(token_request)
            session.commit()

    def accept_token_request(self, token_request_id: int):
        token_request = self.get_token_request(token_request_id)
        amount = token_request.amount
        user_id = token_request.user_id
        self.add_tokens(user_id, amount)
        self.delete_token_request(token_request_id)

    def reject_token_request(self, token_request_id: int):
        self.delete_token_request(token_request_id)




# service = DatabaseService("root", "123")
# rec = Request()
# rec = service.get_request_by_url("https://www.youtube.com/watch?v=nIkH6C3_CX8")
# print(rec.characteristics["characteristics"])

# service.create_db()
#service.add_user("fazylov_v", "admin", 100)
#service.add_user("chel", "banned", 0)
#print(service.get_user_by_id(1).__repr__())
#print(service.get_request_by_user_id(1))
#print(service.get_user(1))

