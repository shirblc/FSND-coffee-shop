import os
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
# db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}
    where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.all()
    drinks_short_format = []

    # Checks whether there are drinks in the database
    if drinks:
        # Gets each drink's short data representation
        for drink in drinks:
            drinks_short_format[drink.id] = drink.short()
    else:
        drinks_short_format.append({
                                    'name': 'There are no drinks at the moment!'
                                    })

    return jsonify({
                    'success': True,
                    'drinks': drinks_short_format
    })


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where
    drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drink_details():
    # Get all the drinks
    drinks = Drink. query.all()
    drinks_long = []

    # Create a list with the drinks' long recipes
    for drink in drinks:
        drinks_long.append(drink.long())

    # Return the list
    return jsonify({
                    'success': True,
                    'drinks': drinks_long
    })


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where
    drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_new_drink():
    # Get the drink details from the request
    drink_details = json.loads(request.data)['drink']
    drink_return = []

    # Try to add the drink to the database
    try:
        drink = Drink(title=drink_details['title'],
                      recipe=str(drink_details['recipe']))
        drink.insert()
        drink_return.append(drink.long())
    # In case of an error, abort with status code 500
    except Exception as e:
        abort(500)

    return jsonify({
                    'success': True,
                    'drinks': drink_return
    })


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where
    drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(drink_id):
    updated_drink = json.loads(request.data)['drink']
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    drink_return = []

    # If the drink doesn't exist in the database, abort with a 404 error
    if(drink is None):
        abort(404)

    # If the drink's name has changed, update the drink's name
    if(drink.title != updated_drink['title']):
        drink.title = updated_drink['title']

    # Gets the new and old recipes
    drink_recipe = literal_eval(drink.recipe)
    updated_recipe = updated_drink['recipe']

    # Checks whether one of the recipes is longer than the other. If it is,
    # it means the user either added or deleted ingredients, so the number
    # of ingredients needs to be updated.
    if(len(drink_recipe) > len(updated_recipe)):
        del drink_recipe[len(updated_recipe):len(drink_recipe)]
    # If the new recipe is longer, gets the difference between the new recipe
    # and the old one and adds placeholders for the new ingredients. The new
    # ingredients are then added in the update loop below.
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


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id
    is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(drink_id):
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
# Error handler for Not Found (404) error.
@app.errorhandler(404)
def not_found(error):
    return jsonify({
                    'success': False,
                    'error': 404,
                    'message': 'The resource you asked for was not found.'
                    }), 404


'''
Example error handling for unprocessable entity
'''
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


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
