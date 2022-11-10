import jwt, datetime, os 
from flask import Flask, request
from flask_mysqldb import MySQL

#Configure server with Flask so request to routes can interface with code
server = Flask (__name__)
#Use MySQL so application can access and query from databse 
mysql = MySQL(server)

#Configure server details
server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
server.config["MYSQL_PORT"] = os.environ.get("MYSQL_PORT")


#Login route
@server.route("/login", methods=["POST"])
def login():
    auth = request.authorization

    # if pieces of the authentication scheme is missing or not found return with error code 401
    # error code 401 is a standard in HTTP protocol and means "client request could not be completed
    # because it lacks valid authentication credential for the requested resource"
    if not auth:
        return "missing credentials", 401

    # Check the database for username and password
    cur = mysql.connection.cursor()
    res = cur.execute(
        "SELECT email, password FROM user WHERE email=%s", (auth.username)
    )
    
    # res greater than 0 means that the user that was entered exists in the  user database
    if res > 0:
        user_row = cur.fetchone()
        email = user_row[0]
        password = user_row[1]

        #If authentcation failed with incorrect email/username and/or incorrect password
        if auth.username != email or auth.password != password:
            return "Invalid Credentials", 401
        # Authentication Passed
        else:
            return createJWT(auth.username, os.environment.get("JWT_SECRET"), True)
    
    # User not found in the database -> User does not have access
    else:
        return "Invalid Credentials the User: " + auth.username + " has not been found", 401


@server.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers["Authorization"]

    # if jwt is not found in the header return an error 401
    if not encoded_jwt:
        return "Missing Credentials", 401
    
    # expecting input to be Bearer <token> so the encoded jwt is the 1 index.   split(" ") sections it 
    # so that Bearer is 0 index and the token is 1 index
    encoded_jwt = encoded_jwt.split(" ")[1]
    try:
        decoded = jwt.decode(
            encoded_jwt, os.environ.get("JWT_SECRET"), algorithm=["HS256"]
        )
    except:
        # If the try fails then the client is not authorized. Error code 403 is a standard HTTP response
        # Error Code 403 means the client lacks valid permission to accessing the valid URL, Server understands
        # the request but cannot fulfill the request because the client is not authorized
        return "Not Authorized", 403

    #Success return the validated decoded token with code 200. Code 200 is a standard HTTP response which means ok/success
    return decoded, 200

def createJWT(username, secret, isAdmin):
    return jwt.encode(
        {
            "username" : username,
            #Let the token access expire in 1 day (24 hours) after creation
            "expiration" : datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
            # Get the current time of when token was created
            "iat": datetime.datetime.utcnow(),
            # Boolean thats passed in to figure out whether to give admin access if isAdmin = True user has admin access
            "admin" : isAdmin,
        },
        secret,
        algorithm="HS256",
    )

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000)



        


