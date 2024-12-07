from functools import wraps
import logging

from clickhouse_driver import Client


class _CH:
    # TODO reconnect
    def __init__(self, dsn):
        self._client = Client.from_url(dsn)
        # logging.info(f"connect {dsn=}")
        self.query("select 1")

    def query(self, query, as_dict=False):
        if as_dict:
            rows, columns = self._client.execute(query, with_column_types=True)
            column_names = [name for name, _ in columns]
            rows = [dict(zip(column_names, row)) for row in rows]
        else:
            rows = self._client.execute(query)
        # logging.debug("query => %s\nrows_num => %s", query, len(rows))
        return rows

    def execute(self, query: str, rows=None):
        return self._client.execute(query, rows)


_gr = {}

def singleton(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        attr = "__k2ch__"
        if args:
            attr, *r = args
            if r:
                raise TypeError(args)
        r = getattr(func, attr, None)
        if r is None:
            r = func(*args, **kwargs)
            name = func.__name__
            logging.info(f"{name} {attr} {kwargs}")
            setattr(func, attr, r)  # ignore-ensure
            _gr[name] = func
        return r
    return wrapped


@singleton
def ch(dsn):
    return _CH(dsn)