create or replace function api.get_last_user_version_id(
	p_user_id bigint
)
returns bigint
language plpgsql
security definer 
set search_path = api, dwh, pg_temp
as $$
declare
	v_found_id bigint;
begin
	select id into v_found_id
	from dwh.d_user du
	where du.user_id = p_user_id
		and is_current = true;

	return v_found_id;
end;
$$;

create or replace function api.get_last_subscription(
	p_user_id bigint
)
returns table (
    transaction_id bigint,
    start_date date,
    end_date date,
    created_at_time time,
    status varchar(15)
)
language plpgsql
security definer 
set search_path = api, dwh, pg_temp
as $$
begin
	return query
	select 
		transaction_id,
		sd.date,
		ed.date,
		created_at_time,
		status
    from dwh.f_subscription fs
	join dwh.d_calendar sd on fs.start_date_id = sd.id
	join dwh.d_calendar ed on fs.end_date_id = ed.id
    where fs.user_id = p_user_id
	order by sd.date desc, created_at_time desc
    limit 1;
end;
$$;

create or replace function api.get_product_id_by_str_id(
	p_found_product_str_id varchar(100)
)
returns smallint
language plpgsql
security definer 
set search_path = api, dwh, pg_temp
as $$
declare
	v_found_id smallint;
begin
	select id into v_found_id
	from dwh.d_product dp
	where str_id = p_found_product_str_id;

	return v_found_id;
end;
$$;

create or replace function api.get_date_id(
	p_target_date date
)
returns integer
language plpgsql
security definer 
set search_path = api, dwh, pg_temp
as $$
declare
	v_found_id integer;
begin
	select id into v_found_id
	from dwh.d_calendar
	where date = p_target_date;
	
	return coalesce(v_found_id, -1);
end;
$$;

create or replace function api.get_or_create_city(
	p_target_city varchar(50),
	p_timezone varchar(50)
)
returns integer
language plpgsql
security definer 
set search_path = api, dwh, pg_temp
as $$
declare
	v_found_id integer;
begin
	select id into v_found_id
	from dwh.d_city
	where name = p_target_city;
	
	if v_found_id is null then
		insert into dwh.d_city (name, timezone)
		values (p_target_city, p_timezone)
		returning id into v_found_id;
	end if;

	return v_found_id;
end;
$$;

create or replace procedure api.add_new_user(
	p_user_id bigint,
	p_name varchar(50),
	p_sex varchar(7),
	p_birthday date,
	p_birth_time time,
	p_birth_city varchar(50),
	p_birthday_city_timezone varchar(50),
	p_residence_city varchar(50),
	p_residence_city_timezone varchar(50),
	p_registration_date date
)
language plpgsql
security definer 
set search_path = api, dwh, pg_temp
as $$
declare
	v_birthday_id integer;
	v_registration_date_id integer;
	v_birth_city_id integer;
	v_residence_city_id integer;
begin
	if api.get_last_user_version_id(p_user_id) is not null
	then
		return;
	end if;

	v_birthday_id := api.get_date_id(p_birthday);
	v_registration_date_id := api.get_date_id(p_registration_date);

	v_birth_city_id := api.get_or_create_city(p_birth_city, p_birthday_city_timezone);
	v_residence_city_id := api.get_or_create_city(p_residence_city, p_residence_city_timezone);

	insert into dwh.d_user (
		user_id,
		name,
		sex,
		birthday_id,
		birth_time,
		birth_city_id,
		residence_city_id,
		registration_date_id
	)
	values (
		p_user_id,
		p_name,
		p_sex,
		v_birthday_id,
		p_birth_time,
		v_birth_city_id,
		v_residence_city_id,
		v_registration_date_id
	);
end;
$$;

create or replace procedure api.update_user_data(
	p_user_id bigint,
	p_name varchar(50),
	p_sex varchar(7),
	p_birthday date,
	p_birth_time time,
	p_birth_city varchar(50),
	p_birthday_city_timezone varchar(50),
	p_residence_city varchar(50),
	p_residence_city_timezone varchar(50)
)
language plpgsql
security definer 
set search_path = api, dwh, pg_temp
as $$
declare
	v_version_id bigint;
	v_registration_date date;
