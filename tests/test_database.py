import pytest
import asyncio
from datetime import date, datetime, time, timedelta
from bot.database.core.database import Database
from bot.database.data_services import DataServices
from bot.database.DTO import UserDTO, TransactionDTO, SubscriptionDTO, GetPredictionDTO, PredictionDTO, ActionLogDTO

DB_URL = "postgresql://postgres:password@localhost:5433/lumia_test_db"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_services():
    db = Database(DB_URL)
    await db.connect()
    services = DataServices(db.pool)
    yield services
    await db.disconnect()


@pytest.mark.asyncio
class TestDatabaseIntegration:
    async def test_user_lifecycle_and_scd2(self, db_services: DataServices):
        user_id = 123456789

        user = UserDTO(
            user_id=user_id, name="Alice", sex="Девушка",
            birthday=date(2000, 1, 1), birth_time=time(12, 0),
            birth_city="Москва", birthday_city_timezone="Europe/Moscow",
            residence_city="Москва", residence_city_timezone="Europe/Moscow",
            registration_date=date.today()
        )
        await db_services.register_user(user)
        
        assert await db_services.is_user_registered(user_id) is True

        updated_user = UserDTO(
            user_id=user_id, name="Alice", sex="Девушка",
            birthday=date(2000, 1, 1), birth_time=time(12, 0),
            birth_city="Москва", birthday_city_timezone="Europe/Moscow",
            residence_city="Токио", residence_city_timezone="Asia/Tokyo",
            registration_date=None
        )
        await db_services.update_user_date(updated_user)

        actual_data = await db_services.get_user_actual_data(user_id)
        assert actual_data["residence_city"] == "Токио"

    async def test_subscription_purchase_and_extension(self, db_services: DataServices):
        user_id = 999

        await db_services.register_user(UserDTO(
            user_id=user_id, name="Bob", sex="Парень",
            birthday=date(1990, 5, 5), birth_time=time(10, 0),
            birth_city="Минск", birthday_city_timezone="Europe/Minsk",
            residence_city="Минск", residence_city_timezone="Europe/Minsk",
            registration_date=date.today()
        ))

        trans_dto = TransactionDTO(
            user_id=user_id, product_str_id="monthly_subscription",
            date_transaction=date.today(), time_transaction=time(14, 0),
            stars_price_actual=100, token="token_1", is_subscription_active=True
        )
        
        t_id, _ = await db_services.handle_purchase(trans_dto)
        assert t_id is not None
        
        sub = await db_services.get_active_subscription(user_id)
        assert sub is not None
        first_end_date = sub["end_date"]

        trans_dto_2 = TransactionDTO(
            user_id=user_id, product_str_id="monthly_subscription",
            date_transaction=date.today(), time_transaction=time(15, 0),
            stars_price_actual=100, token="token_2", is_subscription_active=True
        )
        await db_services.handle_purchase(trans_dto_2)
        
        last_sub = await db_services.get_last_subscription(user_id)
        assert last_sub["start_date"] == first_end_date + timedelta(days=1)

    async def test_prediction_uniqueness(self, db_services: DataServices):
        user_id = 111
        await db_services.register_user(UserDTO(
            user_id=user_id, name="Zoe", sex="Девушка",
            birthday=date(1995, 8, 8), birth_time=time(8, 0),
            birth_city="Астана", birthday_city_timezone="Asia/Almaty",
            residence_city="Астана", residence_city_timezone="Asia/Almaty",
            registration_date=date.today()
        ))

        pred_date = date.today()
        prod_id = "lunar_horoscope_for_the_week"

        check_dto = GetPredictionDTO(user_id=user_id, prediction_date=pred_date, type=prod_id)
        assert await db_services.is_having_prediction(check_dto) is False

        pred_dto = PredictionDTO(
            user_id=user_id, prediction_date=pred_date, transaction_id=None,
            type=prod_id, category="lunar", prediction={"text": "Magic week"},
            success=True, cards="Moon", with_pdf=False
        )
        await db_services.add_new_prediction(pred_dto)

        assert await db_services.is_having_prediction(check_dto) is True

    async def test_promotion_retrieval(self, db_services: DataServices):
        promo_text = await db_services.get_text_promotion()
        assert promo_text is not None
        assert "Здесь могла быть ваша реклама" in promo_text

    async def test_city_uniqueness(self, db_services: DataServices):
        city_name = "Санкт-Петербург"
        tz = "Europe/Moscow"

        user1_id = 11111
        user2_id = 22222
        
        user_dto = lambda uid: UserDTO(
            user_id=uid, name="Test", sex="Парень", birthday=date(1990,1,1),
            birth_time=time(10,0), birth_city=city_name, birthday_city_timezone=tz,
            residence_city=city_name, residence_city_timezone=tz, registration_date=date.today()
        )
        
        await db_services.register_user(user_dto(user1_id))
        await db_services.register_user(user_dto(user2_id))
        

    async def test_transaction_refund_logic(self, db_services: DataServices):
        user_id = 777
        await db_services.register_user(UserDTO(
            user_id=user_id, name="Refunder", sex="Парень",
            birthday=date(1988, 8, 8), birth_time=time(8,0),
            birth_city="Омск", birthday_city_timezone="Europe/Omsk",
            residence_city="Омск", residence_city_timezone="Europe/Omsk",
            registration_date=date.today()
        ))

        token = "refund_test_token"
        trans_dto = TransactionDTO(
            user_id=user_id, product_str_id="monthly_subscription",
            date_transaction=date.today(), time_transaction=time(12,0),
            stars_price_actual=100, token=token, is_subscription_active=True
        )
        
        t_id, _ = await db_services.handle_purchase(trans_dto)

        trans_data = await db_services.get_transaction(t_id)
        assert trans_data["status"] == "paid"

        await db_services.mark_transaction_as_refund_by_token(token)
        
        trans_data_after = await db_services.get_transaction(t_id)
        assert trans_data_after["status"] == "refund"

    async def test_action_logging(self, db_services: DataServices):
        log_dto = ActionLogDTO(
            user_id=123, 
            message_text="User clicked /start", 
            response="Welcome message", 
            date_log=date.today(), 
            time_log=time(12, 0)
        )
        await db_services.add_new_action_log(log_dto)

    async def test_db_constraints_negative(self, db_services: DataServices):
        invalid_user = UserDTO(
            user_id=666, name="Chaos", sex="Робот",
            birthday=date(2000, 1, 1), birth_time=time(12, 0),
            birth_city="Москва", birthday_city_timezone="Europe/Moscow",
            residence_city="Москва", residence_city_timezone="Europe/Moscow",
            registration_date=date.today()
        )
        
        with pytest.raises(Exception):
            await db_services.register_user(invalid_user)

    async def test_calendar_week_logic(self, db_services: DataServices):
        test_date = date(2026, 4, 13)
        week_data = await db_services.get_week(test_date)
        
        assert week_data is not None

        assert week_data["start_date"] == date(2026, 4, 13)
        assert week_data["end_date"] == date(2026, 4, 19)
        assert week_data["year"] == 2026

    async def test_get_all_products_catalog(self, db_services: DataServices):
        """Проверка полноты загруженного справочника продуктов"""
        products = await db_services.get_all_product()
        assert products is not None
        assert len(products) >= 11

        product_ids = [p["str_id"] for p in products]
        assert "monthly_subscription" in product_ids
        assert "fate_matrix" in product_ids

    async def test_subscription_expiration_filtering(self, db_services: DataServices):
        user_id = 555
        await db_services.register_user(UserDTO(
            user_id=user_id, name="LegacyUser", sex="Парень",
            birthday=date(1990, 1, 1), birth_time=time(0, 0),
            birth_city="Киев", birthday_city_timezone="Europe/Kyiv",
            residence_city="Киев", residence_city_timezone="Europe/Kyiv",
            registration_date=date.today()
        ))

        yesterday = date.today() - timedelta(days=1)
        start_past = yesterday - timedelta(days=30)
        
        past_sub = SubscriptionDTO(
            user_id=user_id, transaction_id=None,
            start_date=start_past, end_date=yesterday,
            created_at_time=time(12, 0), status="paid"
        )
        await db_services.add_new_subscription(past_sub)

        is_active = await db_services.is_user_has_active_subscription(user_id)
        assert is_active is False
        
        active_sub = await db_services.get_active_subscription(user_id)
        assert active_sub is None

    async def test_handle_purchase_missing_prediction_error(self, db_services: DataServices):
        user_id = 444
        await db_services.register_user(UserDTO(
            user_id=user_id, name="ErrorTest", sex="Девушка",
            birthday=date(1992, 2, 2), birth_time=time(12, 0),
            birth_city="Рига", birthday_city_timezone="Europe/Riga",
            residence_city="Рига", residence_city_timezone="Europe/Riga",
            registration_date=date.today()
        ))

        trans_dto = TransactionDTO(
            user_id=user_id, product_str_id="fate_matrix",
            date_transaction=date.today(), time_transaction=time(10, 0),
            stars_price_actual=150, token="err_token", is_subscription_active=False
        )

        with pytest.raises(TypeError):
            await db_services.handle_purchase(trans_dto, prediction_dto=None)