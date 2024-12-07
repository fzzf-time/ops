from datetime import datetime, timedelta
import logging

from libs.ch import ch
from libs.aliyun import RDS


rds_instance2name = {
    "pgm-3ns5253oj7b7gi60": "pg-00.pord.alihk",  # deprecated
    "pgm-3ns917119040e4f0": "pg-00.pord.alihk",
}


def _prepare_ch(dsn):
    ch(dsn).execute("truncate table _psql_slow_log_shadow")

def _write_ch(dsn, rows) -> int:
    sql = "insert into _psql_slow_log_shadow (ts, instance, db_name, client_ip, parse_rows, return_rows, query_time, query) values"
    return ch(dsn).execute(sql, rows)

def _commit_ch(dsn, dt):
    ch(dsn).execute(f"alter table psql_slow_log replace partition '{dt}' from _psql_slow_log_shadow")
    ch(dsn).execute(f"alter table _psql_slow_log_shadow drop partition '{dt}'")

def _yesterday():
    dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    return datetime.strftime(dt, "%Y-%m-%d")

def psqllog2ch(key, secret, ch_dsn, region='cn-hongkong', dt=_yesterday()):
    _prepare_ch(ch_dsn)

    client = RDS(key, secret)
    client.get_client(region_id=region)

    for instance in client.get_instances():
        id = instance['DBInstanceId']
        if not id in rds_instance2name:
            continue
        name = rds_instance2name[id]
        engine = instance['Engine']
        engine_version = instance['EngineVersion']
        logging.info(f"{id=} {name=} {engine=} {engine_version=}")

        datas = []
        for log in client.get_slow_logs(id, dt):
            exec_time = log.get("QueryTimeMS")
            if not exec_time:
                logging.info(f"parse error, skip {log}")
                continue
            if exec_time < 1000:
                continue

            ts = datetime.strptime(log["ExecutionStartTime"], "%Y-%m-%dT%H:%M:%SZ")
            datas.append([
                ts,
                name,
                log["DBName"],
                log["HostAddress"],
                log["ParseRowCounts"],
                log["ReturnRowCounts"],
                log["QueryTimeMS"],
                log["SQLText"]
            ])

    # sort by pk
    rows = []
    for row in sorted(datas, key=lambda x: x[0]):
        rows.append(row)
        if len(rows) >= 50000:
            _write_ch(ch_dsn, rows)
            rows = []
    if rows:
        _write_ch(ch_dsn, rows)

    _commit_ch(ch_dsn, dt)