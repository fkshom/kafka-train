#!/usr/bin/env python3
# coding: utf-8

import subprocess
import shlex
import yaml
import os
import argparse
from logging import getLogger, StreamHandler, Formatter, DEBUG

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
handler.setFormatter(Formatter('[%(levelname)s] %(message)s'))
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

dryrun = False

class dict2(dict): 
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs) 
        self.__dict__ = self

def run_command(command):
    logger.debug(command)
    if dryrun:
        print("This is dry-run")
    else:
        subprocess.run(shlex.split(command))

def load_config(filepath):
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def command_ca(args):
    caconfig = dict2(load_config(args.caconfig))
    outdir = args.out_dir
    global dryrun
    dryrun = args.dry_run
    capassword = args.capassword

    if capassword is None:
        if caconfig.get('password'):
            capassword = caconfig.password
        else:
            capassword = input("Input capassword: ")

    if not dryrun:
        os.makedirs(outdir, exist_ok=True)

    # Generate CA key
    run_command(
        f"openssl req -new -x509"
        f" -keyout {outdir}/{caconfig.name}.key"
        f" -out {outdir}/{caconfig.name}.crt"
        f" -days 365"
        f" -subj '{caconfig.subject}'"
        f" -passin pass:{capassword} -passout pass:{capassword}"
    )


def command_cert(args):
    caconfig = dict2(load_config(args.caconfig))
    certconfigs = load_config(args.certconfig)
    outdir = args.out_dir
    cadir = args.ca_dir
    global dryrun
    dryrun = args.dry_run

    capassword = args.capassword
    certpassword = args.password

    if capassword is None:
        if caconfig.get('password'):
            capassword = caconfig.password
        else:
            capassword = input("Input capassword: ")

    if not dryrun:
        os.makedirs(outdir, exist_ok=True)

    def create_cert(certconfig, certpassword=None):
        certconfig = dict2(certconfig)

        if certpassword is None:
            if certconfig.get('password'):
                certpassword = certconfig.password
            else:
                certpassword = input("Input cert password: ")

        keystorepassword = certpassword
        sslkeypassword = certpassword
        truststorepassword = certpassword

        # Create keystores
        run_command(
            f"keytool -genkey -noprompt"
            f" -alias {certconfig.hostname}"
            f" -dname '{certconfig.dname}'"
            f" -keystore {outdir}/{certconfig.hostname}.keystore.jks"
            f" -keyalg RSA"
            f" -storepass {keystorepassword}"
            f" -keypass {sslkeypassword}"
        )

        # Create CSR, sign the key and import back into keystore
        run_command(
            f"keytool -certreq -noprompt"
            f" -keystore {outdir}/{certconfig.hostname}.keystore.jks"
            f" -alias {certconfig.hostname}"
            f" -file {outdir}/{certconfig.hostname}.csr"
            f" -storepass {keystorepassword}"
            f" -keypass {sslkeypassword}"
        )
        with open('/tmp/ssl.conf', 'w') as f:
            import textwrap
            f.write(textwrap.dedent("""
            [SAN]
            subjectAltName=@alt_names
            basicConstraints=CA:FALSE
            [alt_names]
            """))
            for index, dns in enumerate(certconfig.dns):
                f.write(f"DNS.{index+1}={dns}\n")
            for index, ip in enumerate(certconfig.ip):
                f.write(f"IP.{index+1}={ip}\n")

        with open('/tmp/ssl.conf', 'r') as f:
            print(f.read())

        run_command(
            f"openssl x509 -req"
            f" -CA {cadir}/{caconfig.name}.crt"
            f" -CAkey {cadir}/{caconfig.name}.key"
            f" -in {outdir}/{certconfig.hostname}.csr"
            f" -out {outdir}/{certconfig.hostname}.crt"
            f" -days 9999"
            f" -CAcreateserial"
            f" -passin pass:{capassword}"
            f" -extensions SAN -extfile /tmp/ssl.conf"
        )
        run_command(
            f"keytool -import -noprompt"
            f" -keystore {outdir}/{certconfig.hostname}.keystore.jks"
            f" -alias CARoot"
            f" -file {cadir}/{caconfig.name}.crt"
            f" -storepass {keystorepassword}"
            f" -keypass {sslkeypassword}"
        )
        run_command(
            f"keytool -import -noprompt"
            f" -keystore {outdir}/{certconfig.hostname}.keystore.jks"
            f" -alias {certconfig.hostname}"
            f" -file {outdir}/{certconfig.hostname}.crt"
            f" -storepass {keystorepassword}"
            f" -keypass {sslkeypassword}"
        )
        run_command(
            f"keytool -import -noprompt"
            f" -keystore {outdir}/{certconfig.hostname}.truststore.jks"
            f" -alias CARoot"
            f" -file {cadir}/{caconfig.name}.crt"
            f" -storepass {truststorepassword}"
            f" -keypass {sslkeypassword}"
        )
        # with open(f"{certconfig.hostname}_sslkey_creds", mode='w') as f:
        #     f.write(certconfig.sslkeypass)
        # with open(f"{certconfig.hostname}_keystore_creds", mode='w') as f:
        #     f.write(certconfig.keystorepass)
        # with open(f"{certconfig.hostname}_truststore_creds", mode='w') as f:
        #     f.write(certconfig.truststorepass)

    if type(certconfigs) is list:
        for certconfig in certconfigs:
            create_cert(certconfig, certpassword=certpassword)
    elif type(certconfigs) is dict:
        certconfig = certconfigs
        create_cert(certconfig, certpassword=certpassword)
    else:
        print("Cert config file format error. It must be array or dict.")


parser = argparse.ArgumentParser(description='jks generator')
subparsers = parser.add_subparsers()

parser_ca = subparsers.add_parser('ca', help='see `ca -h`')
parser_ca.add_argument('--caconfig', required=True, help='ca configuration file')
parser_ca.add_argument('--dry-run', required=False, action='store_true', default=False, help='enable dry run mode')
parser_ca.add_argument('--out-dir', required=False, default='/ssl/ca', help='enable dry run mode')
parser_ca.add_argument('--capassword', required=False, help='enable dry run mode')
parser_ca.set_defaults(handler=command_ca)

parser_cert = subparsers.add_parser('cert', help='see `cert -h`')
parser_cert.add_argument('--caconfig', required=True, help='ca configuration file')
parser_cert.add_argument('--certconfig', required=True, help='cert configuration file')
parser_cert.add_argument('--dry-run', required=False, action='store_true', default=False, help='enable dry run mode')
parser_cert.add_argument('--out-dir', required=False, default='/ssl', help='enable dry run mode')
parser_cert.add_argument('--ca-dir', required=False, default='/ssl/ca', help='enable dry run mode')
parser_cert.add_argument('--capassword', required=False, help='enable dry run mode')
parser_cert.add_argument('--password', required=False, help='enable dry run mode')
parser_cert.set_defaults(handler=command_cert)

args = parser.parse_args()
if hasattr(args, 'handler'):
    args.handler(args)
else:
    parser.print_help()