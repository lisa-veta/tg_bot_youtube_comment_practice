import calendar
import os
import sys
import tracemalloc

import asyncio

tracemalloc.start()
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import datetime
sys.path.insert(1, os.path.join(sys.path[0], 'C:/Users/Королева/PycharmProjects/tg_youtube_analytics/bot/database'))
from bot.database.db_service import DatabaseService

class Admin:
    def __init__(self, bd: DatabaseService):
        self.bd = bd

    async def plot_user_activity(self, user_id: int):
        df = await self.bd.get_user_requests(user_id)
        user = await self.bd.get_user(user_id)

        df['request_date'] = pd.to_datetime(df['request_date'])

        df_grouped = df.groupby('request_date')['request_count'].sum().reset_index(name='request_count')

        today = datetime.date.today()
        current_day_of_week = today.weekday()

        last_week_start = today - datetime.timedelta(days=current_day_of_week + 7)
        last_week_end = today - datetime.timedelta(days=current_day_of_week)

        dates = pd.date_range(start=last_week_start, end=last_week_end, freq='D')

        df_week = pd.DataFrame({'request_date': dates})
        df_week['request_date'] = pd.to_datetime(df_week['request_date'])

        df_grouped = pd.merge(df_week, df_grouped, on='request_date', how='outer')

        df_grouped['request_count'] = df_grouped['request_count'].fillna(0)

        fig = go.Figure(data=[go.Bar(
            x=df_grouped['request_date'],
            y=df_grouped['request_count'],
            text=df_grouped['request_count'],
            textposition='auto',
            textfont=dict(size=20)
        )])

        fig.update_layout(
            title=f"Активность пользователя {user.username} за последнюю неделю",
            xaxis_title="Дата",
            yaxis_title="Количество запросов",
            xaxis_tickformat="%a %d %b",
            xaxis_tickfont=dict(size=16),
            yaxis_tickfont=dict(size=16),
            title_font=dict(size=20)
        )
        #fig.show()
        return fig

    async def plot_new_users(self, period: str = 'week'): #period: 'week', 'day', 'month'
        users = await self.bd.get_users()

        today = datetime.date.today()
        if period == 'week':
            last_week_start = today - timedelta(days=today.weekday() + 7)
            last_week_end = today
        elif period == 'day':
            last_week_start = today - timedelta(days=1)
            last_week_end = today
        elif period == 'month':
            last_week_start = today - timedelta(days=30)
            last_week_end = today
        else:
            raise ValueError(f"Неверный период: {period}")

        dates = pd.date_range(start=last_week_start, end=last_week_end, freq='D')

        df_week = pd.DataFrame({'date': dates})
        df_week['date'] = pd.to_datetime(df_week['date'])

        registrations_count = {}
        for user in users:
            registration_date = user.date_registration.date()
            if last_week_start <= registration_date <= last_week_end:
                if registration_date in registrations_count:
                    registrations_count[registration_date] += 1
                else:
                    registrations_count[registration_date] = 1

        df_grouped = pd.DataFrame({'date': list(registrations_count.keys()),
                                   'registrations': list(registrations_count.values())})
        df_grouped['date'] = pd.to_datetime(df_grouped['date'])

        df_grouped = pd.merge(df_week, df_grouped, on='date', how='left')
        df_grouped['registrations'] = df_grouped['registrations'].fillna(0)

        fig = go.Figure(data=[go.Bar(
            x=df_grouped['date'],
            y=df_grouped['registrations'],
            text=df_grouped['registrations'],
            textposition='auto',
            textfont=dict(size=16)
        )])

        fig.update_layout(
            title=f"Активность регистрации пользователей за {period}",
            xaxis_title="Дата",
            yaxis_title="Количество новых пользователей",
            xaxis_tickformat="%a %d %b",
            xaxis_tickfont=dict(size=14),
            yaxis_tickfont=dict(size=14),
            title_font=dict(size=20)
        )
        # fig.show()
        return fig

    async def get_bd_statistics(self):
        users = await self.bd.get_users()
        regular_users = [user for user in users if user.role_id == 1]
        admins = [user for user in users if user.role_id == 2]
        banned_users = [user for user in users if user.role_id == 3]
        requests = await self.bd.get_requests()
        return (f"Сводка по объему данных:\n"
                f"Количество запросов : {len(requests)}\n"
                f"Количество пользователей : {len(users)}\n"
                f"Из них : \n"
                f"\tАктивных : {len(regular_users)}\n"
                f"\tЗаблокированных: {len(banned_users)}\n"
                f"\tАдминистраторов : {len(admins)}\n")

        filename = f"registration_activity_{period}.png"
        fig.write_image(filename)

        return filename

# async def main():
#     db = DatabaseService('postgres', '20i16t04s')
#     await db.create_engine()
#     admin = Admin(db)
#     #admin.plot_user_activity(1)
#     #admin.plot_new_users(period='week')
#     # await admin.plot_new_users('day')
#     print(await admin.plot_user_activity(938091580))
#
# if __name__ == "__main__":
#     asyncio.run(main())


