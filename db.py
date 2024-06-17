import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select, update, delete
from sqlalchemy.orm import sessionmaker
from models import User,Team, Base
import config


engine = create_async_engine(url = config.DATABASE_URL, echo=True)

async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def add_user(user_id: int, username: str, first_name: str, last_name: str, team_id: int):
    async with async_session() as session:
        async with session.begin():
            team = await session.get(Team, team_id)
            user = User(user_id=user_id, username=username, first_name=first_name, last_name=last_name, team=team)
            session.add(user)
            await session.commit()


COMANDS_NAME = ["SHIBA", "DOGE", "PEPE", "BRETT", "GORILLA", "PANDA", "MEMEAI", "WOJAK", "STRUMP", "etc"]
async def create_teams():
    async with async_session() as session:
        async with session.begin():
            for i in range(10):
                team_name = f"{COMANDS_NAME[i]}"
                team = await session.execute(select(Team).where(Team.name == team_name))
                team = team.scalar_one_or_none()
                if not team:
                    team = Team(name=team_name)
                    session.add(team)
            await session.commit()

async def user_exists(user_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        return user is not None


async def get_user_profile(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            team = await session.get(Team, user.team_id)
            return {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "points": user.points,
                "team_name": team.name,
                "team_points": team.points
            }
        return None

async def get_rating_table():
    async with async_session() as session:
        result = await session.execute(select(Team).order_by(Team.points.desc()))
        teams = result.scalars().all()
        rating_table = []
        for team in teams:
            team_info = {
                "team_name": team.name,
                "team_points": team.points
            }
            rating_table.append(team_info)
        return rating_table


# Функция обновления очков пользователя
async def update_user_score(user_id: int, score: int):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.points += score
                await session.commit()

# Функция обновления очков команды
async def update_team_score(team_id: int, score: int):
    async with async_session() as session:
        async with session.begin():
            team = await session.get(Team, team_id)
            if team:
                team.points += score
                await session.commit()