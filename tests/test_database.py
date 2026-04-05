import pytest
import asyncpg
import json
import asyncio
from datetime import date, time, timedelta
from asyncpg.exceptions import CheckViolationError

from bot.database.repositories.user_repository import UserRepository
from bot.database.repositories.transaction_repository import TransactionRepository
from bot.database.repositories.subscription_repository import SubscriptionRepository
from bot.database.repositories.prediction_repository import PredictionRepository
from bot.database.repositories.action_log_repository import ActionLogRepository
from bot.database.repositories.products_repository import ProductsRepository
from bot.database.DTO.user_dto import UserDTO
from bot.database.DTO.transaction_dto import TransactionDTO
from bot.database.DTO.subscription_dto import SubscriptionDTO
from bot.database.DTO.prediction_dto import PredictionDTO
from bot.database.DTO.get_prediction_dto import GetPredictionDTO
from bot.database.DTO.action_log_dto import ActionLogDTO


@pytest.fixture(scope="session")
async def db_pool():
    async def init(conn):
        await conn.set_type_codec(
            'jsonb',
            encoder=json.dumps,
            decoder=json.loads,
            schema='pg_catalog'
        )

    pool = await asyncpg.create_pool(
        dsn="postgresql://postgres:password@localhost:5433/lumia_test_db",
        ssl=False,
        init=init 
    )
    
    yield pool
    await pool.close()


# фикстурки
@pytest.fixture
async def user_repo(db_pool):
    return UserRepository(db_pool)


@pytest.fixture
async def trans_repo(db_pool):
    return TransactionRepository(db_pool)


@pytest.fixture
async def sub_repo(db_pool):
    return SubscriptionRepository(db_pool)


@pytest.fixture
async def pred_repo(db_pool):
    return PredictionRepository(db_pool)


@pytest.fixture
async def log_repo(db_pool):
    return ActionLogRepository(db_pool)

@pytest.fixture
async def products_repo(db_pool):
    return ProductsRepository(db_pool)


# тестики
@pytest.mark.asyncio
async def test_register_user_logic(user_repo, db_pool):
    user_data = UserDTO(
        user_id=12345678,
        name="Саня",
        sex="Парень",
        birthday=date(1995, 5, 20),
        birth_time=time(14, 30, 0),
        birth_city="Moscow",
        birthday_city_timezone="Europe/Moscow",
        residence_city="Dubai",
        residence_city_timezone="Asia/Dubai",
        registration_date=date.today()
    )

    await user_repo.add_new_user(user_data)
    row = await db_pool.fetchrow("select * from dwh.d_user where user_id = $1", 12345678)
    
    assert row is not None
    assert row['name'] == "Саня"


@pytest.mark.asyncio
async def test_user_update_versioning(user_repo, db_pool):
    user_id = 999
    initial_data = UserDTO(
        user_id=user_id, name="Первый", sex="Парень",
        birthday=date(1990, 1, 1), birth_time=time(10, 0),
        birth_city="Minsk", birthday_city_timezone="Europe/Minsk",
        residence_city="Minsk", residence_city_timezone="Europe/Minsk",
        registration_date=date.today()
    )

    await user_repo.add_new_user(initial_data)

    updated_data = UserDTO(
        user_id=user_id, name="Первый", sex="Парень",
        birthday=date(1990, 1, 1), birth_time=time(10, 0),
        birth_city="Minsk", birthday_city_timezone="Europe/Minsk",
        residence_city="Warsaw", residence_city_timezone="Europe/Warsaw",
        registration_date=date.today()
    )
    await user_repo.update_user(updated_data)
    
    versions = await db_pool.fetch("select * from dwh.d_user where user_id = $1 order by id", user_id)
    assert len(versions) == 2
    assert versions[0]['is_current'] is False
    assert versions[1]['is_current'] is True
    assert versions[1]['residence_city_id'] != versions[0]['residence_city_id']


