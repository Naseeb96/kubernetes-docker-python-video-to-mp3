import os, requests

def login(request):
    auth = request.authorization
    # if there is no authorization parameters in given request
    if not auth:
        return None, ("missing credentials", 401)

    basicAuth = (auth.username, auth.password)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/login", auth=basicAuth
    )

    # Success will return the login token and no errors
    if response.status_code == 200:
        return response.text, None
    # If it failed return no tokens and return the errors from the response
    else:
        return None, (response.text, response.status_code)

