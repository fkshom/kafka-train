#!/usr/bin/env ruby
require "kafka"
require 'pp'
require 'pry'


module Kafkaa
  module Protocol
    class DescribeConfigsResponse
      def self.decode(decoder)
        pp decoder
        binding.pry
        throttle_time_ms = decoder.int32
        resources = decoder.array do
          error_code = decoder.int16
          error_message = decoder.string

          resource_type = decoder.int8
          if Kafka::Protocol::RESOURCE_TYPES[resource_type].nil?
            raise Kafka::ProtocolError, "Resource type not supported: #{resource_type}"
          end
          resource_name = decoder.string

          configs = decoder.array do
            ConfigEntry.new(
              name: decoder.string,
              value: decoder.string,
              read_only: decoder.boolean,
              is_default: decoder.boolean,
              is_sensitive: decoder.boolean,
            )
          end

          ResourceDescription.new(
            type: RESOURCE_TYPES[resource_type],
            name: resource_name,
            error_code: error_code,
            error_message: error_message,
            configs: configs
          )
        end

        new(throttle_time_ms: throttle_time_ms, resources: resources)
      end
    end

  end
  class Broker
    def describe_configs(**options)
      request = Protocol::DescribeConfigsRequest.new(**options)
      pp request
      a = send_request(request)
      pp a
      a
    end
  end
  class Cluster
    def describe_configs(broker_id, configs = [])
      options = {
        resources: [[Kafka::Protocol::RESOURCE_TYPE_CLUSTER, broker_id.to_s, configs]]
      }

      info = cluster_info.brokers.find {|broker| broker.node_id == broker_id }
      pp info
      broker = @broker_pool.connect(info.host, info.port, node_id: info.node_id)
      pp broker
      response = broker.describe_configs(**options)
      pp response
      response.resources.each do |resource|
        Protocol.handle_error(resource.error_code, resource.error_message)
      end

      response.resources.first.configs
    end
  end
end


logger = Logger.new("kafka.log")
require 'openssl'
OpenSSL::SSL::VERIFY_PEER = OpenSSL::SSL::VERIFY_NONE
brokers = ["localhost:29092"]
kafka = Kafka.new(brokers, client_id: "my-application",
#  ssl_ca_cert: File.read('my_ca_cert.pem'),
#  ssl_client_cert: File.read('my_client_cert.pem'),
#  ssl_client_cert_key: File.read('my_client_cert_key.pem'),
#  ssl_client_cert_key_password: 'my_client_cert_key_password',
  # ssl_ca_certs_from_system: true,
  # ssl_verify_hostname: false,
  # sasl_scram_username: 'kafkaadmin',
  # sasl_scram_password: 'kafkaadmin-pass',
  # sasl_scram_mechanism: 'sha256',
  logger: logger,
)
# pp kafka.methods.sort
# pp kafka.topics
#pp kafka.groups
# pp kafka.brokers
#kafka.deliver_message("Hello, World!", topic: "greetings")
#pp kafka.describe_topic(kafka.topics[0], nil)
#binding.pry
config = kafka.describe_configs(1, nil)
#pp kafka.describe_group(kafka.groups[0])


binding.pry