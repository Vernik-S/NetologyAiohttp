import logging
import json
from typing import Union, Optional

from aiohttp import web
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select

import pydantic

DSN = "postgresql+asyncpg://app:1234@127.0.0.1:5431/netology_flask"

engine = create_async_engine(DSN)
Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

app = web.Application()
Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    nickname = Column(String(50), unique=True, nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String, nullable=False)

    advs = relationship("Adv", backref='owner')


class Adv(Base):
    __tablename__ = "adv"

    id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)
    desc = Column(String)
    owner_id = Column(Integer, ForeignKey("user.id"))
    # user = relationship(User)
    created_at = Column(DateTime, server_default=func.now())


class HTTPError(web.HTTPException):
    def __init__(self, error_message: Union[str, dict]):
        message = json.dumps({"status": "error", "description": error_message})
        super().__init__(text=message, content_type="applications/json")


class NotFound(HTTPError):
    status_code = 404

class BadRequest(HTTPError):
    status_code = 400


# @app.errorhandler(HTTPError)
# def handle_invalid_usage(error):
#     response = jsonify({"message": error.message})
#     response.status_code = error.status_code
#     return response


async def get_user(user_name: str, session: Session) -> User:
    #user = await session.query(User).filter(User.nickname == user_name).first()
    result = await session.execute(select(User).filter(User.nickname == user_name))
    user = result.scalars().first()
    #print(user)
    if user is None:
        raise BadRequest( f"user {user_name} not found ")
    return user


# убрать дублирование get?
async def get_adv(adv_id: int, session: Session) -> Adv:
    print(adv_id)
    adv = await session.get(Adv, adv_id)
    if adv is None:
        raise NotFound(error_message=f"adv_id {adv_id} not found ")
        # raise HTTPError(status_code=404, error_message=f"adv_id {adv_id} not found ")
    return adv


class CreateAdvSchema(pydantic.BaseModel):
    title: str
    desc: str
    owner: str

    @pydantic.validator("title")
    def check_title(cls, value):
        if len(value) <= 10:
            raise ValueError("title is too short")
        elif len(value) > 50:
            raise ValueError("title is too long")
        return value


class UpdateAdvSchema(pydantic.BaseModel):
    title: Optional[str]
    desc: Optional[str]

    # owner: Optional[str] #При патче владельца менять нельзя. Таким образом, owner в validated_data не будет

    @pydantic.validator("title")
    def check_title(cls, value):
        if len(value) <= 10:
            raise ValueError("title is too short")
        elif len(value) > 50:
            raise ValueError("title is too long")

        return value


def validate(Schema, data: dict):
    try:
        data_validated = Schema(**data).dict(exclude_none=True)
    except pydantic.ValidationError as er:
        raise BadRequest( er.errors())
    return data_validated


class AdvView(web.View):
    async def get(self):
        adv_id = int(self.request.match_info["adv_id"])

        async with Session() as session:
            print(adv_id)
            adv = await get_adv(adv_id, session)

            #owner = await session.query(User).get(adv.owner_id)
            owner = await session.get(User, adv.owner_id)

        # return jsonify(**dict(adv)) #Можно ли распаковать?

        return web.json_response(
            {"title": adv.title, "description": adv.desc, "owner": owner.nickname,
             "created_at": adv.created_at.isoformat()})

    async def post(self):
        json_data = await self.request.json()
        json_data_validated = validate(CreateAdvSchema, json_data)

        async with Session() as session:
            user_name = json_data_validated.pop("owner")
            user = await get_user(user_name, session)
            json_data_validated["owner_id"] = user.id
            new_adv = Adv(**json_data_validated)

            session.add(new_adv)

            await session.commit()



            return web.json_response({"status": "success", "id": new_adv.id})


    async def patch(self):
        adv_id = int(self.request.match_info["adv_id"])
        json_data = await self.request.json()
        json_data_validated = validate(UpdateAdvSchema, json_data)
        #print(json_data_validated)
        async with Session() as session:
            adv = await get_adv(adv_id, session)

            for key, value in json_data_validated.items():
                setattr(adv, key, value)
            session.add(adv)
            await session.commit()

            return web.json_response({"title": adv.title, "description": adv.desc})
    #
    async def delete(self):
        adv_id = int(self.request.match_info["adv_id"])
        async with Session() as session:
            adv = await get_adv(adv_id, session)
            await session.delete(adv)
            await session.commit()

        return web.json_response(f"Adv with id {adv_id} deleted")






async def init_orm(app):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()
    yield
    await engine.dispose()


app.router.add_route("GET", '/adv/{adv_id:\d+}', AdvView)
app.router.add_route("DELETE", '/adv/{adv_id:\d+}', AdvView)
app.router.add_route("PATCH", '/adv/{adv_id:\d+}', AdvView)
app.router.add_route("POST", '/adv/', AdvView)
app.cleanup_ctx.append(init_orm)
logging.basicConfig(level=logging.DEBUG)
web.run_app(app)
