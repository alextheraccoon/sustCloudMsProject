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
            
            
def GetResultsDocumentDetection(jobId):
    maxResults = 1000
    paginationToken = None
    finished = False
    allBlocks = []
    
    while finished == False:
        response = None
        
        if paginationToken == None:
            response = client.get_document_text_detection(JobId=jobId,
                                                                         MaxResults=maxResults)
        else:
            response = client.get_document_text_detection(JobId=jobId,
                                                                 MaxResults=maxResults,
                                                                 NextToken=paginationToken)
        # print(response)
    # pages = []
    # response = client.get_document_text_detection(JobId=jobId)
    # pages.append(response)
    # print("Resultset page recieved: {}".format(len(pages)))
    # nextToken = None
    # if('NextToken' in response):
    #     nextToken = response['NextToken']
    # while(nextToken):
    #     response = client.get_document_text_detection(JobId=jobId, NextToken=nextToken)
    #     pages.append(response)
    #     print("Resultset page recieved: {}".format(len(pages)))
    #     nextToken = None
    #     if('NextToken' in response):
    #         nextToken = response['NextToken']
    # # body = ""
    # for resultPage in pages:
    #     print(resultPage['Blocks'])
    #     for item in resultPage['Blocks']:
        #     allBlocks.append(item)
        #     if 'Text' in item:
        #         body += item['Text']
        #         body += " "
    # print(body)
        # Get the text blocks
        blocks = response['Blocks']
        print('Detected Document Text')
        print('Pages: {}'.format(response['DocumentMetadata']['Pages']))
        
        for block in blocks:
            # print(block)
            allBlocks.append(block)
            # print("Type: " + block['BlockType'])
            # print('Page: {}'.format(block['Page']))
            # if 'Text' in block and block['BlockType'] == "LINE":
            # #     print("Text: " + block['Text'])
            #     allBlocks.append(block['Text'])
            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True
                
        # body = ""
        # for item in response['Blocks']:
        #     if 'Text' in item:
        #         print("Text: " + item['Text'])
        #         body += item["Text"]
        #         body += " "
            
        # allBlocks.append(body)
        # if len(allBlocks) == 0:
        #     allBlocks = response['Blocks']
        # else:
        #     for block in response['Blocks']:
        #         allBlocks.append(block)
        # # print(type(blocks))
        # print('Blocks len' + str(len(allBlocks)))
        
    #     if 'NextToken' in response:
    #         print(response['NextToken'])
    #         paginationToken = response['NextToken']
    #     else:
    #         finished = True
    # for i in allBlocks:
    #     print(i)
    return allBlocks
            
def GetResultsDocumentAnalysis(jobId):
    maxResults = 1000
    paginationToken = None
    finished = False
    allBlocks = []
    while finished == False:

        response = None
        if paginationToken == None:
            response = client.get_document_analysis(JobId=jobId,
                                                           MaxResults=maxResults)
        else:
            response = client.get_document_analysis(JobId=jobId,
                                                           MaxResults=maxResults,
                                                           NextToken=paginationToken)


            # Get the text blocks
        blocks = response['Blocks']
        print('Analyzed Document Text')
        print('Pages: {}'.format(response['DocumentMetadata']['Pages']))
        # Display block information
        for block in blocks:
            allBlocks.append(block)

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True
    return allBlocks


