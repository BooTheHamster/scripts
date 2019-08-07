#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import shutil
import os
import socket
import datetime
import secrets
import string
from pathlib import Path
from subprocess import check_output


class Configuration:
    required_packages = ['strongswan', 'strongswan-pki']
    server_root_key = 'ca-key.pem'
    server_root_ca = 'ca-cert.pem'
    vpn_server_key = 'server-key.pem'
    vpn_server_cert = 'server-cert.pem'
    vpn_server_distinguished_name = '"C=RU, O=x5x VPN Server {0}, CN={1}"'
    certs_folder = 'pki'


class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    OK = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def log_step(message: str):
    print("{0}{1}{2}".format(bcolors.HEADER, message, bcolors.ENDC))


def log(message: str):
    print("  {0}".format(message))


def exec_shell(shell_command):
    cmd = subprocess.Popen(
        shell_command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = cmd.communicate()

    if err:
        raise Exception(str(err, 'utf-8'))

    return out.decode(encoding='utf8')


def exec_shell_screen(shell_command):
    cmd = subprocess.Popen(
        shell_command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True)

    for line in iter(cmd.stdout.readline, ""):
        print(u"  ", end="")
        print(line.strip())

    cmd.stdout.close()
    cmd.wait()


def chown_root(file: Path, mode: str):
    cmd = 'sudo chown root {0}' \
        .format(file)
    exec_shell_screen(cmd)

    cmd = 'sudo chgrp root {0}' \
        .format(file)
    exec_shell_screen(cmd)

    cmd = 'sudo chmod {mode} {file}' \
        .format(mode=mode, file=file)
    exec_shell_screen(cmd)


def copy_to_etc(source: Path, target_folder: Path = None):
    if target_folder:
        target = target_folder
    else:
        target = Path('/etc')

    target = target.joinpath(source.name)

    cmd = 'sudo rm -vf {0}'.format(target)
    exec_shell_screen(cmd)

    cmd = 'sudo cp -v {source} {target}' \
        .format(source=source,
                target=target)
    exec_shell_screen(cmd)

    chown_root(target, '644')


def check_packages(required_packages: []):
    log_step(u"Проверка установленных пакетов ...")

    need_to_install_packages = []

    for package_name in required_packages:
        check_cmd = (
            "dpkg-query -W --showformat='${{Status}}'"
            " {0}").format(package_name)
        result = exec_shell(check_cmd)

        if 'install ok installed' in result:
            log("{0}: установлен".format(package_name))
        else:
            need_to_install_packages.append(package_name)

    return need_to_install_packages


def install_packages(packages_to_install: []):
    log_step(u"Установка пакетов ...")

    install_cmd = "sudo apt-get --yes install " + \
        " ".join(packages_to_install)
    exec_shell_screen(install_cmd)


def create_certificates_directory():
    log_step(u"Создание каталога сертификатов ...")
    pki_folder = Path(Path.joinpath(Path.home(), Configuration.certs_folder))

    if pki_folder.exists():
        shutil.rmtree(pki_folder.as_posix())

    pki_cacerts_folder = pki_folder.joinpath('cacerts')
    pki_certs_folder = pki_folder.joinpath('certs')
    pki_private_folder = pki_folder.joinpath('private')

    pki_folder.mkdir()
    pki_cacerts_folder.mkdir()
    pki_certs_folder.mkdir()
    pki_private_folder.mkdir()

    log("Каталог сертификатов: {0}".format(pki_folder))
    log("   {0}".format(pki_cacerts_folder))
    log("   {0}".format(pki_certs_folder))
    log("   {0}".format(pki_private_folder))
    return (pki_cacerts_folder, pki_certs_folder, pki_private_folder)


def create_server_root_key(server_root_key: Path):
    log_step(u"Создание корневого ключа ...")
    cmd = 'ipsec pki --gen --type rsa --size 4096 --outform pem'
    result = exec_shell(cmd)

    with server_root_key.open("wt") as f:
        f.write(result)


def create_server_root_ca(server_root_key: Path,
                          distinguished_name: str,
                          server_root_ca: Path):
    log_step(u"Создание корневого сертификата ...")
    cmd = 'ipsec pki --self --ca --lifetime 3650 ' \
        '--in {server_root_key} ' \
        '--type rsa --dn {distinguished_name} ' \
        '--outform pem'.format(server_root_key=server_root_key,
                               distinguished_name=distinguished_name)
    result = exec_shell(cmd)

    with server_root_ca.open("wt") as f:
        f.write(result)


def create_vpn_server_key(vpn_server_key: Path):
    log_step(u"Создание ключа VPN сервера ...")
    cmd = 'ipsec pki --gen --type rsa --size 4096 --outform pem'
    result = exec_shell(cmd)

    with vpn_server_key.open("wt") as f:
        f.write(result)


def create_vpn_server_cert(vpn_server_key: Path,
                           server_root_ca: Path,
                           server_root_key: Path,
                           vpn_server_cert: Path,
                           distinguished_name: str,
                           server_name_or_ip: str):
    log_step(u"Создание сертификата VPN сервера ...")
    cmd = (
        'ipsec pki --pub --in {vpn_server_key} '
        '--type rsa | ipsec pki --issue --lifetime 1825 '
        '--cacert {server_root_ca} '
        '--cakey {server_root_key} '
        '--dn "{distinguished_name}" '
        '--san "{server_name_or_ip}" '
        '--flag serverAuth --flag ikeIntermediate '
        '--outform pem'
    ).format(vpn_server_key=vpn_server_key,
             server_root_ca=server_root_ca,
             server_root_key=server_root_key,
             distinguished_name=distinguished_name,
             server_name_or_ip=server_name_or_ip)
    result = exec_shell(cmd)

    with vpn_server_cert.open("wt") as f:
        f.write(result)


def copy_certificates_to_etc(server_root_key: Path,
                             server_root_ca: Path,
                             vpn_server_key: Path,
                             vpn_server_cert: Path):
    log_step((u"Копирование ключей и сертификатов в каталог "
              u"настроек ..."))
    etc_ipsec = Path('/etc/ipsec.d')

    for path in [server_root_key, server_root_ca, vpn_server_key, vpn_server_cert]:
        etc_path = Path.joinpath(etc_ipsec, path.parent.parts[-1])        
        copy_to_etc(path, etc_path)


def create_ipsec_config(ipsec_config: Path,
                        vpn_server_cert: Path,
                        server_name_or_ip: str):
    log_step(u"Создание файла конфигурации IPSec")

    config = """
# ipsec.conf - strongSwan IPsec configuration file
# basic configuration

config setup
    # strictcrlpolicy=yes
    uniqueids=no
    charondebug="ike 1, knl 1, cfg 2"

conn ikev2-vpn
    auto=add
    compress=no
    type=tunnel
    keyexchange=ikev2
    fragmentation=yes
    forceencaps=yes
    dpdaction=clear
    dpddelay=35s
    dpdtimeout=300s
    rekey=no

    # left - local (server) side
    left=%any
    leftauth=pubkey
    leftid={server_name_or_ip}
    leftcert={vpn_server_cert}
    leftsendcert=always
    leftsubnet=0.0.0.0/0

    # right - remote (client) side
    right=%any
    rightid=%any
    rightauth=eap-mschapv2
    rightsourceip=10.10.10.0/24
    rightdns=8.8.8.8,8.8.4.4
    rightsendcert=never

    eap_identity=%identity    

""".format(server_name_or_ip=server_name_or_ip,
           vpn_server_cert=vpn_server_cert.name)

    with ipsec_config.open("wt") as f:
        f.write(config)

    copy_to_etc(ipsec_config)


def create_ipsec_secrets(username: str,
                         password: str,
                         ipsec_secrets: Path,
                         vpn_server_key: Path,
                         server_name_or_ip: str):
    log_step(u"Создание файла конфигурации IPSec secrets")

    config = """
# This file holds shared secrets or RSA private keys for authentication.

# RSA private key for this host, authenticating it to any other host
# which knows the public part.

{server_name_or_ip} : RSA {vpn_server_key}

{username} %any% : EAP "{password}"

""".format(server_name_or_ip=server_name_or_ip,
           vpn_server_key=vpn_server_key.name,
           username=username,
           password=password)

    with ipsec_secrets.open("wt") as f:
        f.write(config)

    copy_to_etc(ipsec_secrets)


def restart_strongswan_service():
    log_step(u"Перезапуск IPSec")
    cmd = 'sudo systemctl restart strongswan'
    exec_shell_screen(cmd)

def do_configure_vpn():
    packages_to_install = check_packages(Configuration.required_packages)

    if packages_to_install:
        install_packages(packages_to_install)

    pki_cacerts_folder, pki_certs_folder, pki_private_folder = create_certificates_directory()
    server_root_key = pki_private_folder.joinpath(Configuration.server_root_key)
    server_root_ca = pki_cacerts_folder.joinpath(Configuration.server_root_ca)
    vpn_server_key = pki_private_folder.joinpath(Configuration.vpn_server_key)
    vpn_server_cert = pki_certs_folder.joinpath(Configuration.vpn_server_cert)
    server_name_or_ip = socket.gethostbyname(socket.getfqdn())
    ipsec_config = Path.home().joinpath("ipsec.conf")
    ipsec_secrets = Path.home().joinpath("ipsec.secrets")
    distinguished_name = Configuration.vpn_server_distinguished_name \
       .format(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'), server_name_or_ip)
    username = ''.join(secrets.choice(string.ascii_lowercase) for i in range(8))
    password = ''.join(secrets.choice(string.ascii_lowercase) for i in range(8))

    create_server_root_key(server_root_key)
    create_server_root_ca(server_root_key,
                          distinguished_name,
                          server_root_ca)
    create_vpn_server_key(vpn_server_key)
    create_vpn_server_cert(vpn_server_key,
                           server_root_ca,
                           server_root_key,
                           vpn_server_cert,
                           distinguished_name,
                           server_name_or_ip)
    copy_certificates_to_etc(server_root_key, server_root_ca, vpn_server_key, vpn_server_cert)
    create_ipsec_config(ipsec_config, vpn_server_cert, server_name_or_ip)    
    create_ipsec_secrets(username, password, ipsec_secrets, vpn_server_key, server_name_or_ip)
    restart_strongswan_service()

if __name__ == "__main__":
    do_configure_vpn()