begin
	select du.id, dc.date into v_version_id, v_registration_date
	from dwh.d_user du
	join dwh.d_calendar dc on du.registration_date_id = dc.id
	where du.user_id = p_user_id
		and is_current = true;

	if v_version_id is null then
		return;
	end if;
	
	update dwh.d_user
	set effective_to = now(), 
		is_current = false
	where id = v_version_id;

	call api.add_new_user(
		p_user_id,
		p_name,
		p_sex,
		p_birthday,
		p_birth_time,
		p_birth_city,
		p_birthday_city_timezone,
		p_residence_city,
		p_residence_city_timezone,
		v_registration_date
	);
end;
$$;

create or replace procedure api.add_transaction(
	p_user_id bigint,
	p_product_str_id varchar(100),
	p_date_transaction date,
	p_time_transaction time,
	p_stars_price_original integer,
	p_stars_price_actual integer,
	p_token text,
	p_is_subscription_active bool,
	out out_transaction_id bigint
)
language plpgsql
security definer 
set search_path = api, dwh, pg_temp
as $$
declare
	v_last_user_version_id bigint;
	v_product_id smallint;	
	v_date_id integer;
begin
	v_last_user_version_id := api.get_last_user_version_id(p_user_id);
	v_product_id := api.get_product_id_by_str_id(p_product_str_id);	
	v_date_id := api.get_date_id(p_date_transaction);

	if v_last_user_version_id is null 
		or v_product_id is null
		or v_date_id is null 
	then
		out_transaction_id := null;
		return;
	end if;
	
	insert into dwh.f_transaction (
		user_id,
		product_id,
		date_id,
		time,
		stars_price_original,
		stars_price_actual,
		token,
		is_subscription_active
	)
	values (
		v_last_user_version_id,
		v_product_id,
		v_date_id,
		p_time_transaction,
		p_stars_price_original,
		p_stars_price_actual,
		p_token,
		p_is_subscription_active
	)
	returning id into out_transaction_id;
end;
$$;

create or replace procedure api.add_subscription(
	p_user_id bigint,
	p_transaction_id bigint,
	p_start_date date,
	p_end_date date,
	p_created_at_time time,
	p_status varchar(15)
)
language plpgsql
security definer 
set search_path = api, dwh, pg_temp
as $$
declare
	v_user_last_version_id bigint;
	v_start_date_id integer;
	v_end_date_id integer;
begin
	v_user_last_version_id := api.get_last_user_version_id(p_user_id);
	v_start_date_id := api.get_date_id(p_start_date);
	v_end_date_id := api.get_date_id(p_end_date);

	if v_user_last_version_id is null 
		or v_start_date_id is null
		or v_end_date_id is null 
	then
		return;
	end if;
	
	insert into dwh.f_subscription (
		user_id,
		transaction_id,
		start_date_id,
		end_date_id,
		created_at_time,
		status
	)
	values (
		v_user_last_version_id,
		p_transaction_id,
		v_start_date_id,
		v_end_date_id,
		p_created_at_time,
		p_status
	);
end;
$$;

create or replace procedure api.add_prediction(
	p_user_id bigint,
	p_date_prediction date,
	p_type_id smallint,
	p_prediction jsonb
)
language plpgsql
security definer 
set search_path = api, dwh, pg_temp
as $$
declare
	v_user_last_version_id bigint;
	v_date_id integer;
begin
	v_user_last_version_id := api.get_last_user_version_id(p_user_id);
	v_date_id := api.get_date_id(p_date_prediction);

	if v_user_last_version_id is null 
		or v_date_id is null
	then
		return;
	end if;
	
	insert into dwh.f_prediction (
		user_id,
		date_id,
		type_id,
		prediction
	)
	values (
		v_user_last_version_id,
		v_date_id,
		p_type_id,
		p_prediction
	);
end;
$$;

create or replace procedure api.add_action_log(
	p_user_id bigint, 
	p_message_text text, 
	p_response text, 
	p_date_log date, 
	p_time_log time
)
language plpgsql
security definer 
set search_path = api, dwh, pg_temp
as $$
declare
	v_date_id integer;
begin
	v_date_id := api.get_date_id(p_date_log);

	if v_date_id is null
	then
		return;
	end if;

	insert into dwh.f_user_action_log (
		user_id,
		message_text,
		response,
		date_id,
		time
	)
	values (
		p_user_id,
		p_message_text,
		p_response,
		v_date_id,
		p_time_log
	);
end;
$$;