def CreateTopicandQueue():

    millis = str(int(round(time.time() * 1000)))

    # Create SNS topic
    snsTopicName = "AmazonTextractTopic" + millis

    topicResponse = sns.create_topic(Name=snsTopicName)
    snsTopicArn = topicResponse['TopicArn']

    # create SQS queue
    sqsQueueName = "AmazonTextractQueue" + millis
    sqs.create_queue(QueueName=sqsQueueName)
    sqsQueueUrl = sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']

    attribs = sqs.get_queue_attributes(QueueUrl=sqsQueueUrl,
                                            AttributeNames=['QueueArn'])['Attributes']

    sqsQueueArn = attribs['QueueArn']

    # Subscribe SQS queue to SNS topic
    sns.subscribe(
        TopicArn=snsTopicArn,
        Protocol='sqs',
        Endpoint=sqsQueueArn)

    # Authorize SNS to write SQS queue
    policy = """{{
"Version":"2012-10-17",
"Statement":[
{{
    "Sid":"MyPolicy",
    "Effect":"Allow",
    "Principal" : {{"AWS" : "*"}},
    "Action":"SQS:SendMessage",
    "Resource": "{}",
    "Condition":{{
    "ArnEquals":{{
        "aws:SourceArn": "{}"
    }}
    }}
}}
]
}}""".format(sqsQueueArn, snsTopicArn)

    response = sqs.set_queue_attributes(
        QueueUrl=sqsQueueUrl,
        Attributes={
            'Policy': policy
        })
    return sqsQueueUrl, snsTopicArn
    
    
    
def asyncAnalysis(roleArn, document, bucket, first):
    print("asyncAnalysis")
    sqsQueueUrl, snsTopicArn = CreateTopicandQueue()
    print('queue and topic created: \n queueUrl: ' + sqsQueueUrl + '\n topicArn: ' + snsTopicArn)
    try:
        if first == False:
            print("This is second analysis")
            analysis = client.start_document_text_detection(
                DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': document}},
                NotificationChannel={'RoleArn': roleArn, 'SNSTopicArn': snsTopicArn})
            print('Processing type: Detection')
            jobId = analysis['JobId']
        else:
            print("This is first analysis")
            analysis = client.start_document_analysis(
                DocumentLocation={ 
                "S3Object": { 
                    "Bucket": bucket,
                    "Name": document,
                }},
                FeatureTypes=["TABLES", "FORMS"],
                NotificationChannel={
                    'SNSTopicArn': snsTopicArn,
                    'RoleArn': roleArn,               
                })
            jobId = analysis['JobId']
            print(
                    "Started text analysis job" + jobId + ' on document ' + document)
    except ClientError:
            print("Couldn't analyze text in " + document)
            raise
    else:
        print('jobid' + jobId)

    jobFound = False
    dotLine = 0
    while jobFound == False:
        sqsResponse = sqs.receive_message(QueueUrl=sqsQueueUrl, MessageAttributeNames=['ALL'],
                                                MaxNumberOfMessages=10)
        print('sqsResponse: ' + json.dumps(sqsResponse))
        if sqsResponse:

            if 'Messages' not in sqsResponse:
                if dotLine < 40:
                    print('.', end='')
                    dotLine = dotLine + 1
                else:
                    print()
                    dotLine = 0
                sys.stdout.flush()
                time.sleep(1)
                continue

            for message in sqsResponse['Messages']:
                notification = json.loads(message['Body'])
                textMessage = json.loads(notification['Message'])
                print(textMessage['JobId'])
                print(textMessage['Status'])
                if str(textMessage['JobId']) == analysis['JobId']:
                    print('Matching Job Found:' + textMessage['JobId'])
                    jobFound = True
                    if first == True:
                        blocks = GetResultsDocumentAnalysis(textMessage['JobId'])
                    else:
                        blocks = GetResultsDocumentDetection(textMessage['JobId'])
                        for i in blocks:
                            print(i)
                    sqs.delete_message(QueueUrl=sqsQueueUrl,
                                            ReceiptHandle=message['ReceiptHandle'])
                else:
                    print("Job didn't match: " + str(textMessage['JobId']))
                # Delete the unknown message. Consider sending to dead letter queue
                    sqs.delete_message(QueueUrl=sqsQueueUrl,
                                            ReceiptHandle=message['ReceiptHandle'])
    return blocks


