from collections import defaultdict
import sys
import re

def normalize_sequence_name(seq_name):
    return seq_name.split('.')[-1]

def table_name_from_ddl(ddl):
    m = re.match(r'create\s+table\s+(?P<schema>\w+)\.(?P<table>\w+)', ddl, re.IGNORECASE)
    if not m:
        return None, None
    return m.group('schema'), m.group('table')

def pk_from_ddl(ddl):
    m = re.match(
        r'alter\s+table\s+(only\s+)?(?P<schema>\w+)\.(?P<table_name>\w+)\s+add\s+constraint\s+(?P<pk_name>\w+)\s+primary\s+key\s*\((?P<column>.*)\)',
        ddl.replace('\n', ' '),
        re.IGNORECASE
    )
    if not m:
        return None, None, None
    return m.group('schema'), m.group('table_name'), m.group('column')

def uk_from_ddl(ddl):
    m = re.match(
        r'alter\s+table\s+(only\s+)?(?P<schema>\w+)\.(?P<table_name>\w+)\s+add\s+constraint\s+(?P<uk_name>\w+)\s+unique\s*\((?P<column>.*)\)',
        ddl.replace('\n', ' '),
        re.IGNORECASE
    )
    if not m:
        return None, None, None
    return m.group('schema'), m.group('table_name'), m.group('column')

def uk_from_ddl2(ddl):
    m = re.match(
        r'create\s+unique\s+index\s+(?P<uk_name>\w+)\s+on\s+(?P<schema>\w+)\.(?P<table_name>\w+)\s+using\s+btree\s*\((?P<column>.*)\)',
        ddl.replace('\n', ' '),
        re.IGNORECASE
    )
    if not m:
        return None, None, None
    return m.group('schema'), m.group('table_name'), m.group('column')

def table_name_from_idx_ddl(ddl):
    m = re.match(
        r'create\s+index\s+.*\s+on\s+(?P<schema>\w+)\.(?P<table_name>\w+)\s+.*',
        ddl.replace('\n', ' '),
        re.IGNORECASE
    )
    if not m:
        return None, None
    return m.group('schema'), m.group('table_name')

def table_name_from_comment_ddl(ddl):
    m = re.match(
        r'comment\s+on\s+column\s+(?P<schema>\w+)\.(?P<table>\w+)\.(?P<column>\w+)\s+is\s+.*',
        ddl.replace('\n', ' '),
        re.IGNORECASE
    )
    if not m:
        return None, None
    return m.group('schema'), m.group('table')

def table_name_from_table_comment_ddl(ddl):
    m = re.match(
        r'comment\s+on\s+table\s+(?P<schema>\w+)\.(?P<table>\w+)\s+is\s+.*',
        ddl.replace('\n', ' '),
        re.IGNORECASE
    )
    if not m:
        return None, None
    return m.group('schema'), m.group('table')

