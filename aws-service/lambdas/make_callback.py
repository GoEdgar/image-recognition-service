import json

import requests


def lambda_handler(event, _):
    # extracting attrs from DynamoDB event
    item = event["Records"][0]["dynamodb"]
    item_attrs = item["OldImage"] | item["NewImage"]

    blob_id = item_attrs["BlobId"]["S"]
    recognition_labels = item_attrs["Labels"]["S"]
    callback_url = item_attrs["CallbackUrl"]["S"]

    # preparing payload for client webhook notification
    notification_data = {"blob_id": blob_id,
                         "labels": json.loads(recognition_labels)}
    response = requests.post(callback_url, json=notification_data)

    if response.status_code != 200:
        # TODO
        raise

    return "ok"