def lambda_handler(event, context):
    #TODO create bucket dynamically
    roleArn = "arn:aws:iam::719767148974:role/service-role/myFunction2-role-0w9hfb77"
    bucket = "amazontextractbucket"
    document = event['filename']
    regionName = "eu-central-1"
   
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
        
    else:
        print("This is image")
        response = client.detect_document_text(
                Document={'S3Object': {'Bucket': bucket, 'Name': document}})
        blocks=response['Blocks']
        body = ""
        for item in blocks:
            if item["BlockType"] == "LINE":
                body += item["Text"]
                body += " "
        
    # calling lambda to find distance
    input = {
        "text" : body,
    }
    print(json.dumps(input))
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
        
        
    ######################### key value analysis ######################
    #Get the text blocks
    
    # key_map = {}
    # value_map = {}
    # block_map = {}
    # for block in blocks:
    #     block_id = block['Id']
    #     block_map[block_id] = block
    #     if block['BlockType'] == "KEY_VALUE_SET":
    #         if 'KEY' in block['EntityTypes']:
    #             key_map[block_id] = block
    #         else:
    #             value_map[block_id] = block
    # kvs = get_kv_relationship(key_map, value_map, block_map)
    # print(str(json.dumps(kvs)))
    
    # # input to distance calculator function
    # input = {
    #     "Body" : json.dumps(kvs)
    # }
    
    # #calculate distance
    # distance_response = client_lambda.invoke(
    #     FunctionName= "arn:aws:lambda:eu-central-1:719767148974:function:findDistance",
    #     InvocationType = "RequestResponse",
    #     Payload = json.dumps(input)
    #     )
        
    # res = json.load(distance_response['Payload'])
    # print(res)
    
    # # Case when no airport codes are found
    # if res['statusCode'] == 400:
    #     body = ""
    #     if format == 'pdf':
    #         blocks = asyncAnalysis(roleArn, document, bucket, False)
    #     else:
    #         response = client.detect_document_text(
    #             Document={'S3Object': {'Bucket': bucket, 'Name': document}})
    #         blocks=response['Blocks']
    #     for item in blocks:
    #         if item["BlockType"] == "LINE":
    #             body += item["Text"]
    #             body += " "
    #     print(body)
    #     input = {
    #         "Body" : json.dumps(body)
    #     }
    #     print(input)
    #     distance_response = client_lambda.invoke(
    #         FunctionName= "arn:aws:lambda:eu-central-1:719767148974:function:findDistance",
    #         InvocationType = "RequestResponse",
    #         Payload = json.dumps(input)
    #     )
    #     second_res = json.load(distance_response['Payload'])
    #     print("second res" + json.dumps(second_res))
    #     # if second_res['statusCode'] == 200 and len(second_res['Possible routes']) != 0:
    #     #     print("multiple routes from second analysis")
    #     #     print(second_res['Possible routes'])
    #         # TODO
        
    #     return {
    #         'statusCode': 200,
    #         'body': json.dumps(second_res)
    #     }
        
    # # elif res['statusCode'] == 200 and res['Possible routes'] != []:
    # #     print("multiple routes from first analysis")
    # #     print(res['Possible routes'])
    # else:
    #     return {
    #         'statusCode': 200,
    #         'body': json.dumps(res)
    #     }  
    



    #################################################################################################################################
   #################################################################################################################################
    #################################################################################################################################
     #################################################################################################################################
      #################################################################################################################################

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
            
            
def GetResultsDocumentDetection(jobId):
    maxResults = 1000
    paginationToken = None
    finished = False
    allBlocks = []
    
    while finished == False:
        response = None
        
        if paginationToken == None:
            response = client.get_document_text_detection(JobId=jobId,
                                                                         MaxResults=maxResults)
        else:
            response = client.get_document_text_detection(JobId=jobId,
                                                                 MaxResults=maxResults,
                                                                 NextToken=paginationToken)
        # print(response)
    # pages = []
    # response = client.get_document_text_detection(JobId=jobId)
    # pages.append(response)
    # print("Resultset page recieved: {}".format(len(pages)))
    # nextToken = None
    # if('NextToken' in response):
    #     nextToken = response['NextToken']
    # while(nextToken):
    #     response = client.get_document_text_detection(JobId=jobId, NextToken=nextToken)
    #     pages.append(response)
    #     print("Resultset page recieved: {}".format(len(pages)))
    #     nextToken = None
    #     if('NextToken' in response):
    #         nextToken = response['NextToken']
    # # body = ""
    # for resultPage in pages:
    #     print(resultPage['Blocks'])
    #     for item in resultPage['Blocks']:
        #     allBlocks.append(item)
        #     if 'Text' in item:
        #         body += item['Text']
        #         body += " "
    # print(body)
        # Get the text blocks
        blocks = response['Blocks']
        print('Detected Document Text')
        print('Pages: {}'.format(response['DocumentMetadata']['Pages']))
        
        for block in blocks:
            # print(block)
            allBlocks.append(block)
            # print("Type: " + block['BlockType'])
            # print('Page: {}'.format(block['Page']))
            # if 'Text' in block and block['BlockType'] == "LINE":
            # #     print("Text: " + block['Text'])
            #     allBlocks.append(block['Text'])
            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True
                
        # body = ""
        # for item in response['Blocks']:
        #     if 'Text' in item:
        #         print("Text: " + item['Text'])
        #         body += item["Text"]
        #         body += " "
            
        # allBlocks.append(body)
        # if len(allBlocks) == 0:
        #     allBlocks = response['Blocks']
        # else:
        #     for block in response['Blocks']:
        #         allBlocks.append(block)
        # # print(type(blocks))
        # print('Blocks len' + str(len(allBlocks)))
        
    #     if 'NextToken' in response:
    #         print(response['NextToken'])
    #         paginationToken = response['NextToken']
    #     else:
    #         finished = True
    # for i in allBlocks:
    #     print(i)
    return allBlocks
            
