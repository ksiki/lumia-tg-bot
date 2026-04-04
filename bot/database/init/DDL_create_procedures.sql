create or replace function api.get_last_user_version_id(
	user_id bigint
)
returns bigint
language plpgsql
as $$
declare
	found_id bigint;
begin
	select id into found_id
	from dwh.d_user du
	where du.user_id = user_id
		and is_current = true;

	return found_id;
end;
$$;

create or replace function api.get_product_id_by_str_id(
	found_product_str_id varchar(100)
)
returns smallint
language plpgsql
as $$
declare
	found_id smallint;
begin
	select id into found_id
	from dwh.d_product dp
	where str_id = found_product_str_id;

	return found_id;
end;
$$;

create or replace function api.get_date_id(
	target_date date
)
returns integer
language plpgsql
as $$
declare
	found_id integer;
begin
	select id into found_id
	from dwh.d_calendar
	where date = target_date;
	
	return coalesce(found_id, -1);
end;
$$;

create or replace function api.get_or_create_city(
	target_city varchar(50),
	timezone varchar(50)
)
returns integer
language plpgsql
as $$
declare
	found_id integer;
begin
	select id into found_id
	from dwh.d_city
	where name = target_city;
	
	if found_id is null then
		insert into dwh.d_city (name, timezone)
		values (target_city, timezone)
		returning id into found_id;
	end if;

	return found_id;
end;
$$;

create or replace procedure api.add_new_user(
	user_id bigint,
	name varchar(50),
	sex varchar(7),
	birthday date,
	birth_time time,
	birth_city varchar(50),
	birthday_city_timezone varchar(50),
	residence_city varchar(50),
	residence_city_timezone varchar(50),
	registration_date date
)
language plpgsql
as $$
declare
	birthday_id integer;
	registration_date_id integer;
	birth_city_id integer;
	residence_city_id integer;
begin
	birthday_id := api.get_date_id(birthday);
	registration_date_id := api.get_date_id(registration_date);

	birth_city_id := api.get_or_create_city(birth_city, birthday_city_timezone);
	residence_city_id := api.get_or_create_city(residence_city, residence_city_timezone);

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
		user_id,
		name,
		sex,
		birthday_id,
		birth_time,
		birth_city_id,
		residence_city_id,
		registration_date_id
	);
end;
$$;

create or replace procedure api.update_user_data(
	user_id bigint,
	name varchar(50),
	sex varchar(7),
	birthday date,
	birth_time time,
	birth_city varchar(50),
	birthday_city_timezone varchar(50),
	residence_city varchar(50),
	residence_city_timezone varchar(50)
)
language plpgsql
as $$
declare
	version_id bigint;
	registration_date date;
begin
	select du.id, dc.date into version_id, registration_date
	from dwh.d_user du
	join dwh.d_calendar dc on du.registration_date_id = dc.id
	where du.user_id = user_id
		and is_current = true;

	if version_id is null then
		return;
	end if;
	
	update dwh.d_user
	set effective_to = now(), 
		is_current = false
	where id = version_id;

	call api.add_new_user(
		user_id,
		name,
		sex,
		birthday,
		birth_time,
		birth_city,
		birthday_city_timezone,
		residence_city,
		residence_city_timezone,
		registration_date
	);
end;
$$;

create or replace procedure api.add_transaction(
	user_id bigint,
	product_str_id varchar(100),
	date_transaction date,
	time_transaction time,
	stars_price_original integer,
	stars_price_actual integer,
	token text,
	is_subscription_active bool,
	out transaction_id bigint
)
language plpgsql
as $$
declare
	last_user_version_id bigint;
	product_id smallint;	
	date_id integer;
begin
	last_user_version_id := api.get_last_user_version_id(user_id);
	product_id := api.get_product_id_by_str_id(product_str_id);	
	date_id := api.get_date_id(date_transaction);

	if last_user_version_id is null 
		or product_id is null
		or date_id is null 
	then
		transaction_id := null;
		return;
	end if;
	
	insert into dwh.f_transaction (
		user_id,
		product_id,
		date_id,
		time_transaction,
		stars_price_original,
		stars_price_actual,
		token,
		is_subscription_active
	)
	values (
		last_user_version_id,
		product_id,
		date_id,
		time_transaction,
		stars_price_original,
		stars_price_actual,
		token,
		is_subscription_active
	)
	returning id into transaction_id;
end;
$$;

create or replace procedure api.add_subscription(
	user_id bigint,
	transaction_id bigint,
	start_date date,
	end_date date,
	created_at_time time,
	status varchar(15)
)
language plpgsql
as $$
declare
	user_last_version_id bigint;
	start_date_id integer;
	end_date_id integer;
begin
	user_last_version_id := api.get_last_user_version_id(user_id);
	start_date_id := api.get_date_id(start_date);
	end_date_id := api.get_date_id(end_date);

	if last_user_version_id is null 
		or start_date_id is null
		or end_date_id is null 
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
		user_last_version_id,
		transaction_id,
		start_date_id,
		end_date_id,
		created_at_time,
		status
	);
end;
$$;

create or replace procedure api.add_prediction(
	user_id bigint,
	date_prediction date,
	type_str varchar(100),
	prediction jsonb
)
language plpgsql
as $$
declare
	user_last_version_id bigint;
	date_id integer;
	type_id smallint;
begin
	user_last_version_id := api.get_last_user_version_id(user_id);
	date_id := api.get_date_id(date_prediction);
	type_id := api.get_product_id_by_str_id(type_str);

	if last_user_version_id is null 
		or date_id is null
		or type_id is null
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
		user_last_version_id,
		date_id,
		type_id,
		prediction
	);
end;
$$;

create or replace procedure api.add_action_log(
	user_id bigint, 
	message_text text, 
	response text, 
	date_log date, 
	time_log time
)
language plpgsql
as $$
declare
	user_last_version_id bigint;
	date_id integer;
begin
	user_last_version_id := api.get_last_user_version_id(user_id);
	date_id := api.get_date_id(date_log);

	if last_user_version_id is null 
		or date_id is null
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
		user_last_version_id,
		message_text,
		response,
		date_id,
		time_log
	);
end;
$$;