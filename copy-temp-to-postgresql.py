#!/usr/bin/env python3
# coding: utf8
import datetime
import mysql.connector
import psycopg2
import psycopg2.extras
import time


def do_convert():
    postgresql_connection = psycopg2.connect(
        host='192.168.1.7',
        database='temperatures',
        user='temperatures',
        password='temperatures')
    postgresql_cursor = postgresql_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = 'select max(te.timestamp) as last_timestamp from temperatures.temperatures te'

    postgresql_cursor.execute(query)

    last_timestamp = postgresql_cursor.fetchone()['last_timestamp']
    last_timestamp = last_timestamp if last_timestamp is not None else datetime.datetime(1970, 1, 1, 0, 0, 0, 0)

    mysql_connection = mysql.connector.connect(
        user='booc',
        password='adm232',
        host='192.168.1.14',
        database='temperatures')
    mysql_cursor = mysql_connection.cursor()

    query = 'SELECT Core0, Core1, CPU, ATZ1, ATZ2, MB1, MB2, SDA, SDB, SDC, TimeStamp ' \
            'FROM temperatures.temperatures te WHERE te.Timestamp > %s '

    mysql_cursor.execute(query, (last_timestamp,))
    data = mysql_cursor.fetchall()
    mysql_connection.close()

    ts = time.time()

    for (core0, core1, cpu, atz1, atz2, mb1, mb2, sda, sdb, sdc, timestamp) in data:
        query = "insert into temperatures.temperatures " \
            "(Core0, Core1, CPU, ATZ1, ATZ2, MB1, MB2, SDA, SDB, SDC, TimeStamp) " \
            "values ({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}, '{10}')"\
            .format(core0, core1, cpu, atz1, atz2, mb1, mb2, sda, sdb, sdc, timestamp)

        postgresql_cursor.execute(query)

    postgresql_connection.commit()
    postgresql_connection.close()

    ts = time.time() - ts;
    print(f'{ts} s')

if __name__ == "__main__":
    do_convert()
