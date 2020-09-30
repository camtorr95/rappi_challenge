# Rappi Challenge

Given the specifications, this repository contains a docker proyect, in which the developed API is exposed. Additionally, there's a notebook with details on the training of the model.

## Installation

#### This proyect runs on docker

First download the proyect

```bash
git clone https://github.com/camtorr95/rappi_challenge
```

You'll notice there are 2 main folders: **api** and **notebook**.

### Notebook
On the **notebook** folder there's a filed called


```bash
cd notebook
rappi_challenge.ipynb
```

This is a python notebook with all the details associated to the training of the model, which are then saved as a pickle file.

### Api

The **api** folder contains a docker-compose.yaml file, a pre-trained model, python source files for the specified API and some docker configuration files.

```bash
cd api
```

Once we're in the **api** folder we can see there's a docker-compose.yaml file. We can now start the app and it's containers with the following command.

```bash
docker-compose up -d
```

Now you can make requests to the api locally.

## REST Api

```url
GET http://localhost:5000/orders
```
This will return all orders that have been predicted by this Api. The json output structure looks like this.

```json
{
    "orders": [
        {
            "created_at": "Thu, 07 Sep 2017 20:02:17 GMT",
            "last_predicted_at": "Wed, 30 Sep 2020 06:30:19 GMT",
            "order_id": 14364873,
            "store_id": "30000009",
            "taken": 0,
            "to_user_distance": 2.4781006757058885,
            "to_user_elevation": -72.71936035156295,
            "total_earning": 4200
        }
    ],
    "taken_rate": {
        "0": 1.0,
        "1": 0.0
    },
    "total_orders": 1
}
```


```url
GET http://localhost:5000/orders/<order_id>
```
This will return the order matching <order_id> if it has already been processed, or an error message of not found. This is what the output looks like.

```json
{
    "order": {
        "created_at": "Thu, 07 Sep 2017 20:02:17 GMT",
        "last_predicted_at": "Wed, 30 Sep 2020 06:30:19 GMT",
        "order_id": 14364873,
        "store_id": 30000009,
        "taken": 0,
        "to_user_distance": 2.4781006757058885,
        "to_user_elevation": -72.71936035156295,
        "total_earning": 4200.0
    }
}
```


```url
POST http://localhost:5000/orders/predict
```
This will recieve either a single order with the following structure

```json
{
    "created_at": "2017-09-07T20:07:23Z",
    "order_id": 14364879,
    "store_id": 30000009,
    "to_user_distance": 2.4781006757058885,
    "to_user_elevation": -72.71936035156295,
    "total_earning": 4200.0
}
```

Or a list of orders like this.

```json
{
    "orders": [
        {
            "order_id": 14364873,
            "store_id": 30000009,
            "to_user_distance": 2.4781006757058885,
            "to_user_elevation": -72.71936035156295,
            "total_earning": 4200,
            "created_at": "2017-09-07T20:02:17Z"
        },
        {
            "order_id": 14364874,
            "store_id": 30000009,
            "to_user_distance": 2.4781006757058885,
            "to_user_elevation": -72.71936035156295,
            "total_earning": 4200,
            "created_at": "2017-09-07T20:02:17Z",
        },
        {
            "order_id": 14368573,
            "store_id": 900013508,
            "to_user_distance": 0.5629625762571852,
            "to_user_elevation": -21.301147460937955,
            "total_earning": 5200,
            "created_at": "2017-09-07T20:17:17Z"
        }
    ]
}
```

Notice that *created_at* is formatted in a specific way **YYYY-MM-DD'T'HH:MM:SS'Z'**.

Doesn't matter how you send the request, the output will always look like this.

```json
{
    "predictions": [
        {
            "created_at": "Thu, 07 Sep 2017 20:02:17 GMT",
            "order_id": 14364873,
            "store_id": "30000009",
            "taken": 0,
            "to_user_distance": 2.4781006757058885,
            "to_user_elevation": -72.71936035156295,
            "total_earning": 4200
        },
        {
            "created_at": "Thu, 07 Sep 2017 20:02:17 GMT",
            "order_id": 14364874,
            "store_id": "30000009",
            "taken": 0,
            "to_user_distance": 2.4781006757058885,
            "to_user_elevation": -72.71936035156295,
            "total_earning": 4200
        },
        {
            "created_at": "Thu, 07 Sep 2017 20:17:17 GMT",
            "order_id": 14368573,
            "store_id": "900013508",
            "taken": 1,
            "to_user_distance": 0.5629625762571852,
            "to_user_elevation": -21.301147460937955,
            "total_earning": 5200
        }
    ],
    "taken_rate": {
        "0": 0.6666666666666667,
        "1": 0.3333333333333333
    },
    "total_predictions": 3
}
```