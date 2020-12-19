#!/usr/bin/env python3

from kafka import KafkaClient, KafkaAdminClient
from pprint import pprint as pp
import logging
import sys
logger = logging.getLogger('kafka')
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

# admin = KafkaAdminClient(
#     bootstrap_servers=['localhost:19092','localhost:29092'],
#     security_protocol="SASL_PLAINTEXT",
#     sasl_mechanism="SCRAM-SHA-256",
#     sasl_plain_username="kafkaadmin",
#     sasl_plain_password="kafkaadmin-pass",
# )
# pp(admin.list_consumer_groups())
meta = KafkaClient(
    bootstrap_servers=['localhost:19092','localhost:29092'],
    security_protocol="SASL_PLAINTEXT",
    sasl_mechanism="SCRAM-SHA-256",
    sasl_plain_username="kafkaadmin",
    sasl_plain_password="kafkaadmin-pass",
)
pp(meta.bootstrap_connected())
pp(meta.poll())
pp(meta.cluster.topics())
pp(dir(list(meta.cluster.brokers())[0]))
