import json

import boto3
import json
import sys
import time
from botocore.exceptions import ClientError


class ProcessType:
    DETECTION = 1
    ANALYSIS = 2


class DocumentProcessor:
    jobId = ''
    region_name = ''

    roleArn = ''
    bucket = ''
    document = ''

    sqsQueueUrl = ''
    snsTopicArn = ''
    processType = ''

    def __init__(self, role, bucket, document, region):
        self.roleArn = role
        self.bucket = bucket
        self.document = document
        self.region_name = region

        self.textract = boto3.client('textract', region_name=self.region_name)
        self.sqs = boto3.client('sqs')
        self.sns = boto3.client('sns')

    def ProcessDocument(self, type):
        

        self.processType = type
        validType = False

        # Determine which type of processing to perform
        if self.processType == ProcessType.DETECTION:
            response = self.textract.start_document_text_detection(
                DocumentLocation={'S3Object': {'Bucket': self.bucket, 'Name': self.document}},
                NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn})
            print('Processing type: Detection')
            validType = True

        if self.processType == ProcessType.ANALYSIS:
            response = self.textract.start_document_analysis(
                DocumentLocation={'S3Object': {'Bucket': self.bucket, 'Name': self.document}},
                FeatureTypes=["TABLES", "FORMS"],
                NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn})
            print('Processing type: Analysis')
            validType = True

        if validType == False:
            print("Invalid processing type. Choose Detection or Analysis.")
            return

        print('Start Job Id: ' + response['JobId'])
        return response['JobId']
        
        
    def FindResult(self, jobId):
        jobFound = False
        dotLine = 0
        while jobFound == False:
            sqsResponse = self.sqs.receive_message(QueueUrl=self.sqsQueueUrl, MessageAttributeNames=['ALL'],
                                                   MaxNumberOfMessages=10)

            if sqsResponse:

                if 'Messages' not in sqsResponse:
                    if dotLine < 40:
                        print('.', end='')
                        dotLine = dotLine + 1
                    else:
                        print()
                        dotLine = 0
                    sys.stdout.flush()
                    time.sleep(5)
                    continue

                for message in sqsResponse['Messages']:
                    notification = json.loads(message['Body'])
                    textMessage = json.loads(notification['Message'])
                    print(textMessage['JobId'])
                    print(textMessage['Status'])
                    if str(textMessage['JobId']) == jobId:
                        print('Matching Job Found:' + textMessage['JobId'])
                        jobFound = True
                        text = self.GetResults(textMessage['JobId'])
                        self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                                ReceiptHandle=message['ReceiptHandle'])
                    else:
                        print("Job didn't match:" +
                              str(textMessage['JobId']) + ' : ' + str(response['JobId']))
                    # Delete the unknown message. Consider sending to dead letter queue
                    self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                            ReceiptHandle=message['ReceiptHandle'])

        print('Done!')
        return text

    def CreateTopicandQueue(self):

        millis = str(int(round(time.time() * 1000)))

        # Create SNS topic
        snsTopicName = "AmazonTextractTopic" + millis

        topicResponse = self.sns.create_topic(Name=snsTopicName)
        self.snsTopicArn = topicResponse['TopicArn']

        # create SQS queue
        sqsQueueName = "AmazonTextractQueue" + millis
        self.sqs.create_queue(QueueName=sqsQueueName)
        self.sqsQueueUrl = self.sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']

        attribs = self.sqs.get_queue_attributes(QueueUrl=self.sqsQueueUrl,
                                                AttributeNames=['QueueArn'])['Attributes']

        sqsQueueArn = attribs['QueueArn']

        # Subscribe SQS queue to SNS topic
        self.sns.subscribe(
            TopicArn=self.snsTopicArn,
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
}}""".format(sqsQueueArn, self.snsTopicArn)

        response = self.sqs.set_queue_attributes(
            QueueUrl=self.sqsQueueUrl,
            Attributes={
                'Policy': policy
            })

    def DeleteTopicandQueue(self):
        self.sqs.delete_queue(QueueUrl=self.sqsQueueUrl)
        self.sns.delete_topic(TopicArn=self.snsTopicArn)

   

    def GetResults(self, jobId):
        maxResults = 1000
        paginationToken = None
        finished = False
        allText = []
        while finished == False:

            response = None

            if self.processType == ProcessType.ANALYSIS:
                if paginationToken == None:
                    response = self.textract.get_document_analysis(JobId=jobId,
                                                                   MaxResults=maxResults)
                else:
                    response = self.textract.get_document_analysis(JobId=jobId,
                                                                   MaxResults=maxResults,
                                                                   NextToken=paginationToken)

            if self.processType == ProcessType.DETECTION:
                if paginationToken == None:
                    response = self.textract.get_document_text_detection(JobId=jobId,
                                                                         MaxResults=maxResults)
                else:
                    response = self.textract.get_document_text_detection(JobId=jobId,
                                                                         MaxResults=maxResults,
                                                                         NextToken=paginationToken)

            blocks = response['Blocks']
            print('Detected Document Text')
            print('Pages: {}'.format(response['DocumentMetadata']['Pages']))
            print("Blocks: " + str(len(blocks)))
            # Display block information
            ids = []
            count = 0
            bb = []
            for block in blocks:
                if block['Page'] == 1:
                    bb.append(block)
                
                if block['BlockType'] == "PAGE":
                    if block['Page'] == 1:
                        for r in block['Relationships']:
                            for id in r['Ids']:
                                ids.append(id)
            print("Ids len " + str(len(ids)))
            print("Page 1 blocks " + str(count))
            for ii in ids:
                # print("Id " + str(ii))
                for b in bb:
                    if ii == b['Id']:
                        if 'Text' in b:
                            allText.append(b['Text'])
                            # print(b['Text'])
                            break
            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True
        return allText
        
    def setParam(self, queue, topic):
        self.sqsQueueUrl = queue
        self.snsTopicArn = topic
        self.processType = ProcessType.ANALYSIS

    


def lambda_handler(event, context):
    roleArn = event['roleArn']
    bucket = event['bucket']
    document = event['filename']
    region_name = event['regionName']
    client_lambda = boto3.client('lambda')
    analyzer = DocumentProcessor(roleArn, bucket, document, region_name)
    if 'first' in event:
        analyzer.CreateTopicandQueue()
        jobId = analyzer.ProcessDocument(ProcessType.ANALYSIS)
        if jobId != None:
            return {
                'statusCode': 200,
                'jobId': jobId,
                'queueUrl' : analyzer.sqsQueueUrl,
                'topicArn' : analyzer.snsTopicArn
            }
        else:
            return {
                'statusCode': 400,
                'jobId': jobId,
                'queueUrl' : analyzer.sqsQueueUrl,
                'topicArn' : analyzer.snsTopicArn
            }
            
    else:
        if 'jobId' in event:
            analyzer.setParam(event['queueUrl'], event['topicArn'])
            text = analyzer.FindResult(event['jobId'])
    analyzer.DeleteTopicandQueue()
    
    if len(text) != 0:
        return {
            'statusCode': 200,
            'body': text
        }
    else:
        return {
            'statusCode': 400,
            'body': "couldn't fin any text"
        }
