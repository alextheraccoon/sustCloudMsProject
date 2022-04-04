
import sys
import time

client = boto3.client('textract')
sqs = boto3.client('sqs')
sns = boto3.client('sns')
bucket = "amazontextractbucket"
# # const payload = JSON.parse(event)

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


def GetResultsDocumentAnalysis(jobId):
    maxResults = 1000
    paginationToken = None
    finished = False

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
        if 'NextToken' in response:
            paginationToken = response['NextToken']
        else:
            finished = True
    return blocks


def lambda_handler(event, context):
    
    document=event['filename']
    roleArn = 'arn:aws:iam::719767148974:role/service-role/myFunction2-role-0w9hfb77'
    bucket = 'amazontextractbucket'
    document = document=event['filename']
    region_name = 'eu-central-1'
    sqsQueueUrl = 'arn:aws:sqs:eu-central-1:719767148974:AmazonTextractMyqueue'
    snsTopicArn = 'arn:aws:sns:eu-central-1:719767148974:AmazonTextractMytopic'

    try:
        analysis = client.start_document_analysis(
            DocumentLocation={ 
            "S3Object": { 
                "Bucket": bucket,
                "Name": document,
            }},
            FeatureTypes=["TABLES", "FORMS"],
            NotificationChannel={
                'SNSTopicArn': 'arn:aws:sns:eu-central-1:719767148974:AmazonTextractMytopic',
                'RoleArn': 'arn:aws:iam::719767148974:role/service-role/myFunction2-role-0w9hfb77'
            })
        jobId = analysis['JobId']
        logger.info(
                "Started text analysis job %s on %s.", jobId, document)
    except ClientError:
            logger.exception("Couldn't analyze text in %s.", document)
            raise
    else:
        logger.info(jobId)

    jobFound = False
    dotLine = 0
    while jobFound == False:
        sqsResponse = sqs.receive_message(QueueUrl=sqsQueueUrl, MessageAttributeNames=['ALL'],
                                                MaxNumberOfMessages=10)

        if sqsResponse:

            if 'Messages' not in sqsResponse:
                if dotLine < 40:
                    # print('.', end='')
                    dotLine = dotLine + 1
                else:
                    # print()
                    dotLine = 0
                sys.stdout.flush()
                time.sleep(5)
                continue

            for message in sqsResponse['Messages']:
                notification = json.loads(message['Body'])
                textMessage = json.loads(notification['Message'])
                # print(textMessage['JobId'])
                # print(textMessage['Status'])
                if str(textMessage['JobId']) == analysis['JobId']:
                    # print('Matching Job Found:' + textMessage['JobId'])
                    jobFound = True
                    blocks = GetResultsDocumentAnalysis(textMessage['JobId'])
                    sqs.delete_message(QueueUrl=sqsQueueUrl,
                                            ReceiptHandle=message['ReceiptHandle'])
                else:
                    logger.info("Job didn't match: %s", str(textMessage['JobId']))
                    
                    
                    
                # Delete the unknown message. Consider sending to dead letter queue
                    sqs.delete_message(QueueUrl=sqsQueueUrl,
                                            ReceiptHandle=message['ReceiptHandle'])

            # print('Done!')


        
    # try:
    #     response = client.get_document_analysis(
    #             JobId=jobId)
    #     job_status = response['JobStatus']
    #     logger.info("Job %s status is %s.", jobId, job_status)
    # except ClientError:
    #     logger.exception("Couldn't get data for job %s.", jobId)
    #     raise
    # else:
    #     logger.info("Response of get doc analysis", jobId, response)