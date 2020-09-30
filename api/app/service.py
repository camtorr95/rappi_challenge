import numpy as np
import pandas as pd
import datetime as dt
import mysql.connector
import functools

import json
import pickle
import math

from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression


class OrderDAO:
    '''
    Order DAO
    This class encapsulates all sql logic associated with orders.
    The db is an example db from mysql.
    '''

    def __init__(self, database='example', host="db", user="root", password_file=None):
        pf = open(password_file, 'r')
        self.connection = mysql.connector.connect(
            user=user,
            password=pf.read(),
            host=host,
            database=database,
            auth_plugin='mysql_native_password'
        )
        pf.close()

    def initialize_db(self):
        cursor = self.connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS order_table')
        cursor.execute(
            'CREATE TABLE order_table (order_id INT PRIMARY KEY, ' +
            'store_id INT, to_user_distance DOUBLE, to_user_elevation DOUBLE, ' +
            'total_earning FLOAT, created_at DATETIME, ' +
            'last_predicted_at DATETIME DEFAULT NOW(), taken BOOL)')
        cursor.close()
        self.connection.commit()

    def get_order(self, order_id=None):
        if order_id is None:
            return None

        cursor = self.connection.cursor()
        cursor.execute(
            f'SELECT * FROM order_table WHERE order_id = {order_id}')

        record = cursor.fetchone()
        order = None

        if record is not None:
            order = {"order_id": record[0],
                     "store_id": record[1],
                     "to_user_distance": record[2],
                     "to_user_elevation": record[3],
                     "total_earning": record[4],
                     "created_at": record[5],
                     "last_predicted_at": record[6],
                     "taken": record[7]}

        cursor.close()
        return order

    def get_all_orders(self):
        records = []
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM order_table')

        for record in cursor.fetchall():
            order = {"order_id": record[0],
                     "store_id": record[1],
                     "to_user_distance": record[2],
                     "to_user_elevation": record[3],
                     "total_earning": record[4],
                     "created_at": record[5],
                     "last_predicted_at": record[6],
                     "taken": record[7]}
            records.append(order)

        cursor.close()
        return records

    def insert_orders(self, orders):
        cursor = self.connection.cursor()
        # insert query with update on duplicate key
        cursor.executemany('INSERT INTO order_table (order_id, store_id, ' +
                           'to_user_distance, to_user_elevation, ' +
                           'total_earning, created_at, taken) ' +
                           'VALUES (%s, %s, %s, %s, %s, %s, %s) ' +
                           'ON DUPLICATE KEY UPDATE ' +
                           'order_id = VALUES(order_id), ' +
                           'store_id = VALUES(store_id), ' +
                           'to_user_distance = VALUES(to_user_distance), ' +
                           'to_user_elevation = VALUES(to_user_elevation), ' +
                           'total_earning = VALUES(total_earning), ' +
                           'created_at = VALUES(created_at), ' +
                           'last_predicted_at = NOW(), ' +
                           'taken = VALUES(taken)', [
                               (order["order_id"], order["store_id"],
                                order["to_user_distance"], order["to_user_elevation"],
                                order["total_earning"], order["created_at"].strftime(
                                    "%Y-%m-%d %H:%M:%S"),
                                order["taken"]) for order in orders])
        cursor.close()
        self.connection.commit()


def start_service():
    # initializes the db and creates all needed tables on boot.
    # start_service.conn acts as an static variable
    if (not start_service.conn):
        conn = OrderDAO(
            password_file="/run/secrets/db-password")
        conn.initialize_db()
        start_service.conn = True

    return OrderDAO(
        password_file="/run/secrets/db-password")


# prepares ids for the model
def prepare_ids(data, end):
    n_data = data
    n_data["store_id"] = data["store_id"].apply(lambda x: str(x)[0: end])
    n_data = n_data.drop("order_id", axis=1)

    return n_data


