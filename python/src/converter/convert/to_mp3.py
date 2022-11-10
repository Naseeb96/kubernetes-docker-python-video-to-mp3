import pika, json, tempfile, os 
from bson.objectid import ObjectId
import moviepy.editor

def start(message, fs_videos, fs_mp3s, channel):

    #load the message and deserialize the json into a usable python object
    message = json.loads(message)

    # empty temp file
    tf = tempfile.NamedTemporaryFile()

    # video contents
    out = fs_videos.get(ObjectId(message["video_fid"]))

    # add video contents to empty file
    tf.write(out.read())

    # extract just the audio from the temp video file
    audio = moviepy.editor.VideoFileClip(tf.name).audio
    # close and delete the temp file
    tf.close()

    # write audio to the file
    tf_path = tempfile.gettempdir() + f"/{message['video_fid']}.mp3"
    audio.write_audiofile(tf_path)

    # Save file to MongoDB
    f = open(tf_path,"rb")
    data = f.read()
    fid = fs_mp3s.put(data)
    # delete temp file
    f.close()
    os.remove(tf_path)

    message["mp3_fid"] = str(fid)

    try:
        channel.basic_publish (
            exchange="",
            routing_key=os.environ.get("MP3_QUEUE"),
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE),
        ),
    except Exception as err:
        # If we cant put the message on the que delete the file otherwise it will never get procesed and get stuck
        fs_mp3s.delete(fid)
        return "Failed to publish message"
