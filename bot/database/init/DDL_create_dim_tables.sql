create table if not exists dwh.d_city (
    id serial not null,
    name varchar(50) not null,
    timezone varchar(50) not null,
    constraint d_city_pk primary key (id), 
    constraint d_city_name_uqn unique (name)
);

create table if not exists dwh.d_calendar (
    id integer not null,
    date date not null,
    day_num smallint not null,
    day_of_week smallint not null,
    day_name varchar(9) not null,
    week_of_year smallint not null,
    month_num smallint not null,
    month_name varchar(9) not null,
    quarter smallint not null,
    year smallint not null,
    is_weekend bool not null,
    constraint d_calendar_pk primary key (id),
    constraint d_calendar_date_key unique (date)
);

create table if not exists dwh.d_user (
	id bigserial not null,
	user_id bigint not null,
	name varchar(50) not null,
	sex varchar(7) not null,
	birthday_id integer not null, 
    birth_time time not null,
    birth_city_id integer not null,
    residence_city_id integer not null,
    registration_date_id integer not null,
	effective_from timestamp not null default now(),
    effective_to timestamp default null, 
    is_current boolean not null default true,
	constraint d_user_pk primary key (id),
	constraint d_user_sex_check check (sex in ('Парень', 'Девушка')),
	foreign key (birthday_id) references dwh.d_calendar (id),
    foreign key (birth_city_id) references dwh.d_city (id),
    foreign key (residence_city_id) references dwh.d_city (id),
    foreign key (registration_date_id) references dwh.d_calendar (id)
);

create table if not exists dwh.d_product (
    id smallserial not null,
    str_id varchar(100) not null, 
    name varchar(100) not null,
    description varchar(200) not null,
    category varchar(50),               
    price_stars smallint not null,  
    is_discountable boolean default false,
    constraint d_product_pk primary key (id),
    constraint d_product_str_id_unq unique (str_id),
    constraint d_product_category_check check (category in ('microtransaction', 'subscription', 'free_service', 'subscription_service')),
    constraint d_product_price_stars_check check (price_stars >= 0)
);
