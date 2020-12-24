#!/usr/bin/env python
# coding: utf-8

import subprocess
import shlex
import yaml
import argparse

class dict2(dict): 
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs) 
        self.__dict__ = self 

def run_command(command):
    subprocess.run(shlex.split("echo " + command))

def load_config(filepath):
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def command_ca(args):
    caconfig = dict2(load_config(args.caconfig))

    # Generate CA key
    run_command(
        f"openssl req -new -x509"
        f" -keyout {caconfig.name}.key"
        f" -out {caconfig.name}.crt"
        f" -days 365"
        f" -subj '{caconfig.subject}'"
        f" -passin pass:{caconfig.password} -passout pass:{caconfig.password}"
    )

def command_cert(args):
    caconfig =dict2( load_config(args.caconfig))
    certconfigs = load_config(args.certconfig)
    
    def create_cert(certconfig):
        certconfig = dict2(certconfig)
        # Create keystores
        run_command(
            f"keytool -genkey -noprompt"
            f" -alias {certconfig.hostname}"
            f" -dname '{certconfig.dname}'"
            f" -keystore {certconfig.hostname}.keystore.jks"
            f" -keyalg RSA"
            f" -storepass {certconfig.keystorepass}"
            f" -keypass {certconfig.sslkeypass}"
        )

        # Create CSR, sign the key and import back into keystore
        run_command(
            f"keytool -certreq -noprompt"
            f" -keystore {certconfig.hostname}.keystore.jks"
            f" -alias {certconfig.hostname}"
            f" -file {certconfig.hostname}.csr"
            f" -storepass {certconfig.keystorepass}"
            f" -keypass {certconfig.sslkeypass}"
        )
        run_command(
            f"openssl x509 -req"
            f" -CA {caconfig.name}.crt"
            f" -CAkey {caconfig.name}.key"
            f" -in {certconfig.hostname}.csr"
            f" -out {certconfig.hostname}.crt"
            f" -days 9999"
            f" -CAcreateserial"
            f" -passin pass:{caconfig.password}"
        )
        run_command(
            f"keytool -import -noprompt"
            f" -keystore {certconfig.hostname}.keystore.jks"
            f" -alias CARoot"
            f" -file {caconfig.name}.crt"
            f" -storepass {certconfig.keystorepass}"
            f" -keypass {certconfig.sslkeypass}"
        )
        run_command(
            f"keytool -import -noprompt"
            f" -keystore {certconfig.hostname}.keystore.jks"
            f" -alias {certconfig.hostname}"
            f" -file {certconfig.hostname}.crt"
            f" -storepass {certconfig.keystorepass}"
            f" -keypass {certconfig.sslkeypass}"
        )
        run_command(
            f"keytool -import -noprompt"
            f" -keystore {certconfig.hostname}.truststore.jks"
            f" -alias CARoot"
            f" -file {caconfig.name}.crt"
            f" -storepass {certconfig.truststorepass}"
            f" -keypass {certconfig.sslkeypass}"
        )
        with open(f"{certconfig.hostname}_sslkey_creds", mode='w') as f:
            f.write(certconfig.sslkeypass)
        with open(f"{certconfig.hostname}_keystore_creds", mode='w') as f:
            f.write(certconfig.keystorepass)
        with open(f"{certconfig.hostname}_truststore_creds", mode='w') as f:
            f.write(certconfig.truststorepass)

    if type(certconfigs) is list:
        for certconfig in certconfigs:
            create_cert(certconfig)
    elif type(certconfigs) is dict:
        certconfig = certconfigs
        create_cert(certconfig)
    else:
        print("Cert config file format error. It must be array or dict.")

parser = argparse.ArgumentParser(description='jks generator')
subparsers = parser.add_subparsers()

parser_ca = subparsers.add_parser('ca', help='see `ca -h`')
parser_ca.add_argument('--caconfig', required=True, help='ca configuration file')
parser_ca.set_defaults(handler=command_ca)

parser_cert = subparsers.add_parser('cert', help='see `cert -h`')
parser_cert.add_argument('--caconfig', required=True, help='ca configuration file')
parser_cert.add_argument('--certconfig', required=True, help='cert configuration file')
parser_cert.set_defaults(handler=command_cert)

args = parser.parse_args()
if hasattr(args, 'handler'):
    args.handler(args)
else:
    parser.print_help()