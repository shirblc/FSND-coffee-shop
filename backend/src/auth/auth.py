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
'''
@TODO implement get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''
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


'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here:
    https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
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

    # Try to decode the JWT
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


'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in
    the payload permissions array
    return true otherwise
'''
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


'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check
    the requested permission
    return the decorator which passes the decoded payload to the decorated
    method
'''
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
