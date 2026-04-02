create or replace view mart.v_user_current as
select 
	du.user_id as user_id,
	du.id as version_id,
	du.name as name,
	du.sex as sex,
	bd.date as birthday,
	du.birth_time as birth_time,
	bc.name as birth_city,
	rc.name as residence_city,
	rc.timezone as timezone,
	rd.date as registration_date
from dwh.d_user du
join dwh.d_calendar bd on du.birthday_id = bd.id
join dwh.d_calendar rd on du.registration_date_id = rd.id
join dwh.d_city bc on du.birth_city_id = bc.id
join dwh.d_city rc on du.residence_city_id = rc.id
where du.is_current;

create or replace view mart.v_active_subscription as
select 
	fs.user_id as user_id,
	sd.date as start_date,
	ed.date as end_date,
	fs.created_at_time as created_at_time
from dwh.f_subscription fs
join dwh.d_calendar sd on fs.start_date_id = sd.id
join dwh.d_calendar ed on fs.end_date_id = ed.id
where current_timestamp <= ed.date + '1 day'::interval;

create or replace view mart.v_product as
select 
	str_id, 
	name,
	category,
	price_stars,
	is_discountable
from dwh.d_product;

create or replace view mart.v_prediction as
select 
	du.user_id as user_id,
	du.id as user_version_id,
	dc.date as date,
	dc.week_of_year as week_of_year,
	dp.str_id as type,
	fp.prediction as prediction
from dwh.f_prediction fp
join dwh.d_user du on du.id = fp.user_id
join dwh.d_calendar dc on dc.id = fp.date_id
join dwh.d_product dp on dp.id = fp.type_id;