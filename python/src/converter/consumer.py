import pika, sys, os, time
from pymongo import MongoClient
import gridfs 
from convert import to_mp3

def main():
    client = MongoClient("host.minikube.internal", 27017)

    # Access to the videos and mp3s databases that exist within MongoDB
    db_videos = client.videos
    db_mp3s = client.mp3s

    #GridFS
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    #RabbitMQ Synchronous Connection
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq")
    )

    channel = connection.channel()

    def callback(ch, method, properties, body):
        err = to_mp3.start(body, fs_videos, fs_mp3s, ch)

        # if theres an error send a negtive acknowledgement to the channel so the message is not removed from the queue
        # and can be processed again by another consumer
        if err:
            ch.basic_nack(delivery_tag=method.delivery_tag)
        # if there was no error then acknowledge
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("VIDEO_QUEUE"), on_message_callback=callback
    )

    print ("Waiting for messages... To exit press CTRL+C")

    channel.start_consuming()

    if __name__ == "__main__":
        try:
            main()

        # Gracefully shutting down this service in the event we do a keyboard interrupt
        except KeyboardInterrupt:
            print("Interrupted")
            try:
                sys.exit(0)
            except:
                os.exit(0)


