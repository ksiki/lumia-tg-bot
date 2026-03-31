-- add 'Unknown' date
insert into dwh.d_calendar (id, date, day_num, day_of_week, day_name, week_of_year, month_num, month_name, quarter, year, is_weekend)
values (-1, '1900.01.01'::date, 1, 1, 'Monday', 1, 1, 'January', 1, 1990, false)
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

insert into dwh.d_product (product_name, category, price_stars, is_discountable)
values 
	('monthly_subscription', 'subscription', 150, false),
	('short_horoscope_for_the_day', 'free_service', 0, false),
	('one_card_of_the_day', 'free_service', 0, false),
	('full_horoscope_for_the_day', 'subscription_service', 0, false),
	('three_tarot_cards_for_the_day', 'subscription_service', 0, false),
	('detailed_horoscope_for_the_week', 'subscription_service', 0, false),
	('one_time_deep_seven_card_hand', 'microtransaction', 150, true),
	('fate_matrix', 'microtransaction', 150, true),
	('human_design', 'microtransaction', 150, true),
	('deep_compatibility_analysis_synastry', 'microtransaction', 150, true),
	('test_of_loyalty', 'microtransaction', 150, true)
on conflict (product_name) do nothing;