def format_sql(i="stdin", o="stdout"):
    if i == "stdin":
        sql_statements = sys.stdin.read().lower()
    else:
        with open(i, 'r') as file:
            sql_statements = file.read().lower()

    patterns_to_remove = [
        (re.compile(r'^\s*--.*\n', re.MULTILINE), ''),
        (re.compile(r'\bcomment on extension [^\n]+ is [^\n]+;', re.IGNORECASE | re.MULTILINE), ''),
        (re.compile(r'\bcreate extension if not exists [^\n]+ with schema public;', re.IGNORECASE | re.MULTILINE), ''),
        (re.compile(r'\bselect pg_catalog\.set_config\s*\([^)]*\);', re.IGNORECASE), ''),
        (re.compile(r'\bset\s+[^\s;]+?\s*=\s*[^\s;]+?;', re.IGNORECASE | re.MULTILINE), ''),
        # publication
        (re.compile(r'^create publication [^\n]+;', re.IGNORECASE | re.MULTILINE), ''),
        (re.compile(r'^alter publication [^\n]+;', re.IGNORECASE | re.MULTILINE), ''),
        (re.compile(r'^alter table [^\n]+ replica identity [^\n]+;', re.IGNORECASE | re.MULTILINE), ''),
        # DCLs
        (re.compile(r'^alter .* owner to [^\n]+;', re.IGNORECASE | re.MULTILINE), ''),
        (re.compile(r'^alter sequence [^\n]+ owned by [^\n]+;', re.IGNORECASE | re.MULTILINE), ''),
        (re.compile(r'^alter default privileges [^\n]+;', re.IGNORECASE | re.MULTILINE), ''),
        (re.compile(r'^grant .* to [^\n]+;', re.IGNORECASE | re.MULTILINE), ''),
        (re.compile(r'^revoke .* from [^\n]+;', re.IGNORECASE | re.MULTILINE), ''),
        # partitioned tables
        (re.compile(r'^alter table .* attach partition .*;', re.IGNORECASE | re.MULTILINE), ''),
        # type defs
        (re.compile(r'\bcharacter\s+varying\s*\((\d+)\)\s+default\s+\'\'\s*::\s*character\s+varying', re.IGNORECASE), r"varchar(\1) default ''"),
        (re.compile(r'\btimestamp\s*(?:\(\d+\))?\s*without\s+time\s+zone\b', re.IGNORECASE | re.MULTILINE), 'timestamp'),
        (re.compile(r'\bcharacter\s+varying\s*\((\d*)\)', re.IGNORECASE), r'varchar(\1)'),
        (re.compile(r'\binteger\b', re.IGNORECASE), 'int'),
        # default values
        (re.compile(r'\bdefault\s+\'\'::character varying', re.IGNORECASE), "default ''"),
        (re.compile(r'\bdefault\s+current_timestamp', re.IGNORECASE), 'default current_timestamp'),
        # default timestamp
        (re.compile(r'\b\'\s*::\s*timestamp', re.IGNORECASE), '\''),
        (re.compile(r'\bboolean\b', re.IGNORECASE), 'bool'),
        (re.compile(r'\b(character\s+varying|varchar)\s*\((\d+)\)\s+default\s+\'([^\']*)\'::character\s+varying\s+not\s+null', re.IGNORECASE), r"varchar(\2) not null default '\3'"),
        (re.compile(r'\b(character\s+varying|varchar)\s*\((\d+)\)\s+default\s+\'([^\']*)\'::character\s+varying', re.IGNORECASE), r"varchar(\2) default '\3'"),

    ]
    for p, rm in patterns_to_remove:
        sql_statements = p.sub(rm, sql_statements)

    table_ddls = {}
    pk_ddls = {}
    uk_ddls = defaultdict(set)
    idx_ddls = defaultdict(list)
    seq_ddls = {}
    seq_attach_ddls = {}
    comment_ddls = defaultdict(list)
    unique_index_ddls = defaultdict(list)
    for ddl in sql_statements.split(';\n'):
        ddl = ddl.strip(' \n')
        if not ddl:
            continue

        if ddl.startswith('create sequence '):
            seq_name = ddl.split(' ')[2].strip().strip(';')
            seq_ddls[seq_name] = ddl
            continue
        if ddl.startswith('create table '):
            schema, table = table_name_from_ddl(ddl)
            if schema == "partman":
                continue
            if not table:
                print(f"table name parse failed:\n{ddl}")
                continue
            # schema.table
            table_full_name = f"{schema}.{table}"
            table_ddls[table_full_name] = ddl
            continue
        if ddl.startswith('alter table ') and ' add constraint ' in ddl:
            if ' primary key ' in ddl:
                ret = pk_from_ddl(ddl)
                if not ret or len(ret) != 3:
                    print(f"pk parse failed:\n{ddl}")
                    continue
                schema, tbl, pk = ret
                tbl_full_name = f"{schema}.{tbl}"
                pk_ddls[tbl_full_name] = pk
            elif ' unique ' in ddl:
                ret = uk_from_ddl(ddl)
                if not ret or len(ret) != 3:
                    print(f"uk parse failed:\n{ddl}")
                    continue
                schema, tbl, uk = ret
                tbl_full_name = f"{schema}.{tbl}"
                uk_ddls[tbl_full_name].add(uk)
            else:
                print(f"idx ddl not parsed: {ddl}")
            continue
        if ddl.startswith('create index '):
            schema, tbl = table_name_from_idx_ddl(ddl)
            if not tbl:
                print(f"idx table name parse failed:\n{ddl}")
                continue
            tbl_full_name = f"{schema}.{tbl}"
            idx_ddls[tbl_full_name].append(ddl)
            continue
        if ddl.startswith('create unique index '):
            ret = uk_from_ddl2(ddl)
            if not ret or len(ret) != 3:
                print(f"uk parse failed:\n{ddl}")
                continue
            schema, tbl, uk = ret
            tbl_full_name = f"{schema}.{tbl}"
            unique_index_ddls[tbl_full_name].append(ddl)
            continue
        if ddl.startswith('alter table ') and ' alter column ' in ddl and ' set default nextval(' in ddl:
            # 处理默认值为nextval的ddl
            m = re.match(
                r'alter\s+table\s+(only\s+)?(?P<schema>\w+)\.(?P<table>\w+)\s+alter\s+column\s+(?P<column>\w+)\s+set\s+default\s+nextval\(\'' + r'(?P<sequence>[^\']+)' + r"'::regclass\)",
                ddl.replace('\n', ' '),
                re.IGNORECASE
            )
            if not m:
                print(f"sequence default parse failed:\n{ddl}")
                continue
            schema = m.group('schema')
            table = m.group('table')
            column = m.group('column')
            sequence = m.group('sequence').strip()
            tbl_full_name = f"{schema}.{table}"
            seq_attach_ddls[(tbl_full_name, column)] = sequence
            continue
        if ddl.startswith('comment on column '):
            schema, tbl = table_name_from_comment_ddl(ddl)
            if not tbl:
                print(f"comment table name parse failed:\n{ddl}")
                continue
            tbl_full_name = f"{schema}.{tbl}"
            comment_ddls[tbl_full_name].append(ddl)
            continue
        elif ddl.startswith('comment on table '):
            schema, tbl = table_name_from_table_comment_ddl(ddl)
            if not tbl:
                print(f"comment table name parse failed:\n{ddl}")
                continue
            tbl_full_name = f"{schema}.{tbl}"
            comment_ddls[tbl_full_name].append(ddl)
            continue
        if not ddl:
            continue

    stmts = ""
    # 不再输出已被使用的序列创建语句
    used_sequences = set(seq_attach_ddls.values())
    unused_sequences = set(seq_ddls.keys()) - used_sequences
    if unused_sequences:
        simplified_seqs = []
        for seq in sorted(unused_sequences):
            original_ddl = seq_ddls[seq]
            m = re.match(r'create\s+sequence\s+([^\s]+)', original_ddl, re.IGNORECASE)
            if m:
                seq_full_name = m.group(1)
                simplified_seqs.append(f'create sequence {seq_full_name};')
            else:
                print(f"Sequence name parse failed:\n{original_ddl}")
                simplified_seqs.append(original_ddl + ';')
        stmts += '\n'.join(simplified_seqs) + '\n\n\n'

    for tbl_full_name, ddl in sorted(table_ddls.items()):
        schema, table_name = table_name_from_ddl(ddl)
        columns = []
        ddl_lines = ddl.split('\n')
        ddl_content = '\n'.join(ddl_lines)
        m = re.search(r'\((.*)\)', ddl_content, re.DOTALL)
        if m:
            columns_raw = m.group(1)
            columns_list = re.split(r',\s*(?![^()]*\))', columns_raw)
            for col_def in columns_list:
                col_def = col_def.strip()
                if col_def:
                    columns.append(col_def)
        else:
            print(f"Failed to parse columns for table {tbl_full_name}")
            continue
        # 处理列，修改使用序列的列类型为serial/bigserial
        new_columns = []
        for col_def in columns:
            col_def = col_def.strip()
            col_parts = col_def.split()
            if len(col_parts) < 2:
                new_columns.append(col_def)
                continue
            col_name = col_parts[0]
            col_type = ' '.join(col_parts[1:])
            key = (tbl_full_name, col_name)
            if key in seq_attach_ddls:
                sequence = seq_attach_ddls[key]
                # 检查序列名以确定使用serial还是bigserial
                if 'bigint' in col_type.lower() or 'bigserial' in col_type.lower():
                    col_type = 'bigserial'
                else:
                    col_type = 'serial'
                # 移除默认值中的'not null'和'default'部分
                col_type = re.sub(r'\s+default\s+nextval\(.*\)', '', col_type, flags=re.IGNORECASE)
                col_type = re.sub(r'\s+not\s+null', '', col_type, flags=re.IGNORECASE)
                col_type = col_type.strip()
                # 如果原始列定义有'not null'，则在修改后的类型后添加
                if 'not null' in col_def.lower():
                    col_type += ' not null'
            new_columns.append(f'    {col_name} {col_type}')
        all_defs = new_columns.copy()

        tbl_pk = pk_ddls.get(tbl_full_name)
        if tbl_pk:
            all_defs.append(f'    primary key ({tbl_pk})')

        for uk in sorted(uk_ddls.get(tbl_full_name, [])):
            all_defs.append(f'    unique ({uk})')

        ddl_content = ',\n'.join(all_defs)

        ddl_lines = [f'create table {schema}.{table_name} (\n{ddl_content}\n);']
        ddl = '\n'.join(ddl_lines) + '\n\n'
        idx_list = idx_ddls.get(tbl_full_name, [])
        if idx_list:
            idx = ';\n'.join(sorted(idx_list))
            ddl += idx + ';\n'
        comment_list = comment_ddls.get(tbl_full_name, [])
        if comment_list:
            comment = ';\n'.join(comment_list)
            ddl += comment + ';\n'
        ddl += '\n\n'
        stmts += ddl

    if o == "stdout":
        print(stmts)
        return
    with open(o, 'w') as file:
        file.write(stmts)