# extracts all features from the date field
def prepare_created_at(data):
    n_data = data

    _datetime = n_data["created_at"].apply(
        lambda x: dt.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ'))

    # creates variables which encode the different values of the datetime
    # and the cyclic nature of the sequences of numbers found in datetime fields
    # for example, 0h comes after 23h, and so on

    xmes = _datetime.dt.month.apply(lambda x: math.sin(2 * math.pi * x / 12))
    ymes = _datetime.dt.month.apply(lambda x: math.cos(2 * math.pi * x / 12))

    avg_days_year = 365.2425

    xdia = _datetime.dt.dayofyear.apply(
        lambda x: math.sin(2 * math.pi * x / avg_days_year))
    ydia = _datetime.dt.dayofyear.apply(
        lambda x: math.cos(2 * math.pi * x / avg_days_year))

    xsem = _datetime.dt.dayofweek.apply(
        lambda x: math.sin(2 * math.pi * x / 7))
    ysem = _datetime.dt.dayofweek.apply(
        lambda x: math.cos(2 * math.pi * x / 7))

    xhora = _datetime.dt.hour.apply(lambda x: math.sin(2 * math.pi * x / 24))
    yhora = _datetime.dt.hour.apply(lambda x: math.cos(2 * math.pi * x / 24))

    xmin = _datetime.dt.minute.apply(lambda x: math.sin(2 * math.pi * x / 60))
    ymin = _datetime.dt.minute.apply(lambda x: math.cos(2 * math.pi * x / 60))

    n_columns = pd.concat([xmes, ymes, xdia, ydia, xsem,
                           ysem, xhora, yhora, xmin, ymin], axis=1)
    n_columns.columns = ["xmes", "ymes", "xdia", "ydia",
                         "xsem", "ysem", "xhora", "yhora", "xmin", "ymin"]

    n_data = n_data.drop("created_at", axis=1)
    n_data = pd.concat([n_data, n_columns], axis=1)

    return n_data


def prepare_eval(dataset):
    # prepares the dataset with preprocessing tecniques
    ohencoder = pickle.load(open("_encoder.pkl", "rb"))
    stdscaler = pickle.load(open("_scaler.pkl", "rb"))

    store_id_limit = 10
    prep_id = prepare_ids(dataset, store_id_limit)
    dataset = prepare_created_at(prep_id)

    base_encode = dataset["store_id"]
    base_scale = dataset.drop("store_id", axis=1)

    x_eval_ohe = ohencoder.transform(base_encode.values.reshape(-1, 1))
    x_eval_std = stdscaler.transform(base_scale)

    x_eval = pd.DataFrame(np.concatenate([x_eval_ohe, x_eval_std], axis=1))

    return x_eval


def predict(orders_list):
    conn = start_service()

    # extract only the features needed
    def order_build(order):
        n_order = {
            "order_id": order["order_id"],
            "store_id": order["store_id"],
            "to_user_distance": order["to_user_distance"],
            "to_user_elevation": order["to_user_elevation"],
            "total_earning": order["total_earning"],
            "created_at": order["created_at"],
        }
        return n_order

    orders = map(order_build, orders_list)
    orders = pd.DataFrame(orders)

    # prepares the dataset and builds a dataframe
    x_eval = prepare_eval(orders)
    model = pickle.load(open("_log_reg.pkl", "rb"))
    prediction = model.predict(x_eval)
    prediction = pd.Series(prediction, name="taken")

    # format the response
    response = pd.concat([orders, prediction], axis=1)
    response["created_at"] = response["created_at"].apply(
        lambda x: dt.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ'))

    taken_rate = 0 if 1 not in response["taken"] else response["taken"].value_counts(
        normalize=True)[1]
    response = response.to_dict('records')
    conn.insert_orders(response)

    predictions = {"predictions": response, "total_predictions": len(response), "taken_rate": {
        0: (1 - taken_rate) if len(response) > 0 else 0.0, 1: taken_rate}}

    return predictions


def get_order_description():
    return ["order_id", "store_id", "to_user_distance", "to_user_elevation", "total_earning", "created_at"]


def get_order(order_id):
    conn = start_service()
    order = {"order": conn.get_order(order_id)}
    return order


def get_orders():
    conn = start_service()
    _orders = conn.get_all_orders()

    taken_rate = 0
    for order in _orders:
        taken_rate += order["taken"]
    taken_rate /= (len(_orders) if len(_orders) > 0 else 1)
    orders = {"orders": _orders, "total_orders": len(_orders), "taken_rate": {
        0: (1 - taken_rate) if len(_orders) > 0 else 0.0, 1: taken_rate}}

    return orders
