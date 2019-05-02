#!/usr/bin/env python3
# coding: utf8
import datetime
import mysql.connector
import psycopg2
import psycopg2.extras
import time


class Connection:
    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password


def do_convert(target_database_connections):
    for connection in target_database_connections:
        postgresql_connection = psycopg2.connect(
            host=connection.host,
            database=connection.database,
            user=connection.user,
            password=connection.password)
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

        query = "insert into temperatures.temperatures " \
                "(Core0, Core1, CPU, ATZ1, ATZ2, MB1, MB2, SDA, SDB, SDC, TimeStamp) " \
                "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        psycopg2.extras.execute_batch(
            postgresql_cursor,
            query,
            data,
            page_size=100)

        postgresql_connection.commit()
        postgresql_connection.close()


if __name__ == "__main__":
    g_connections = [
        Connection('192.168.1.7', 'temperatures', 'temperatures', 'temperatures'),
        Connection('192.168.1.14', 'temperatures', 'temperatures', 'temperatures')
    ]
    do_convert(g_connections)