@pytest.mark.asyncio
async def test_transaction_and_subscription(user_repo, trans_repo, sub_repo, db_pool):
    user_id = 777
    await user_repo.add_new_user(UserDTO(
        user_id=user_id, name="Buyer", sex="Девушка",
        birthday=date(2000, 1, 1), birth_time=time(12, 0),
        birth_city="Brest", birthday_city_timezone="Europe/Minsk",
        residence_city="Brest", residence_city_timezone="Europe/Minsk",
        registration_date=date.today()
    ))

    trans_dto = TransactionDTO(
        user_id=user_id, product_str_id="monthly_subscription",
        date_transaction=date.today(), time_transaction=time(15, 0),
        stars_price_original=150, stars_price_actual=150,
        token="test_token", is_subscription_active=True
    )
    t_id = await trans_repo.add_new_transaction(trans_dto)
    assert t_id is not None

    sub_dto = SubscriptionDTO(
        user_id=user_id, transaction_id=t_id,
        start_date=date.today(), end_date=date.today() + timedelta(days=30),
        created_at_time=time(15, 0), status="paid"
    )
    await sub_repo.add_new_subscription(sub_dto)

    is_active = await sub_repo.exists_active_subscription(user_id)
    assert is_active is True


@pytest.mark.asyncio
async def test_prediction_storage(user_repo, pred_repo):
    user_id = 555
    pred_date = date.today()
    pred_type = "short_horoscope_for_the_day"
    payload = {"main": "Удачный день", "luck_score": 95, "colors": ["red", "gold"]}

    await user_repo.add_new_user(UserDTO(
        user_id=user_id, name="Esoteric", sex="Парень",
        birthday=date(1988, 8, 8), birth_time=time(8, 0),
        birth_city="Gomel", birthday_city_timezone="Europe/Minsk",
        residence_city="Gomel", residence_city_timezone="Europe/Minsk",
        registration_date=date.today()
    ))

    await pred_repo.add_prediction(PredictionDTO(
        user_id=user_id, prediction_date=pred_date,
        type=pred_type, prediction=payload
    ))

    result = await pred_repo.get_prediction(GetPredictionDTO(
        user_id=user_id, prediction_date=pred_date, type=pred_type
    ))
    
    assert result is not None
    assert result['prediction']['luck_score'] == 95


@pytest.mark.asyncio
async def test_action_logging(user_repo, log_repo, db_pool):
    user_id = 111
    await user_repo.add_new_user(UserDTO(
        user_id=user_id, name="Logger", sex="Девушка",
        birthday=date(1999, 9, 9), birth_time=time(9, 0),
        birth_city="Minsk", birthday_city_timezone="Europe/Minsk",
        residence_city="Minsk", residence_city_timezone="Europe/Minsk",
        registration_date=date.today()
    ))

    log_entry = ActionLogDTO(
        user_id=user_id, message_text="/start",
        response="Welcome!", date_log=date.today(), time_log=time(10, 0)
    )
    await log_repo.add_action_log(log_entry)

    log_row = await db_pool.fetchrow("select * from dwh.f_user_action_log where message_text = '/start'")
    assert log_row is not None
    assert log_row['response'] == "Welcome!"


@pytest.mark.asyncio
async def test_get_product_success(products_repo):
    target_str_id = 'monthly_subscription'
    
    product_val = await products_repo.get_product(target_str_id)
    
    assert product_val is not None
    assert product_val == target_str_id


@pytest.mark.asyncio
async def test_get_product_not_found(products_repo):
    non_existent_id = "some_fake_product_123"
    result = await products_repo.get_product(non_existent_id) #
    
    assert result is None


@pytest.mark.asyncio
async def test_city_deduplication_and_timezone(user_repo, db_pool):
    city_name = "Минск"
    tz_format = "+3UTC"

    user1 = UserDTO(
        user_id=101, name="User One", sex="Парень",
        birthday=date(1990, 1, 1), birth_time=time(10, 0),
        birth_city=city_name, birthday_city_timezone=tz_format,
        residence_city=city_name, residence_city_timezone=tz_format,
        registration_date=date.today()
    )
    
    user2 = UserDTO(
        user_id=102, name="User Two", sex="Девушка",
        birthday=date(1995, 5, 5), birth_time=time(12, 0),
        birth_city=city_name, birthday_city_timezone=tz_format,
        residence_city=city_name, residence_city_timezone=tz_format,
        registration_date=date.today()
    )

    await user_repo.add_new_user(user1)
    await user_repo.add_new_user(user2)

    city_rows = await db_pool.fetch("select * from dwh.d_city where name = $1", city_name)
    
    assert len(city_rows) == 1
    assert city_rows[0]['timezone'] == tz_format
    
    users = await db_pool.fetch(
        "select birth_city_id from dwh.d_user where user_id in (101, 102)"
    )
    assert users[0]['birth_city_id'] == users[1]['birth_city_id']
    assert users[0]['birth_city_id'] == city_rows[0]['id']


