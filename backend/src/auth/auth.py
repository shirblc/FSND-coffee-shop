import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'dev-sbac.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffeeshop'


# AuthError Exception
# A standardized way to communicate auth failure modes
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header

# Function: get_token_auth_header
# Description: Gets the request's 'Authorization' header. Checks to see whether
#              said header exists; whether the header is comprised of two
#              parts; and whether the first part is 'bearer'. This serves as
#              preliminary verification that the JWT is in the correct form.
# Parameters: None
# Returns: auth_list[1] - The JSON web token.
def get_token_auth_header():
    # Checks whether the authorisation header is in the request. If not,
    # raises an authorisation error.
    if('Authorization' not in request.headers):
        raise AuthError({
                        'code': 401,
                        'description': 'Unauthorised.'
                        }, 401)

    auth_header = request.headers.get('Authorization')
    auth_list = auth_header.split(" ")

    # Checks whether the authorisation header contains two parts. If not,
    # raises an authorisation error.
    if(len(auth_list) != 2):
        raise AuthError({
                        'code': 401,
                        'description': 'Unauthorised.'
                        }, 401)

    # Checks whether the first part of the authorisation header is the word
    # 'bearer'. If not, raises an authorisation error.
    if(auth_list[0].lower() != 'bearer'):
        raise AuthError({
                        'code': 401,
                        'description': 'Unauthorised.'
                        }, 401)

    return auth_list[1]


# Function: verify_decode_jwt
# Description: Gets the token and attempts to decode and verify it using the
#              Auth0 JWKS (JSON Web Key Set) JSON. Ensures that the JWT is
#              authentic, still valid and hasn't been tampered with.
# Parameters: token - a JSON Web Token.
# Returns: payload - The payload from the decoded token.
def verify_decode_jwt(token):
    # Gets the JWKS json to decode the JWT
    jsonurl = urlopen(f'https://' + AUTH0_DOMAIN + '/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    token_header = jwt.get_unverified_header(token)
    rsa_key = {}

    # If the 'kid' key doesn't exist in the token header
    if('kid' not in token_header):
        raise AuthError({
                        'code': 401,
                        'description': 'Unauthorised.'
                        }, 401)

    # Gets the JWKS from the JSON
    for key in jwks['keys']:
        if key['kid'] == token_header['kid']:
            rsa_key = {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'use': key['use'],
                    'n': key['n'],
                    'e': key['e']
                }

    # Try to decode and validate the JWT
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )
        # If the signature expired
        except jwt.ExpiredSignatureError:
            raise AuthError({
                            'code': 401,
                            'description': 'Unauthorised. The token expired.'
                            }, 401)
        # If any claim(s) is (are) invalid
        except jwt.JWTClaimsError:
            raise AuthError({
                            'code': 401,
                            'description': ''
                            }, 401)
        # If the JWT signature is invalid
        except jwt.JWTError:
            raise AuthError({
                            'code': 401,
                            'description': ''
                            }, 401)
        # If there was any other error decoding the JWT
        except Exception as e:
            raise AuthError({
                            'code': 401,
                            'description': ''
                            }, 401)

    return payload


# Function: check_permissions
# Description: Checks the payload from of the decoded, verified JWT for
#              permissions. Then compares the user's permissions to the
#              required permission to check whether the user is allowed to
#              access the given resource.
# Parameters: permission (string) - The resource's required permission.
#             payload - The payload from the decoded, verified JWT.
# Returns: True - Boolean confirming the user has the required permission.
def check_permissions(permission, payload):
    # If there are no permissions in the payload, raises an AuthError
    if('permissions' not in payload):
        raise AuthError({
                        'code': 403,
                        'description':
                        'You do not have permission to perform that action.'
                        }, 403)

    user_permissions = payload['permissions']

    # If the needed permission isn't in the user's permissions, raises an error
    if(permission not in user_permissions):
        raise AuthError({
                        'code': 403,
                        'description':
                        'You do not have permission to perform that action.'
                        }, 403)

    return True


# @requires_auth() Decorator Definition
# Description: Gets the Authorization header, verifies the JWT and checks
#              the user has the required permissions using the functions above.
# Parameters: permission (string) - The resource's required permission.
# Returns: @requires_auth decorator.
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
