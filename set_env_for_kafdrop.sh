#!/usr/bin/env bash

export KAFKA_KEYSTORE=$(cat secrets/kafka.keystore.jks | base64)
export KAFKA_TRUSTSTORE=$(cat secrets/kafka.truststore.jks | base64)
export KAFKA_PROPERTIES=$(cat kafka.properties | base64)
