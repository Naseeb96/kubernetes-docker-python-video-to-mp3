import os, requests

def token(request):
    #Check to see if request has the proper authorization header
    #If there is not authorization in the header this request has no authorization and no access
    if not "Authorization" in request.headers:
        return None, ("missing credentials, 401")
    token = request.headers["Authorization"]
    # If token doesn't exist the request has no access
    if not token:
        return None, ("missing credentials", 401)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/validate",
        headers={"Authorization": token},
    )
    # Upon Successful response return the body access token
    if response.status_code == 200:
        return response.text, None
    # Upon failure return the errors
    else:
        return None, (response.text, response.status_code)

    
