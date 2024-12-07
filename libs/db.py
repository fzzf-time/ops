from typing import Generator
from typing import Iterable
from typing import Iterator

import psycopg


def chop(iterable: Iterable, batch=500) -> Generator:
    piece = []
    for ele in iterable:
        piece.append(ele)
        if len(piece) >= batch:
            yield piece
            piece = []
    if piece:
        yield piece


class _Postgres:
    def __init__(self, dsn):
        self._conn = psycopg.connect(dsn, autocommit=True)
        self._cur = self._conn.cursor()
        self.query("select 1")

    def query(self, query, args=None, as_dict=False):
        self._cur.execute(query, args)
        rows = list(self._cur.fetchall())
        if as_dict:
            cols = self._cur.description
            col_names = [col.name for col in cols]
            rows = [dict(zip(col_names, row)) for row in rows]
        return rows

    # def mogrify(self, query: str, args) -> str:
    #     """格式化最终执行SQL"""
    #     # TODO internalize
    #     if args is None:
    #         return query
    #     conn = self._conn
    #     if isinstance(args, (tuple, list)):  # TODO drop list ???
    #         args = tuple(conn.literal(arg) for arg in args)
    #     elif isinstance(args, dict):
    #         args = {key.encode(): conn.literal(val) for (key, val) in args.items()}
    #     else:
    #         args = conn.literal(args)
    #     # TODO mysqldb面向bytes / pymysql面向str
    #     query = query.encode()
    #     # TODO query中某个字段有 % 时有问题
    #     return (query % args).decode()
    
    def _execute_batch(self, query: str, rows: Iterable, last_id: str="") -> int:
        aff = 0
        ids = []
        for batch in chop(rows):
            self._cur.executemany(query, batch, returning=last_id)
            if last_id:
                while True:
                    ids.append(self._cur.fetchone()[0])
                    if not self._cur.nextset():
                        break
                continue
            aff += self._cur.rowcount
        return (ids if last_id else aff)

    def execute(self, query: str, args: Iterable=None, last_id: str=""):
        if last_id and query.lower().find("returning") == -1:
            query += f" returning {last_id}"

        if isinstance(args, (list, Iterator, Generator)):
            self._execute_batch(query, args)
            return self._cur.rowcount
        # real_query = self.mogrify(query, args)


        self._cur.execute(query, args, last_id)

        return self._cur.fetchall()[0] if last_id else self._cur.rowcount


def pg(dsn):
    return _Postgres(dsn)