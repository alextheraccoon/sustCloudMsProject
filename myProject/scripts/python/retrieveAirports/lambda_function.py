import json
import pandas as pd
import boto3

def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    filename = 'airport_iata.csv'
    bucket = 'amazontextractbucket'
    resp = s3_client.get_object(Bucket=bucket, Key=filename)
    df = pd.read_csv(resp['Body'], sep=',')
    df = df[df['iata_code'].notna()]
    df = df[df.type != 'closed']
    df = df[df.type != 'small_airport'] 
    df = df[df.type != 'heliport']
    df = df[df.type != 'seaplane_base']
    df = df[df.type != 'balloonport']
    airports = []
    for index, row in df.iterrows():
        airports.append({"iata":row['iata_code'],"name":row['name'], "coord": row['coordinates']})
    if len(airports) > 0:
        return {
            "statusCode": 200,
            "airports": airports
        }
    else:
        return {
            'statusCode': 400,
            'message': 'could not find airports'
        }