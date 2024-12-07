create database if not exists ops;
use ops;


create table access_log (
    dt Date default toDate(ts),
    ts DateTime,
    request_id String,
    host LowCardinality(String),
    path String,
    method LowCardinality(String),
    version LowCardinality(String),
    user_agent String,
    bytes_sent Int32,
    remote_user String,
    client_ip String,
    x_forward_for String,
    request_time Float32,
    request_length Int32,
    referer String, 
    status Int16,
    upstream_addr String,
    upstream_name String,
    pod_ip String,
    pod_name String,
    upstream_status Int16,
    upstream_response_time Float32,
    upstream_response_length Int32
) engine = MergeTree()
partition by (dt)
order by (ts)
TTL dt + toIntervalDay(180)
comment 'nginx access log';


create table k8s_app_access_log (
    dt Date default toDate(ts),
    ts DateTime,
    request_id String,   
    host LowCardinality(String),
    path String,
    method LowCardinality(String),
    protocol LowCardinality(String),
    bytes_sent Int32,
    bytes_received Int32,
    request_time Float32,
    status Int16,
    upstream_addr String,
    downstream_addr String,
    pod_name String,
    namespace LowCardinality(String)
) engine = MergeTree()
partition by (dt)
order by (ts)
TTL dt + toIntervalDay(180)
comment 'k8s app access log';


create table psql_slow_log (
    dt Date default toDate(ts),
    ts DateTime,
    instance String,
    db_name String,
    client_ip String,
    parse_rows Int32,
    return_rows Int32,
    query_time Int32,
    query String
) engine = MergeTree()
partition by (dt)
order by (ts)
TTL dt + toIntervalDay(360)
comment 'postgresql slow query log';

create table ops.nginx_log (
    dt Date default toDate(ts),
    ts DateTime,
    host LowCardinality(String),
    path String,
    method LowCardinality(String),
    version LowCardinality(String),
    user_agent String,
    bytes_sent Int32,
    client_ip IPv4,
    request_time Float32,
    request_length Int32,
    referer String,
    status Int16,
    upstream_addr String,
    upstream_name String,
    upstream_status Int16,
    upstream_response_time Float32,
    upstream_response_length Int32
) engine = MergeTree()
partition by (dt)
order by (ts)
TTL dt + toIntervalDay(180)
comment 'nginx log';

-- create table _access_log_shadow as access_log;
create table _psql_slow_log_shadow as psql_slow_log;




