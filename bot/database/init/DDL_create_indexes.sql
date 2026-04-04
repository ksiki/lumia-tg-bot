create index idx_d_user_current_active on dwh.d_user (user_id) 
where is_current = true;

create index idx_f_transaction_user_id on dwh.f_transaction (user_id);
create index idx_f_subscription_user_id on dwh.f_subscription (user_id);
create index idx_f_prediction_user_id on dwh.f_prediction (user_id);
create index idx_f_user_action_log_user_id on dwh.f_user_action_log (user_id);

create index idx_f_subscription_end_date on dwh.f_subscription (end_date_id);

create index idx_d_product_id on dwh.d_product (id)
create index idx_d_product_str_id on dwh.d_product (str_id)
