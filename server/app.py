#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource
from werkzeug.exceptions import NotFound
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

class Restaurants(Resource):
    def get(self):
        try:
            return [restaurant.to_dict(only=("id", "name", "address")) for restaurant in Restaurant.query], 200
        except Exception as e: 
            return {"error": str(e)}, 400

api.add_resource(Restaurants, "/restaurants")

class RestaurantsById(Resource):
    def get(self, id):
        try:
            restaurant = db.session.get(Restaurant, id) #2.0 SQLAlchemy
            if not restaurant:
                return make_response({"error": "Restaurant not found"}, 404)
            return restaurant.to_dict(), 200
        except Exception as e:
            return {"error": str(e)}, 500
        
    def delete(self, id):
        try:
            restaurant = Restaurant.query.get_or_404(id, "Restaurant not found")
            db.session.delete(restaurant)
            db.session.commit()
            return "", 204
        except NotFound as e:
            return {"error": str(e)}, 404
        except Exception as e:
            return {"error": str(e)}, 404

api.add_resource(RestaurantsById, "/restaurants/<int:id>")

class Pizzas(Resource):
    def get(self):
        try:
            return [pizza.to_dict() for pizza in Pizza.query], 200
        except Exception as e:
            return {"error": str(e)}, 400

api.add_resource(Pizzas, "/pizzas")

class RestaurantPizzas(Resource):
    def post(self):
        data = request.get_json()
        pizza_id = data.get("pizza_id")
        restaurant_id = data.get("restaurant_id")
        price = data.get("price")

        if not pizza_id or not restaurant_id or price is None:
            return{"errors": ["Validation errors"]}, 400
        pizza = Pizza.query.get(pizza_id)
        restaurant = Restaurant.query.get(restaurant_id)

        if not pizza or not restaurant:
            return {"errors": ["Pizza or Restaurant not found"]}, 400
        
        try:
            new_record = RestaurantPizza(
                pizza_id=pizza_id,
                restaurant_id=restaurant_id,
                price=price
            )
            db.session.add(new_record)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return{"errors": ['validation errors']}, 400
        
        response_dict = {
            "id": new_record.id,
            "pizza": {
                "id": pizza.id,
                "ingredients": pizza.ingredients,
                "name": pizza.name
            },
            "pizza_id": new_record.pizza_id,
            "price": new_record.price,
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address
            },
            "restaurant_id": new_record.restaurant_id
        }

        response = make_response(response_dict, 201)
        return response

api.add_resource(RestaurantPizzas, "/restaurant_pizzas")

if __name__ == "__main__":
    app.run(port=5555, debug=True)