@pytest.mark.asyncio
async def test_subscription_boundaries(user_repo, trans_repo, sub_repo, db_pool):
    user_id = 888
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    await user_repo.add_new_user(UserDTO(
        user_id=user_id, name="BoundaryUser", sex="Парень",
        birthday=date(1990, 1, 1), birth_time=time(10, 0),
        birth_city="Minsk", birthday_city_timezone="+3UTC",
        residence_city="Minsk", residence_city_timezone="+3UTC",
        registration_date=today
    ))
    
    t_id = await trans_repo.add_new_transaction(TransactionDTO(
        user_id=user_id, product_str_id="monthly_subscription",
        date_transaction=today, time_transaction=time(12, 0),
        stars_price_original=150, stars_price_actual=150,
        token="token_boundary", is_subscription_active=True
    ))

    await sub_repo.add_new_subscription(SubscriptionDTO(
        user_id=user_id, transaction_id=t_id,
        start_date=yesterday - timedelta(days=30), end_date=yesterday,
        created_at_time=time(12, 0), status="paid"
    ))
    assert await sub_repo.exists_active_subscription(user_id) is False

    await sub_repo.add_new_subscription(SubscriptionDTO(
        user_id=user_id, transaction_id=t_id,
        start_date=yesterday, end_date=today,
        created_at_time=time(13, 0), status="paid"
    ))
    assert await sub_repo.exists_active_subscription(user_id) is True

    future_user_id = 889
    await user_repo.add_new_user(UserDTO(
        user_id=future_user_id, name="FutureUser", sex="Девушка",
        birthday=date(1995, 1, 1), birth_time=time(10, 0),
        birth_city="Moscow", birthday_city_timezone="+3UTC",
        residence_city="Moscow", residence_city_timezone="+3UTC",
        registration_date=today
    ))
    await sub_repo.add_new_subscription(SubscriptionDTO(
        user_id=future_user_id, transaction_id=t_id,
        start_date=tomorrow, end_date=tomorrow + timedelta(days=30),
        created_at_time=time(14, 0), status="paid"
    ))
    assert await sub_repo.exists_active_subscription(future_user_id) is False


@pytest.mark.asyncio
async def test_add_transaction_non_existent_user(trans_repo, db_pool):
    fake_user_id = 123999999
    
    trans_dto = TransactionDTO(
        user_id=fake_user_id, 
        product_str_id="monthly_subscription",
        date_transaction=date.today(), 
        time_transaction=time(12, 0),
        stars_price_original=150, 
        stars_price_actual=150,
        token="fake_token", 
        is_subscription_active=True
    )

    t_id = await trans_repo.add_new_transaction(trans_dto)
    
    assert t_id is None

    count = await db_pool.fetchval("select count(*) from dwh.f_transaction where token = 'fake_token'")
    assert count == 0


@pytest.mark.asyncio
async def test_add_prediction_invalid_product_type(user_repo, pred_repo, db_pool):
    user_id = 444
    await user_repo.add_new_user(UserDTO(
        user_id=user_id, name="ErrorTester", sex="Парень",
        birthday=date(1990, 1, 1), birth_time=time(10, 0),
        birth_city="Minsk", birthday_city_timezone="+3UTC",
        residence_city="Minsk", residence_city_timezone="+3UTC",
        registration_date=date.today()
    ))

    pred_dto = PredictionDTO(
        user_id=user_id, 
        prediction_date=date.today(),
        type="mega_ultra_horoscope", 
        prediction={"text": "Fail"}
    )

    await pred_repo.add_prediction(pred_dto)

    exists = await db_pool.fetchval(
        "select exists(select 1 from dwh.f_prediction where user_id = (select id from dwh.d_user where user_id = $1))",
        user_id
    )
    assert exists is False


