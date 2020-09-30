import service as srv

from flask import Flask
from flask.globals import request

app = Flask(__name__)


def handle_bad_request(m):
    # encapsulates bad request response
    return {"error": f"bad request: {m}"}, 400


@app.route("/orders/predict", methods=["POST"])
def orders_predict():
    body = request.get_json(force=False)
    if body is None:
        return handle_bad_request("post request must contain a body")

    if "orders" in body:
        orders = body["orders"]

        # This segment guarantees that every order on the list complies
        # with the dataset structure that was used to train the model
        syntax_check = True
        error_order = None
        for order_req in orders:
            syntax_check = syntax_check and all(
                feature in order_req for feature in srv.get_order_description())
            if (not syntax_check):
                error_order = order_req
                break

        if(syntax_check):
            predictions = srv.predict(orders)
            return predictions, 201
        else:
            return handle_bad_request(f'all your orders must have the following attributes: {str(srv.get_order_description())}, please check the following entry {error_order}')

    # checks if theres a single order object in the request body
    # or if it's empty. Additionaly, it guarantees the data entry
    # has the correct structure
    else:
        if all(feature in body for feature in srv.get_order_description()):
            wrap = [body]
            predictions = srv.predict(wrap)
            return predictions, 201
        else:
            if (bool(body)):
                return handle_bad_request(f'your order must have the following attributes: {str(srv.get_order_description())}, this is what you sent: {body}')
            else:
                return handle_bad_request("body must contain an order or a list of orders")


@app.route("/orders", methods=["GET"])
@app.route("/orders/<order_id>", methods=["GET"])
def orders(order_id=None):
    # logic for both all orders, and order by id
    if order_id is not None:
        try:
            # checks if order_id is an integer
            temp = 0
            temp += int(order_id)
            order = srv.get_order(temp)
            if (order["order"] is None):
                return {"error": f"order {order_id} not found"}, 404
            else:
                return order, 200
        except (TypeError, ValueError) as e:
            return handle_bad_request("order id must be an integer")
    else:
        return srv.get_orders(), 200


if __name__ == "__main__":
    srv.start_service.conn = False
    srv.start_service()

    app.run(host='0.0.0.0')
