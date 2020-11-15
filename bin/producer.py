from kafka import KafkaProducer, KafkaAdminClient, NewTopic
import ssl

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
ssl_context.verify_mode = ssl.None
ssl_context.check_hostname = False

kafka_param = {
    'bootstrap_servers': ['localhost:19092'],
    'security_protocol': 'SASL_SSL',
    'sasl_mechanisms': 'PLAIN',
    'sasl_username': "user",
    'sasl_password': "password",
    'ssl_cafile': "/security/ca-chain.cert.pem",
    'ssl_celfile': "/security/producer.cert.pem",
    'ssl_keyfile': "/security/producer.key.pem",
    'ssl_password': "keypassword",
    'ssl_context': ssl_context,
    'ssl_check_hostname': False,
}

def main():
    try:
        admin = KafkaAdminClient(
            **kafka_param
       )

        topic = NewTopic(name='my-topic',
                         num_partitions=1,
                         replication_factor=1)
        admin.create_topics([topic])
    except Exception:
        pass

    producer = KafkaProducer(
        **kafka_param
    )
    for _ in range(100):
        producer.send('foobar', b'some_message_bytes')

if __name__ == "__main__":
    main()