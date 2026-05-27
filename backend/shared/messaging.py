import pika
import json

class RabbitMQHandler():
    def __init__(self):
        self.exchange = 'promocoes'
        self.exchange_type = 'topic'
        self.host = 'localhost'
        self.connection = None
        self.channel = None

    def establish_connection(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host, heartbeat=0))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(
            exchange=self.exchange,
            exchange_type=self.exchange_type
        )
    
    def close_connection(self):
        self.connection.close()

    def publish_message(self, routing_key, message_dict):
        message_string = json.dumps(message_dict)

        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=routing_key,
            body=message_string
        )
    
    def declare_queue(self, queue_name=''):
        result = self.channel.queue_declare(queue=queue_name, exclusive=True)
        return result.method.queue
    
    def bind_keys(self, queue, routing_keys):
        for routing_key in routing_keys:
            self.channel.queue_bind(
                exchange=self.exchange,
                queue=queue,
                routing_key=routing_key
            )
    
    def start_consuming(self, queue_name, callback_function):
        self.channel.basic_consume(
            queue=queue_name, 
            on_message_callback=callback_function, 
            auto_ack=True
        )
        print(f"[*] Waiting for messages in {queue_name}. To exit press CTRL+C")
        self.channel.start_consuming()
    