def GetResultsDocumentAnalysis(jobId):
    maxResults = 1000
    paginationToken = None
    finished = False
    allBlocks = []
    while finished == False:

        response = None
        if paginationToken == None:
            response = client.get_document_analysis(JobId=jobId,
                                                           MaxResults=maxResults)
        else:
            response = client.get_document_analysis(JobId=jobId,
                                                           MaxResults=maxResults,
                                                           NextToken=paginationToken)


            # Get the text blocks
        blocks = response['Blocks']
        print('Analyzed Document Text')
        print('Pages: {}'.format(response['DocumentMetadata']['Pages']))
        # Display block information
        for block in blocks:
            allBlocks.append(block)

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True
    return allBlocks


def CreateTopicandQueue():

    millis = str(int(round(time.time() * 1000)))

    # Create SNS topic
    snsTopicName = "AmazonTextractTopic" + millis

    topicResponse = sns.create_topic(Name=snsTopicName)
    snsTopicArn = topicResponse['TopicArn']

    # create SQS queue
    sqsQueueName = "AmazonTextractQueue" + millis
    sqs.create_queue(QueueName=sqsQueueName)
    sqsQueueUrl = sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']

    attribs = sqs.get_queue_attributes(QueueUrl=sqsQueueUrl,
                                            AttributeNames=['QueueArn'])['Attributes']

    sqsQueueArn = attribs['QueueArn']

    # Subscribe SQS queue to SNS topic
    sns.subscribe(
        TopicArn=snsTopicArn,
        Protocol='sqs',
        Endpoint=sqsQueueArn)

    # Authorize SNS to write SQS queue
    policy = """{{
"Version":"2012-10-17",
"Statement":[
{{
    "Sid":"MyPolicy",
    "Effect":"Allow",
    "Principal" : {{"AWS" : "*"}},
    "Action":"SQS:SendMessage",
    "Resource": "{}",
    "Condition":{{
    "ArnEquals":{{
        "aws:SourceArn": "{}"
    }}
    }}
}}
]
}}""".format(sqsQueueArn, snsTopicArn)

    response = sqs.set_queue_attributes(
        QueueUrl=sqsQueueUrl,
        Attributes={
            'Policy': policy
        })
    return sqsQueueUrl, snsTopicArn
    
    
    
