#!/usr/bin/env python3
# coding: utf8
import re
import subprocess
import psycopg2
import psycopg2.extras
import datetime
import ptvsd

#ptvsd.enable_attach(address=('192.168.1.14', 3000), redirect_output=True)

#ptvsd.wait_for_attach()

class Connection:
    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password


def exec_shell(shell_command):
    cmd = subprocess.Popen(shell_command, shell=True, stdout=subprocess.PIPE)
    out, err = cmd.communicate()

    if not (err is None):
        return err

    return out.decode(encoding="utf8")

def get_temperature_value(temp_in_string):
    regex = re.compile(r'^.*:+\s+(\++\d+\.\d+)', re.DOTALL)
    temp = regex.findall(temp_in_string)

    if not temp:
        return 0

    return float(temp[0])


def get_temperatures():
    core0 = 0
    core1 = 0
    cpu = 0
    mb1 = 0
    mb2 = 0

    out = exec_shell('sensors it8728-isa-0a30 coretemp-isa-0000')

    for line in out.split("\n"):
        if 'Core 0:' in line:
            core0 = get_temperature_value(line)

        if 'Core 1:' in line:
            core1 = get_temperature_value(line)

        if 'Package id 0:' in line:
            cpu = get_temperature_value(line)

        if 'temp1:' in line:
            mb1 = get_temperature_value(line)

        if 'temp3:' in line:
            mb2 = get_temperature_value(line)

    out = exec_shell('nc localhost 7634')

    temps = out.split('|')
    sda = float(temps[3])
    sdb = float(temps[8])
    sdc = float(temps[13])

    return {'core0': core0, 'core1': core1, 'cpu': cpu, 'mb1': mb1, 'mb2': mb2, 'sda': sda, 'sdb': sdb, 'sdc': sdc, 'timestamp': datetime.datetime.now()}


def do_insert_temperatures(connection: Connection):
    temperatures = get_temperatures()
    postgresql_connection = psycopg2.connect(
        host=connection.host,
        database=connection.database,
        user=connection.user,
        password=connection.password)
    postgresql_cursor = postgresql_connection.cursor()
    
    query = "insert into temperatures.temperatures " \
            "(Core0, Core1, CPU, ATZ1, ATZ2, MB1, MB2, SDA, SDB, SDC, TimeStamp) " \
            "values (%(core0)s, %(core1)s, %(cpu)s, 0, 0, %(mb1)s, %(mb2)s, %(sda)s, %(sdb)s, %(sdc)s, %(timestamp)s)"
            
    postgresql_cursor.execute(query, temperatures)

    postgresql_connection.commit()
    postgresql_connection.close()


if __name__ == "__main__":
    g_connection = Connection('192.168.1.14', 'temperatures', 'temperatures', 'temperatures')    
    do_insert_temperatures(g_connection)