@pytest.mark.asyncio
async def test_transaction_negative_price_constraint(user_repo, trans_repo):
    user_id = 333
    await user_repo.add_new_user(UserDTO(
        user_id=user_id, name="PriceTester", sex="Парень",
        birthday=date(1990, 1, 1), birth_time=time(10, 0),
        birth_city="Minsk", birthday_city_timezone="+3UTC",
        residence_city="Minsk", residence_city_timezone="+3UTC",
        registration_date=date.today()
    ))

    invalid_trans = TransactionDTO(
        user_id=user_id, product_str_id="monthly_subscription",
        date_transaction=date.today(), time_transaction=time(12, 0),
        stars_price_original=150, stars_price_actual=-500,
        token="negative_token", is_subscription_active=True
    )

    with pytest.raises(CheckViolationError):
        await trans_repo.add_new_transaction(invalid_trans)


@pytest.mark.asyncio
async def test_user_invalid_sex_constraint(user_repo):
    invalid_user = UserDTO(
        user_id=444, name="OptimusPrime", sex="Робот",
        birthday=date(2020, 1, 1), birth_time=time(0, 0),
        birth_city="Cybertron", birthday_city_timezone="+0UTC",
        residence_city="Cybertron", residence_city_timezone="+0UTC",
        registration_date=date.today()
    )

    with pytest.raises(CheckViolationError):
        await user_repo.add_new_user(invalid_user)


@pytest.mark.asyncio
async def test_subscription_invalid_status_constraint(user_repo, trans_repo, sub_repo):
    user_id = 555
    await user_repo.add_new_user(UserDTO(
        user_id=user_id, name="StatusTester", sex="Девушка",
        birthday=date(1995, 1, 1), birth_time=time(12, 0),
        birth_city="Moscow", birthday_city_timezone="+3UTC",
        residence_city="Moscow", residence_city_timezone="+3UTC",
        registration_date=date.today()
    ))
    
    t_id = await trans_repo.add_new_transaction(TransactionDTO(
        user_id=user_id, product_str_id="monthly_subscription",
        date_transaction=date.today(), time_transaction=time(12, 0),
        stars_price_original=150, stars_price_actual=150,
        token="status_token", is_subscription_active=True
    ))

    invalid_sub = SubscriptionDTO(
        user_id=user_id, transaction_id=t_id,
        start_date=date.today(), end_date=date.today() + timedelta(days=30),
        created_at_time=time(12, 0), status="stolen"
    )

    with pytest.raises(CheckViolationError):
        await sub_repo.add_new_subscription(invalid_sub)


@pytest.mark.asyncio
async def test_scd2_user_versioning_integrity(user_repo, db_pool):
    user_id = 112233
    reg_date = date(2026, 1, 1)
    
    initial_user = UserDTO(
        user_id=user_id, name="Original", sex="Парень",
        birthday=date(1990, 1, 1), birth_time=time(10, 0),
        birth_city="Minsk", birthday_city_timezone="+3UTC",
        residence_city="Minsk", residence_city_timezone="+3UTC",
        registration_date=reg_date
    )
    await user_repo.add_new_user(initial_user)

    await asyncio.sleep(0.1) 

    updated_user = UserDTO(
        user_id=user_id, name="Updated", sex="Парень",
        birthday=date(1990, 1, 1), birth_time=time(10, 0),
        birth_city="Minsk", birthday_city_timezone="+3UTC",
        residence_city="Warsaw", residence_city_timezone="+1UTC",
        registration_date=date.today()
    )
    await user_repo.update_user(updated_user)

    rows = await db_pool.fetch(
        "select id, is_current, effective_from, effective_to, registration_date_id, name "
        "from dwh.d_user where user_id = $1 order by effective_from asc", 
        user_id
    )
    
    assert len(rows) == 2, "Должно быть ровно две записи в истории"
    
    old_ver = rows[0]
    new_ver = rows[1]

    assert old_ver['is_current'] is False, "Старая версия должна быть неактивна"
    assert old_ver['effective_to'] is not None, "У старой версии должна быть дата окончания"
    assert old_ver['name'] == "Original"

    assert new_ver['is_current'] is True, "Новая версия должна быть активна"
    assert new_ver['effective_to'] is None, "У новой версии не должно быть даты окончания"
    assert new_ver['name'] == "Updated"

    assert new_ver['effective_from'] >= old_ver['effective_to'], "Новая версия должна начинаться не раньше закрытия старой"
    
    reg_date_id = await db_pool.fetchval("select id from dwh.d_calendar where date = $1", reg_date)
    assert old_ver['registration_date_id'] == reg_date_id
    assert new_ver['registration_date_id'] == reg_date_id, "Дата регистрации не должна меняться при обновлении профиля"