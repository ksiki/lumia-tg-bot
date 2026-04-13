create table if not exists dwh.f_transaction (
    id bigserial not null,
    user_id bigint not null,      
    product_id smallint not null,  
    date_id integer not null,        
    time time not null default now()::time,
    stars_price_original integer not null,
    stars_price_actual integer not null,
    token text,
    is_subscription_active boolean,
    status varchar(6) not null default 'paid',
    constraint f_transaction_pk primary key (id),
    constraint f_transaction_stars_price_original_check check (stars_price_original >= 0),
    constraint f_transaction_stars_price_actual_check check (stars_price_actual >= 0),
    constraint f_transaction_status_check check (status in ('paid', 'refund')),
    foreign key (user_id) references dwh.d_user (id),
    foreign key (product_id) references dwh.d_product (id),
    foreign key (date_id) references dwh.d_calendar (id)
);

create table if not exists dwh.f_subscription (
	id bigserial not null, 
	user_id bigint not null,
	transaction_id bigint,
	start_date_id integer not null,
	end_date_id integer not null,
	created_at_time time not null default now()::time,
	status varchar(15) not null,
    constraint f_subscription_pk primary key (id),
    constraint f_subscription_status_check check (status in ('gift', 'trial', 'paid', 'admin_gift')),
    foreign key (user_id) references dwh.d_user (id),
    foreign key (transaction_id) references dwh.f_transaction (id),
    foreign key (start_date_id) references dwh.d_calendar (id),
    foreign key (end_date_id) references dwh.d_calendar (id)
);

create table if not exists dwh.f_user_action_log (
	id bigserial not null, 
	user_id bigint not null,
	message_text text,
	response text,
	date_id integer not null,
    time time not null default now()::time,
    constraint user_action_log_pk primary key (id),
    foreign key (date_id) references dwh.d_calendar (id)
);

create table if not exists dwh.f_prediction (
	id bigserial not null,
	user_id bigint not null,
	date_id integer not null,
    transaction_id bigint,
	type_id smallint not null,
    category varchar(50) not null,
	prediction jsonb not null,
    success bool not null,
    cards text,
    with_pdf bool not null,
	constraint f_horoscope_pk primary key (id),
	foreign key (user_id) references dwh.d_user (id),
	foreign key (date_id) references dwh.d_calendar (id),
	foreign key (type_id) references dwh.d_product (id)
);