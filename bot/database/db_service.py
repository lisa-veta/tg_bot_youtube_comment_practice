from typing import Optional

from model import *
from sqlalchemy.orm import Session

class DatabaseService():
    role_dict = {'user': 1, 'admin': 2, 'banned': 3}

    def __init__(self, user: str, password: str):
        self.engine = create_engine("postgresql+psycopg2://" + user + ":" + password + "@localhost/practice")

    def create_db(self):
        Base.metadata.create_all(self.engine)

    def add_roles(self):
        with Session(self.engine) as session:
            user = Role(role_name="user")
            admin = Role(role_name="admin")
            banned = Role(role_name="banned")
            session.add_all([user, admin, banned])
            session.commit()

    def add_user(self, username: str, role: str, token_balance=5):
        with Session(self.engine) as session:
            user = User(username=username, role_id=self.role_dict[role], token_balance=token_balance)
            session.add(user)
            session.commit()

    def add_request(self, user_id: int, video_url: str, video_information: str, message_id: int):
        with Session(self.engine) as session:
            request = Request(user_id=user_id, video_url=video_url, video_information=video_information, message_id=message_id)
            session.add(request)
            session.commit()

    def add_token_request(self, user_id: int, amount: int):
        with Session(self.engine) as session:
            token_request = TokenRequest(user_id=user_id, amount=amount)
            session.add(token_request)
            session.commit()

    def add_characteristics(self, request_id: int, data: str):
        with Session(self.engine) as session:
            characteristics = Characteristics(request_id=request_id, data=data, is_paid=True)
            session.add(characteristics)
            session.commit()

    def add_summary(self, request_id: int, data: str):
        with Session(self.engine) as session:
            summary = Summary(request_id=request_id, data=data, is_paid=True)
            session.add(summary)
            session.commit()

    def get_user(self, user_id: int) -> User:
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            return user

    def get_users(self) -> list[User]:
        with Session(self.engine) as session:
            users = session.query(User).all()
            return users

    def get_request(self, request_id: int) -> Request:
        with Session(self.engine) as session:
            request = session.get(Request, request_id)
            return request

    #def get_request_by_url(self):

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

    def get_characteristics(self, request_id: int) -> Optional[Characteristics]:
        with Session(self.engine) as session:
            characteristics = session.query(Characteristics).filter(Characteristics.request_id == request_id).first()
            return characteristics

    def get_summary(self, request_id: int) -> Optional[Summary]:
        with Session(self.engine) as session:
            summary = session.query(Summary).filter(Summary.request_id == request_id).first()
            return summary

    def get_token_requests(self) -> list[TokenRequest]:
        with Session(self.engine) as session:
            token_requests = session.query(TokenRequest).all()
            return token_requests

    def add_tokens(self, user_id: int, amount: int):
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            user.token_balance = amount
            session.commit()

    def change_role(self, user_id: int, role: str):
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            user.role_id = self.role_dict[role]
            session.commit()

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



service = DatabaseService("root", "123")
service.create_db()
#service.add_roles()
#service.add_user("fazylov_v", "admin", 100)
#print(service.get_user_by_id(1).__repr__())
#print(service.get_request_by_user_id(1))
#print(service.get_user(1))
