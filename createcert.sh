#!/usr/bin/env bash

set -xu
# trap ctrl-c and call ctrl_c()
trap ctrl_c INT

function ctrl_c() {
  echo "** Trapped CTRL-C"
  exit 1
}

mkdir -p /work/ssl
cd /work/ssl

PASSWORD=test1234
VALIDITY=365

# create CA
openssl req -new -x509 -keyout ca-key -out ca-cert -days $VALIDITY -subj "/C=US/ST=California/L=San Diego/O=Development/OU=Dev/CN=example.com" -passout pass:$PASSWORD
keytool -import -keystore kafka.server.truststore.jks -alias CARoot -file ca-cert -storepass $PASSWORD -keypass $PASSWORD -noprompt
keytool -import -keystore kafka.client.truststore.jks -alias CARoot -file ca-cert -storepass $PASSWORD -keypass $PASSWORD -noprompt

# Create server cert
keytool -genkey -keystore kafka.server.keystore.jks -alias localhost -validity $VALIDITY \
   -dname "CN=mqttserver.ibm.com, OU=ID, O=IBM, L=Hursley, S=Hants, C=GB" -storepass $PASSWORD -keypass $PASSWORD -noprompt
keytool -certreq -keystore kafka.server.keystore.jks -alias localhost -file cert-file -storepass $PASSWORD -keypass $PASSWORD -noprompt
openssl x509 -req -CA ca-cert -CAkey ca-key -in cert-file -out cert-signed -days $VALIDITY -CAcreateserial -passin pass:$PASSWORD
keytool -import -keystore kafka.server.keystore.jks -alias CARoot -file ca-cert -storepass $PASSWORD -keypass $PASSWORD -noprompt
keytool -import -keystore kafka.server.keystore.jks -alias localhost -file cert-signed -storepass $PASSWORD -keypass $PASSWORD -noprompt
rm cert-file cert-signed

# Create client cert
keytool -genkey -keystore kafka.client.keystore.jks -alias localhost -validity $VALIDITY \
   -dname "CN=mqttserver.ibm.com, OU=ID, O=IBM, L=Hursley, S=Hants, C=GB" -storepass $PASSWORD -keypass $PASSWORD -noprompt
keytool -certreq -keystore kafka.client.keystore.jks -alias localhost -file cert-file -storepass $PASSWORD -keypass $PASSWORD -noprompt
openssl x509 -req -CA ca-cert -CAkey ca-key -in cert-file -out cert-signed -days $VALIDITY -CAcreateserial -passin pass:$PASSWORD
keytool -import -keystore kafka.client.keystore.jks -alias CARoot -file ca-cert -storepass $PASSWORD -keypass $PASSWORD -noprompt
keytool -import -keystore kafka.client.keystore.jks -alias localhost -file cert-signed -storepass $PASSWORD -keypass $PASSWORD -noprompt
rm cert-file cert-signed
