from quart import Quart, request, jsonify
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select
from models import User, Team, Base
import config
import asyncio

app = Quart(__name__)

engine = create_async_engine(url=config.DATABASE_URL, echo=True)
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Инициализация базы данных
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Семафор для ограничения одновременного доступа
db_semaphore = asyncio.Semaphore(1)

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

# Обработка POST-запроса с результатами игры
@app.route('/update_score', methods=['POST'])
async def update_score():
    data = await request.get_json()
    async with db_semaphore:
        try:
            user_id = data['user_id']
            score = data['score']
            async with async_session() as session:
                result = await session.execute(select(User).where(User.user_id == user_id))
                user = result.scalar_one_or_none()
                if user:
                    team_id = user.team_id
                    await update_user_score(user_id, score)
                    await update_team_score(team_id, score)
                    return jsonify({"success": True}), 200
                else:
                    return jsonify({"error": "User not found"}), 404
        except KeyError as e:
            return jsonify({"error": f"Missing key in JSON data: {str(e)}"}), 400

if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    # loop.run_until_complete(init_db())
    app.run(host='0.0.0.0', port=5000)