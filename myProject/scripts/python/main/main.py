import json
import boto3
import io
from io import BytesIO
import sys
import re
import os
from botocore.exceptions import ClientError
import logging
import math
import time


client = boto3.client('textract')
sqs = boto3.client('sqs')
sns = boto3.client('sns')
client_lambda = boto3.client('lambda')


def get_kv_relationship(key_map, value_map, block_map):
    kvs = {}
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key = get_text(key_block, block_map)
        val = get_text(value_block, block_map)
        kvs[key] = val
    return kvs


def find_value_block(key_block, value_map):
    for relationship in key_block['Relationships']:
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                value_block = value_map[value_id]
    return value_block


def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] == 'SELECTED':
                            text += 'X '    

                                
    return text
    
def search_value(kvs, search_key):
    for key, value in kvs.items():
        if re.search(search_key, key, re.IGNORECASE):
            return value
            
            


def lambda_handler(event, context):
    
    roleArn = "arn:aws:iam::719767148974:role/service-role/myFunction2-role-0w9hfb77"
    bucket = "amazontextractbucket"
    document = event['filename']
    # s3 = boto3.client("s3") # example client, could be any
    regionName = "eu-central-1"
    bpass_keywords = ["to", "from", "departure", "arrival"]
   
    format = document.split('.', 1)[1].lower()
    
    if format == 'pdf':
        if 'first' in event:
            input = {
                "filename" : document,
                "regionName" : regionName,
                "bucket": bucket,
                "roleArn": roleArn,
                "first" : True
            }
            asyncFirstCall = client_lambda.invoke(
                FunctionName = "arn:aws:lambda:eu-central-1:719767148974:function:asyncAnalysis",
                InvocationType = "RequestResponse",
                Payload = json.dumps(input)
            )
            payloadAsync = json.load(asyncFirstCall['Payload'])
            jobId = payloadAsync["jobId"]
            queueUrl = payloadAsync["queueUrl"]
            topicArn = payloadAsync["topicArn"]
            if jobId != None:
                return {
                    "statusCode" : 200,
                    "jobId" : jobId,
                    "queueUrl": queueUrl,
                    "topicArn" : topicArn
                }
            else:
                return {
                    "statusCode" : 400,
                    "jobId" : jobId,
                    "queueUrl": queueUrl,
                    "topicArn" : topicArn
                }
                
        else:
            if 'jobId' in event:
                input = {
                    "filename" : document,
                    "regionName" : regionName,
                    "bucket": bucket,
                    "roleArn": roleArn,
                    "jobId" : event["jobId"],
                    "queueUrl" : event["queueUrl"],
                    "topicArn" : event["topicArn"]
                }
                
                asyncResponse = client_lambda.invoke(
                    FunctionName = "arn:aws:lambda:eu-central-1:719767148974:function:asyncAnalysis",
                    InvocationType = "RequestResponse",
                    Payload = json.dumps(input)
                    )
                payloadAsync = json.load(asyncResponse['Payload'])
                print("async resp " + json.dumps(payloadAsync))
                textList = payloadAsync["body"]
                body = ""
                for i in textList:
                    body += i
                    body += " "
    # format image
    else:
        print("This is image")
        response = client.analyze_document(
            Document={'S3Object': {'Bucket': bucket, 'Name': document}},
            FeatureTypes=["FORMS"])
        print(response)
        #Get the text blocks
        blocks=response['Blocks']
        key_map = {}
        value_map = {}
        block_map = {}
        for block in blocks:
            block_id = block['Id']
            block_map[block_id] = block
            if block['BlockType'] == "KEY_VALUE_SET":
                if 'KEY' in block['EntityTypes']:
                    key_map[block_id] = block
                else:
                    value_map[block_id] = block
        kvs = get_kv_relationship(key_map, value_map, block_map)
        print(kvs)
        print(len(kvs))
        list_keys = list(kvs.keys())
        list_keys_str = ""
        for i in list_keys:
            list_keys_str += i
            list_keys_str += "@@@ "
        translate = boto3.client(service_name='translate', region_name='eu-central-1', use_ssl=True)
        if len(list_keys_str) > 1:
            result = translate.translate_text(Text=list_keys_str, SourceLanguageCode="auto" , TargetLanguageCode="en")
            translated_body = str(result.get('TranslatedText')).split("@@@")
            print(len(translated_body))
            
            words_found = []
            for j in range(0, len(translated_body)):
                for i in range(0, len(bpass_keywords)):
                    if bpass_keywords[i].lower() in translated_body[j].lower():
                        if j not in words_found:
                            words_found.append(j)
            locations = []
            list_kvs = list(kvs.values())
            for i in words_found:
                locations.append(list_kvs[i])
            print(locations)
            
            if len(locations) == 2 and len(locations[0]) > 0 and len(locations[1]) > 0:
                input = {
                    "point1" : locations[0],
                    "point2" : locations[1]
                }
                print(input)
                #calculate distance
                distance_response = client_lambda.invoke(
                    FunctionName= "arn:aws:lambda:eu-central-1:719767148974:function:findDistance",
                    InvocationType = "RequestResponse",
                    Payload = json.dumps(input)
                    )
                res_dist = json.load(distance_response['Payload'])
                print(res_dist)
                if res_dist['statusCode'] == 200:
                    return {
                        'statusCode': 200,
                        'body': json.dumps(res_dist)
                    }
        #     else:
        response = client.detect_document_text(
                Document={'S3Object': {'Bucket': bucket, 'Name': document}})
        blocks=response['Blocks']
        body = ""
        for item in blocks:
            if item["BlockType"] == "LINE":
                body += item["Text"]
                body += " "
        
    # # calling lambda to find distance
    input = {
        "text" : body,
    }
    print("second call")
    print(input)
    distance_response = client_lambda.invoke(
        FunctionName= "arn:aws:lambda:eu-central-1:719767148974:function:findDistance",
        InvocationType = "RequestResponse",
        Payload = json.dumps(input)
    )
    second_res = json.load(distance_response["Payload"])
    
    
    
    if second_res['statusCode'] == 200:
        return {
            'statusCode': 200,
            'body': json.dumps(second_res)
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps(second_res)
        }
    
    