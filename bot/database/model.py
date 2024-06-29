#Модуль для работы с базой данных
from sqlalchemy import create_engine, DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, TEXT, BIGINT

class Base(DeclarativeBase):
    pass

class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String(15))
    def __repr__(self) -> str:
        return f"Role(id={self.id}, role_name={self.role_name})"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    username: Mapped[str] = mapped_column(String(30), nullable=False)
    token_balance: Mapped[int] = mapped_column(default=5)
    data_registration: Mapped[DateTime] = mapped_column(TIMESTAMP, server_default=func.now())

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, role_id={self.role_id!r}, " \
               f"username={self.username!r}, token_balance={self.token_balance}, " \
               f"data_registration={self.data_registration})"

class TokenRequest(Base):
    __tablename__ = "token_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[int] = mapped_column()
    datetime: Mapped[DateTime] = mapped_column(TIMESTAMP, server_default=func.now())

    def __repr__(self) -> str:
        return f"TokenRequest(id={self.id}, user_id={self.user_id}, amount={self.amount}, datetime={self.datetime}"


class Request(Base):
    __tablename__ = "requests"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    video_url: Mapped[str] = mapped_column(String(200), nullable=False)
    is_favourite: Mapped[bool] = mapped_column(default=False)
    datetime: Mapped[DateTime] = mapped_column(TIMESTAMP, server_default=func.now())
    video_information: Mapped[str] = mapped_column(JSONB, nullable=False)
    message_id: Mapped[int] = mapped_column()
    characteristics: Mapped[str] = mapped_column(JSONB, nullable=True)
    summary: Mapped[str] = mapped_column(TEXT, nullable=True)

    def __repr__(self) -> str:
        return f"Request(id={self.id}, user_id={self.user_id}, " \
               f"video_url={self.video_url}, is_favourite={self.is_favourite}, " \
               f"datetime={self.datetime}, video_information={self.video_information}, message_id={self.message_id})"

# class Data(Base):
#     __tablename__ = "data"
#
#     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), unique=True)
#     characteristics: Mapped[str] = mapped_column(JSONB, nullable=True)
#     summary: Mapped[str] = mapped_column(TEXT, nullable=True)
#
#     def  __repr__(self) -> str:
#         return f"Characteristics(request_id={self.request_id}, is_paid={self.is_paid}, data={self.data})"

# class Summary(Base):
#     __tablename__ = "summary"
#
#     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), unique=True)
#     data: Mapped[str] = mapped_column(TEXT, nullable=True)
#     is_paid: Mapped[bool] = mapped_column(default=False)
#
#     def __repr__(self) -> str:
#         return f"Summary(request_id={self.request_id}, is_paid={self.is_paid}, data={self.data})"


# class TonalityModel(Base):
#     __tablename__ = "tonality"
#
#     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), unique=True)
#     data: Mapped[str] = mapped_column(JSONB, nullable=True)
#     is_paid: Mapped[bool] = mapped_column(default=False)
#
#     def __repr__(self) -> str:
#         return f"Tonality(request_id={self.request_id}, is_paid={self.is_paid}, data={self.data})"
#
# class VideoModel(Base):
#     __tablename__ = "videos"
#     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     video_name: Mapped[str] = mapped_column(String(200), nullable=False)
#     video_url: Mapped[str] = mapped_column(String(200), nullable=False)
#
#     def __repr__(self) -> str:
#         return f"Video(id={self.id}, video_name={self.video_name}, video_url={self.video_url}"