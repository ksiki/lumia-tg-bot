-- 'Unknown' date
insert into dwh.d_calendar (id, date, day_num, day_of_week, day_name, week_of_year, month_num, month_name, quarter, year, is_weekend)
values (-1, '1900.01.01'::date, 1, 1, 'Monday', 1, 1, 'January', 1, 1900, false)
on conflict (id) do nothing;

insert into dwh.d_calendar (id, date, day_num, day_of_week, day_name, week_of_year, month_num, month_name, quarter, year, is_weekend)
select
    to_char(date, 'YYYYMMDD')::int as id,
    date::date as date,
    extract(day from date)::smallint as day_num,
    extract(isodow from date)::smallint as day_of_week,
    to_char(date, 'FMDay') as day_name,
    extract(week from date)::smallint as week_of_year,
    extract(month from date)::smallint as month_num,
    to_char(date, 'FMMonth') as month_name,
    extract(quarter from date)::smallint as quarter,
    extract(year from date)::smallint as year,
    (extract(isodow from date) in (6, 7)) as is_weekend
from generate_series(
    '1970.01.01'::date, 
    '2030.01.01'::date, 
    '1 day'::interval
) d(date)
on conflict (id) do nothing;

insert into dwh.d_promotion (id, start_date_id, end_date_id, text, cost, currency, created_at_date_id)
values (-1, -1, -1, '<b>Здесь могла быть ваша реклама</b> 📢', 0, 'STARS', -1)
on conflict (id) do nothing;

insert into dwh.d_product (str_id, name, description, category, price_stars, period, is_discountable, min_generate_seconds, max_generate_seconds)
values 
    ('monthly_subscription', 'Premium', 'Premium подписка на месяц', 'subscription', 100, 'month', false, 0, 1),
    ('short_horoscope_for_the_day', 'Гороскоп на день', 'Краткий прогноз главных событий', 'free_service', 0, 'day', false, 900, 1800),
    ('one_card_of_the_day', 'Карта дня', 'Твой персональный символ и совет', 'free_service', 0, 'day', false, 900, 1800),
    ('full_horoscope_for_the_day', 'Гороскоп на день', 'Детальный разбор всех сфер жизни', 'subscription_service', 0, 'day', false, 900, 1800),
    ('three_tarot_cards_for_the_day', 'Три карты дня', 'Прошлое, настоящее и будущее', 'subscription_service', 0, 'day', false, 900, 1800),
    ('lunar_horoscope_for_the_week', 'Лунный гороскоп на неделю', 'Влияние фаз Луны на твою неделю', 'subscription_service', 0, 'week', false, 900, 1800),
    ('one_time_deep_seven_card_hand', 'Разбор ситуации (7 карт)', 'Полный разбор любой ситуации (7 карт)', 'microtransaction', 150, 'no', true, 2400, 3600),
    ('fate_matrix', 'Матрица судьбы', 'Расшифровка твоего пути по дате рождения', 'microtransaction', 150, 'no', true, 2400, 3600),
    ('human_design', 'Дизайн человека', 'Твоя уникальная генетическая стратегия', 'microtransaction', 150, 'no', true, 2400, 3600),
    ('deep_compatibility_analysis_synastry', 'Совместимость', 'Анализ союза по натальным картам', 'microtransaction', 150, 'no', true, 2400, 3600),
    ('test_of_loyalty', 'Проверка на верность', 'Скрытые мотивы и честность партнера', 'microtransaction', 150, 'no', true, 2400, 3600)
on conflict (str_id) do nothing;