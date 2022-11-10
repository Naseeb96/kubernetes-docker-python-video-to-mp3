import os, gridfs, pika, json
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util
from bson.objectid import ObjectId

server = Flask(__name__)

# PyMongo wraps Flask server which allows the server to interact with MongoDB
# Access to the video database where the user uploads the video to
mongo_video = PyMongo(server, uri="mongodb://host.minikube.internal:27017/videos")
# Access to the mp3 database where the program deposits converted mp3 from video to so the user can download it
mongo_mp3 = PyMongo(server, uri="mongodb://host.minikube.internal:27017/mp3s")


# Use GridFS because the default mongo uses BSON files with a maximum of 16MB (this is to ensure that
# a single document doesnt use an excessive amount of RAM or bandwith during trasmission)
# GridFS allows us to use files larger than 16 MB by sharding the files -> dividing the file into chunks and storing
# the files as "pieces of the pie" instead of the entire pie. Each chunk is a maximum of 255KiloBytes.
# GridFS stores 2 collections, one is a collection of the chunks the other is the metadata.
# GridFS Wraps mongo database to enables the ability to use Mongo GridFS
fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

#Configure RabbitMQ connection
#Blocking connection makes the connection with RabbitMQ Queue Synchronous
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()

#Login Route
@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)
    
    # If login was successful (no errors) we can return the token
    if not err:
        return token
    # If login was unsuccessfulwe we can return the error
    else:
        return err

#Upload Route -> Route the client will use to upload the desired video to convert it to an MP3
@server.route("/upload", methods=["POST"])
def upload():
    # Validate the token to figure out whether client has access
    access, err = validate.token(request)

    # If we have an error when validating, return that error
    if err:
        return err
    
    # Convert the json object that was returned into a python object
    access = json.loads(access)

    # if the request has admin privileges then the user has access to this feature
    if access["admin"]:
        if len(request.files) > 1 or len(request.files) < 1:
            return "exactly 1 file is required", 400
         # For every file in the users request, upload that file
        for _,f in request.files.items():
            err.util.upload(f, fs_videos, channel, access)

            if err:
                return err
        
        #If For loop completes every file was successful
        return "SUCCESS!", 200
    #If the user is not authorized
    else:
        return "Not Authorized", 401

#Download Route -> Route the client will use to download the mp3 from the desired uploded video
@server.route("/download", methods=["GET"])
def download():
    # Validate the token to figure out whether client has access
    access, err = validate.token(request)

    # If we have an error when validating, return that error
    if err:
        return err
    
    # Convert the json object that was returned into a python object
    access = json.loads(access)

    # if the request has admin privileges then the user has access to this feature
    if access["admin"]:
        # Make sure the File ID exists in the requests
        fid_string = request.args.get("fid")

        #If the File ID is not found
        if not fid_string:
            return "A File ID is required", 400
        
        # If File Id does exist use to get the file from the MongoB MP3 Database
        try:
            out = fs_mp3s.get(ObjectId(fid_string))
            return send_file(out, download_name=f'{fid_string}.mp3')
        except Exception as err:
            print(err)
            return "Internal Service Error", 500
            
    # If the request has no access
    return "Not Authorized", 401
    

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)