def asyncAnalysis(roleArn, document, bucket, first):
    print("asyncAnalysis")
    sqsQueueUrl, snsTopicArn = CreateTopicandQueue()
    print('queue and topic created: \n queueUrl: ' + sqsQueueUrl + '\n topicArn: ' + snsTopicArn)
    try:
        if first == False:
            print("This is second analysis")
            analysis = client.start_document_text_detection(
                DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': document}},
                NotificationChannel={'RoleArn': roleArn, 'SNSTopicArn': snsTopicArn})
            print('Processing type: Detection')
            jobId = analysis['JobId']
        else:
            print("This is first analysis")
            analysis = client.start_document_analysis(
                DocumentLocation={ 
                "S3Object": { 
                    "Bucket": bucket,
                    "Name": document,
                }},
                FeatureTypes=["TABLES", "FORMS"],
                NotificationChannel={
                    'SNSTopicArn': snsTopicArn,
                    'RoleArn': roleArn,               
                })
            jobId = analysis['JobId']
            print(
                    "Started text analysis job" + jobId + ' on document ' + document)
    except ClientError:
            print("Couldn't analyze text in " + document)
            raise
    else:
        print('jobid' + jobId)

    jobFound = False
    dotLine = 0
    while jobFound == False:
        sqsResponse = sqs.receive_message(QueueUrl=sqsQueueUrl, MessageAttributeNames=['ALL'],
                                                MaxNumberOfMessages=10)
        print('sqsResponse: ' + json.dumps(sqsResponse))
        if sqsResponse:

            if 'Messages' not in sqsResponse:
                if dotLine < 40:
                    print('.', end='')
                    dotLine = dotLine + 1
                else:
                    print()
                    dotLine = 0
                sys.stdout.flush()
                time.sleep(1)
                continue

            for message in sqsResponse['Messages']:
                notification = json.loads(message['Body'])
                textMessage = json.loads(notification['Message'])
                print(textMessage['JobId'])
                print(textMessage['Status'])
                if str(textMessage['JobId']) == analysis['JobId']:
                    print('Matching Job Found:' + textMessage['JobId'])
                    jobFound = True
                    if first == True:
                        blocks = GetResultsDocumentAnalysis(textMessage['JobId'])
                    else:
                        blocks = GetResultsDocumentDetection(textMessage['JobId'])
                        for i in blocks:
                            print(i)
                    sqs.delete_message(QueueUrl=sqsQueueUrl,
                                            ReceiptHandle=message['ReceiptHandle'])
                else:
                    print("Job didn't match: " + str(textMessage['JobId']))
                # Delete the unknown message. Consider sending to dead letter queue
                    sqs.delete_message(QueueUrl=sqsQueueUrl,
                                            ReceiptHandle=message['ReceiptHandle'])
    return blocks


def lambda_handler(event, context):
    #TODO create bucket dynamically
    roleArn = "arn:aws:iam::719767148974:role/service-role/myFunction2-role-0w9hfb77"
    bucket = "amazontextractbucket"
    document = event['filename']
    # s3 = boto3.client("s3") # example client, could be any
    regionName = "eu-central-1"
   
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
        
    else:
        print("This is image")
        response = client.detect_document_text(
                Document={'S3Object': {'Bucket': bucket, 'Name': document}})
        blocks=response['Blocks']
        body = ""
        for item in blocks:
            if item["BlockType"] == "LINE":
                body += item["Text"]
                body += " "
        
    # calling lambda to find distance
    input = {
        "text" : body,
    }
    # print(json.dumps(in))
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
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    