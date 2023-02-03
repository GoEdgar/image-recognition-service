import json
import logging
import os

import boto3

BLOB_TABLE_NAME = os.getenv("BLOB_TABLE_NAME")

dynamodb_client = boto3.client("dynamodb")
rekognition_client = boto3.client("rekognition", region_name="eu-west-1")

log = logging.getLogger()
log.setLevel(logging.INFO)


def lambda_handler(event, _):
    # load image info from event
    s3_object = event['Records'][0]['s3']
    blob_bucket = s3_object["bucket"]["name"]
    blob_key = s3_object['object']['key']
    log.info(f"Received {blob_key} object in {blob_bucket} bucket")

    # extract labels via AWS Rekognition
    response = rekognition_client.detect_labels(
        Image={
            "S3Object": {
                "Bucket": blob_bucket,
                "Name": blob_key
                }
            },
        MaxLabels=20)
    log.info("The blob has been processed")

    labels = response["Labels"]

    # save lables info into DynamoDB
    response = dynamodb_client.update_item(
        TableName=BLOB_TABLE_NAME,
        Key={"BlobId": {"S": blob_key}},
        AttributeUpdates={
            "Labels": {
                "Action": "PUT",
                "Value": {
                    "S": json.dumps(labels)
                    }
                }
            }
        )

    db_status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    log.info(f"Result was placed with {db_status_code} status code. {response}")
