import json
import boto3

def lambda_handler(event, context):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(event['bucket'])
    objToDelete = event['object']
    result = bucket.object_versions.filter(Prefix=objToDelete).delete()
    if len(result) > 0:
        statusCode = result[0]['ResponseMetadata']['HTTPStatusCode']
        message = "Successfully deleted objects"
        return {
            "statusCode" : statusCode,
            "message" : message
        }
    print(result)
    return {
        "statusCode" : 200,
        "message": "No objects to delete were found"
    }

