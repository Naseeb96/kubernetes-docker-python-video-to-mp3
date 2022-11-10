import pika, json

# the parameters are
# f = the file to be upload
# fs = GridFS instance
# channel = RabbitMQ Channel
# access = user's access ability
def upload(f, fs, channel, access):
    try:
        #Attempt to put the file in the mongodb database using the grid FS, if successful returns a File ID
        fid = fs.put(f)
    except Exception as err:
        return "Internal Server Error", 500

    # If file upload was successful write a message to the queue
    # message contains video file ID, MP3 File ID (set after conversion is complete), and the sender 
    # of the conversion request(username)
    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"],
    }

    # Put this message on the queue using default RabbitMQ Queue with the routing key of video to distinguish 
    # between uploading a video queue and downloaing the converted mp3 queue
    # json.dumps converts a python object into a json string
    # delivery mode is persistant to make sure events are persistant in the case of a Pod Crash or restart of Pod
    try:
        channel.basic_publish(
            exchange ="",
            routing_key = "video",
            body = json.dumps(message),
            properties = pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    # If we are unable to put this message onto the video Queue
    except:
        # Delete that file from MongoDB -> If there is no message associated with the file that file will not get processed
        # because the downstream service does not know the file exist because it nevers recieves a message notifying it to 
        # process that file
        fs.delete(fid)
        return "Internal Server Error", 500
