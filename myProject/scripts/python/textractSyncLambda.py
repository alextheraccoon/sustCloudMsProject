import json
import boto3
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

import boto3
import io
from io import BytesIO
import sys

import math
# from PIL import Image, ImageDraw, ImageFont

def ShowBoundingBox(draw,box,width,height,boxColor):
             
    left = width * box['Left']
    top = height * box['Top'] 
    draw.rectangle([left,top, left + (width * box['Width']), top +(height * box['Height'])],outline=boxColor)   

def ShowSelectedElement(draw,box,width,height,boxColor):
             
    left = width * box['Left']
    top = height * box['Top'] 
    draw.rectangle([left,top, left + (width * box['Width']), top +(height * box['Height'])],fill=boxColor)  

# Displays information about a block returned by text detection and text analysis
def DisplayBlockInformation(block):
    print('Id: {}'.format(block['Id']))
    if 'Text' in block:
        print('    Detected: ' + block['Text'])
    print('    Type: ' + block['BlockType'])
   
    if 'Confidence' in block:
        print('    Confidence: ' + "{:.2f}".format(block['Confidence']) + "%")

    if block['BlockType'] == 'CELL':
        print("    Cell information")
        print("        Column:" + str(block['ColumnIndex']))
        print("        Row:" + str(block['RowIndex']))
        print("        Column Span:" + str(block['ColumnSpan']))
        print("        RowSpan:" + str(block['ColumnSpan']))    
    
    if 'Relationships' in block:
        print('    Relationships: {}'.format(block['Relationships']))
    print('    Geometry: ')
    print('        Bounding Box: {}'.format(block['Geometry']['BoundingBox']))
    print('        Polygon: {}'.format(block['Geometry']['Polygon']))
    
    if block['BlockType'] == "KEY_VALUE_SET":
        print ('    Entity Type: ' + block['EntityTypes'][0])
    
    if block['BlockType'] == 'SELECTION_ELEMENT':
        print('    Selection element detected: ', end='')

        if block['SelectionStatus'] =='SELECTED':
            print('Selected')
        else:
            print('Not selected')    
    
    if 'Page' in block:
        print('Page: ' + block['Page'])
    print()
    
    
    

def lambda_handler(event, context):
    bucket = "amazontextractbucket"
    # const payload = JSON.parse(event)
    document=event['filename']
    client = boto3.client('textract')
    logger.info(event)


    #process using S3 object
    # response = client.detect_document_text(
    #     Document={'S3Object': {'Bucket': bucket, 'Name': document}})
        
    response = client.analyze_document(
        Document={'S3Object': {'Bucket': bucket, 'Name': document}},
        FeatureTypes=["TABLES", "FORMS"])

    #Get the text blocks
    blocks=response['Blocks']
    
    return {
        'statusCode': 200,
        'body': json.dumps(blocks)
    }                
            

