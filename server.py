import asyncio
import json
from aiohttp import web
from random import randint


from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base, session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import sessionmaker



Base = declarative_base()
async_session = None

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String)
    password = Column(String)
    data = Column(String)
    create_date = Column(DateTime, server_default=func.now())
    orders = relationship("Order", back_populates='user', lazy='subquery')

    # required in order to access columns with server defaults
    # or SQL expression defaults, subsequent to a flush, without
    # triggering an expired load
    __mapper_args__ = {"eager_defaults": True}


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"))
    data = Column(String)
    user = relationship("User", back_populates='orders')


# async def async_main():
    
#     engine = create_async_engine(
#         "sqlite+aiosqlite:///AIOHTTP_REST_FULL_API.db",
#         echo=True,
#     )

#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)
#         await conn.run_sync(Base.metadata.create_all)

#     # expire_on_commit=False will prevent attributes from being expired
#     # after commit.
#     async_session = sessionmaker(
#         engine, expire_on_commit=False, class_=AsyncSession
#     )

#     async with async_session() as session:
#         async with session.begin():
#             session.add_all(
#                 [
#                     A(bs=[B(), B()], data="a1"),
#                     A(bs=[B()], data="a2"),
#                     A(bs=[B(), B()], data="a3"),
#                 ]
#             )

#         stmt = select(A).options(selectinload(A.bs))

#         result = await session.execute(stmt)

#         for a1 in result.scalars():
#             print(a1)
#             print(f"created at: {a1.create_date}")
#             for b1 in a1.bs:
#                 print(b1)

#         result = await session.execute(select(A).order_by(A.id))

#         a1 = result.scalars().first()

#         a1.data = "new data"

#         await session.commit()

#         # access attribute subsequent to commit; this is what
#         # expire_on_commit=False allows
#         print(a1.data)

#     # for AsyncEngine created in function scope, close and
#     # clean-up pooled connections
#     await engine.dispose()


# asyncio.run(async_main())




# routes
routes = web.RouteTableDef()


@routes.get('/create_tables')
async def create_tables(request: web.BaseRequest):
    engine = create_async_engine(
        "sqlite+aiosqlite:///AIOHTTP_REST_FULL_API.db",
        echo=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # expire_on_commit=False will prevent attributes from being expired
    # after commit.
    global async_session
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        async with session.begin():
            session.add_all(
                [
                    User(
                                orders=[Order(), Order()], 
                                data="u1",
                                email=f"test_{randint(1,10000)}@gmail.com", 
                                password=f"pass_{randint(1,10000)}"
                        ),
                    User(
                                orders=[Order()], 
                                data="u2",
                                email=f"test_{randint(1,10000)}@gmail.com", 
                                password=f"pass_{randint(1,10000)}"
                        ),
                    User(
                                orders=[Order(), Order()], 
                                data="u3",
                                email=f"test_{randint(1,10000)}@gmail.com", 
                                password=f"pass_{randint(1,10000)}"
                        )
                ]
            )

        stmt = select(User).options(selectinload(User.orders))

        result = await session.execute(stmt)

        for a1 in result.scalars():
            print(a1)
            print(f"created at: {a1.create_date}")
            for b1 in a1.orders:
                print(b1)

        result = await session.execute(select(User).order_by(User.id))

        a1 = result.scalars().first()

        a1.data = "new data"

        await session.commit()

        # access attribute subsequent to commit; this is what
        # expire_on_commit=False allows
        print(a1.data)

    # for AsyncEngine created in function scope, close and
    # clean-up pooled connections
    await engine.dispose()
    return web.json_response({
            'result': 'tables created succsessfully'
    })


@routes.get('/users')
async def get_users(request: web.BaseRequest):
    
    url = request.url
    print(url)

    r = []
    # adding A and B
    users = []
    async with async_session() as session:
        async with session.begin():
            q = select(User)
            result = await session.execute(q)
            users = result.scalars()

            # access attribute subsequent to commit; this is what
            # expire_on_commit=False allows
    for user in users:
        r.append({
                'user_id': user.id,
                'email': user.email,
                'password': user.password,
                'data': user.data,
                'create_date': str(user.create_date),
                'orders': [
                        {
                            'order_id': order.id,
                            'data': order.data
                        }
                        for order in user.orders
                ]
        })

    return web.json_response(r)



@routes.get('/querys')
async def show_users(request: web.BaseRequest):
    res = {}
    for key, value in request.query.items():
        res.update({
                key: value
        })
        # print(key)
        # print(value)
#     if 'id' in request.query:
#         ID = request.query['id']
#     else:
#         ID = 'id not exist!'
    return web.json_response(res)


@routes.get('/add_user')
async def add_user(request: web.BaseRequest):
    res = {}
    email = request.query['email']
    password = request.query['password']
    async with async_session() as session:
        async with session.begin():
            session.add(
                        User(
                        orders=[Order(data=f"order_{randint(1,10000)}")],
                        email=email,
                        password=password,
                        data=f"user_{randint(1,10000)}"
                        )
                )
            session.commit()
    for key, value in request.query.items():
        res.update({
                'status': 'user added.'
        })
        res.update({
                key: value
        })
    return web.json_response(res)



app = web.Application()
app.add_routes(routes)

if __name__ == '__main__':
    web.run_app(app)