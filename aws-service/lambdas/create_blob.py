import json
import os
from urllib.parse import urlparse
from uuid import uuid4

import boto3

BUCKET_NAME = os.getenv("BLOB_BUCKET_NAME")
BLOB_TABLE_NAME = os.getenv("BLOB_TABLE_NAME")
BUCKET_PUT_OBJECT_ROLE = os.getenv("BUCKET_PUT_OBJECT_ROLE")

sts_client = boto3.client("sts")
dynamodb_client = boto3.client("dynamodb")


def lambda_handler(event, _):
    # validation
    if event["body"] is None:
        return {"statusCode": 400, "body": "Body is empty"}

    body = json.loads(event["body"])
    callback_url = body.get("callback_url", "")

    parsed_url = urlparse(callback_url)
    is_valid_url = all((parsed_url.scheme, parsed_url.netloc))

    if not is_valid_url:
        return {"statusCode": 400, "body": "Callback url isn't valid"}

    # create S3 presign URL
    blob_id = str(uuid4())

    # Since Lambda Execution Role will expire
    # after Lambda return the blob url
    # we need to generate presigned url
    # via another long-live role with PutObject access
    response = sts_client.assume_role(RoleArn=BUCKET_PUT_OBJECT_ROLE,
                                      RoleSessionName=blob_id)
    put_role_creds = response["Credentials"]
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=put_role_creds["AccessKeyId"],
        aws_secret_access_key=put_role_creds["SecretAccessKey"],
        aws_session_token=put_role_creds["SessionToken"]
        )
    url = s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={'Bucket': BUCKET_NAME, 'Key': blob_id},
        ExpiresIn=3600
        )

    # save blob_id and callback_url to DynamoDB
    dynamodb_client.put_item(
        TableName=BLOB_TABLE_NAME,
        Item={
            "BlobId": {"S": blob_id},
            "CallbackUrl": {"S": callback_url}
            },
        )

    # return blob_id, callback_url and upload_url
    response = {"blob_id": blob_id,
                "callback_url": callback_url,
                "upload_url": url}

    return {"statusCode": 201, "body": json.dumps(response)}
