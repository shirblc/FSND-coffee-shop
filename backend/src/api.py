import os
import sys
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from ast import literal_eval

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

# CORS Setup
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET, POST, PATCH, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers',
                         'Authorization, Content-Type')
    return response


'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()


# ROUTES
# ---------------------------------------------------------------------------#
# Endpoint: GET /drinks
# Description: Gets the list of drinks currently available, with each drink's
#              short data representation.
# Parameters: None.
# Authorization: None.
@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.all()
    drinks_short_format = []

    # Checks whether there are drinks in the database
    if drinks:
        # Gets each drink's short data representation
        for drink in drinks:
            drinks_short_format.append(drink.short())
    else:
        abort(404)

    return jsonify({
                    'success': True,
                    'drinks': drinks_short_format
    })


# Endpoint: GET /drinks-detail
# Description: Gets the list of drinks currently available, with each drink's
#              long data representation.
# Parameters: jwt - JSON Web Token.
# Authorization: Requires authorisation, and 'get:drinks-detail' permission.
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drink_details(jwt):
    # Get all the drinks
    drinks = Drink.query.all()
    drinks_long = []

    # Checks whether there are drinks in the database
    if drinks:
        # Create a list with the drinks' long recipes
        for drink in drinks:
            drinks_long.append(drink.long())
    else:
        abort(404)

    # Return the list
    return jsonify({
                    'success': True,
                    'drinks': drinks_long
    })


# Endpoint: POST /drinks
# Description: Adds a new drink to the database from the supplied data.
# Parameters: jwt - JSON Web Token.
# Authorization: Requires authorisation, and 'post:drinks' permission.
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_new_drink(jwt):
    # Get the drink details from the request
    drink_details = json.loads(request.data)
    drink_return = []
    all_drinks = Drink.query.all()

    # If the drink name already exists in the database, abort
    for drink in all_drinks:
        if(drink.title == drink_details['title']):
            abort(409)

    drink = Drink(title=drink_details['title'],
                  recipe=json.dumps(drink_details['recipe']))

    # Try to add the drink to the database
    try:
        drink.insert()
        drink_return.append(drink.long())
    # In case of an error, abort with status code 500
    except Exception as e:
        print(sys.exc_info())
        abort(500)

    return jsonify({
                    'success': True,
                    'drinks': drink_return
    })


# Endpoint: PATCH /drinks/<drink_id>
# Description: Edits the selected drink with the supplied data and updates the
#              appropriate database row.
# Parameters: drink_id (Integer).
#             jwt - JSON Web Token.
# Authorization: Requires authorisation, and 'patch:drinks' permission.
@app.route('/drinks/<drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(jwt, drink_id):
    updated_drink = json.loads(request.data)
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    drink_return = []

    # If the drink doesn't exist in the database, abort with a 404 error
    if(drink is None):
        abort(404)

    if('title' in updated_drink):
        # If the drink's name has changed, update the drink's name
        if(drink.title != updated_drink['title']):
            drink.title = updated_drink['title']

    # If the user included a new recipe
    if('recipe' in updated_drink):
        # Gets the new and old recipes
        drink_recipe = literal_eval(drink.recipe)
        updated_recipe = updated_drink['recipe']

        # Checks whether one of the recipes is longer than the other. If it is,
        # it means the user either added or deleted ingredients, so the number
        # of ingredients needs to be updated.
        if(len(drink_recipe) > len(updated_recipe)):
            del drink_recipe[len(updated_recipe):len(drink_recipe)]
        # If the new recipe is longer, gets the difference between the new
        # recipe and the old one and adds placeholders for the new ingredients.
        # The new ingredients are then added in the update loop below.
        elif(len(drink_recipe) < len(updated_recipe)):
            difference = len(updated_recipe) - len(drink_recipe)
            for i in range(difference):
                drink_recipe.append({
                                    'name': 'name',
                                    'color': 'color',
                                    'parts': 1
                                    })

        # Updates the recipe according to the new recipe
        for i in range(len(drink_recipe)):
            drink_recipe[i]['name'] = updated_recipe[i]['name']
            drink_recipe[i]['color'] = updated_recipe[i]['color']
            drink_recipe[i]['parts'] = updated_recipe[i]['parts']

        # Replaces the recipe with the new recipe
        drink.recipe = str(drink_recipe)

    # Try to update the recipe in the database
    try:
        drink.update()
        drink_return.append(drink.long())
    # If there's an error, abort
    except Exception as e:
        abort(500)

    return jsonify({
                    'success': True,
                    'drinks': drink_return
    })


# Endpoint: DELETE /drinks/<drink_id>
# Description: Deletes the selected drink from the drinks database.
# Parameters: drink_id (Integer).
#             jwt - JSON Web Token.
# Authorization: Requires authorisation, and 'delete:drinks' permission.
@app.route('/drinks/<drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, drink_id):
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

    # If there's no drink with that ID
    if(drink is None):
        abort(404)

    # Try to delete the drink from the database
    try:
        drink.delete()
    # If there's an error, abort
    except Exception as e:
        abort(500)

    return jsonify({
                    'success': True,
                    'delete': drink_id
    })


# Error Handling
# ---------------------------------------------------------------------------#
# Error handler for Bad Request (400) error.
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
                    'success': False,
                    'error': 400,
                    'message': 'Bad request. Check your request format.'
                    }), 400


# Error handler for Not Found (404) error.
@app.errorhandler(404)
def not_found(error):
    return jsonify({
                    'success': False,
                    'error': 404,
                    'message': 'The resource you asked for was not found.'
                    }), 404


# Error handler for Method Not Allowed (405) error.
@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
                    'success': False,
                    'error': 405,
                    'message': 'Method not allowed.'
                    }), 405


# Error handler for Conflict (409) error.
@app.errorhandler(409)
def conflict(error):
    return jsonify({
                    'success': False,
                    'error': 409,
                    'message': 'Conflict. The resource you were trying to\
                                create already exists.'
                    }), 409


# Error handler for Unprocessable (422) error.
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False,
                    "error": 422,
                    "message": "unprocessable"
                    }), 422


# Error handler for Internal Server Error (500).
@app.errorhandler(500)
def internal_server(error):
    return jsonify({
                    'success': False,
                    'error': 500,
                    'message': 'An internal server error occurred.'
                    }), 500


# Error handler for authentication error.
@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
                    'success': False,
                    'error': error.status_code,
                    'message': error.error['description']
                    }), error.status_code
