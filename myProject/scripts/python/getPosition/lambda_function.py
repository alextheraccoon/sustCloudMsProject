import json
import boto3
import datetime
import json
import pandas as pd

# '["Senador PetrÃ´nio Portela Airport", "Qionghai Bo'ao Airport", "Guarani International Airport", "Perales Airport", "Anderson Regional Airport", "Pinto Martins International Airport", "Guangzhou Baiyun International Airport", "Lakefront Airport", "Villanova D'Albenga International Airport", "Antonio Nery Juarbe Pol Airport','Malpensa International Airport", "Dubai International Airport"]'
def lambda_handler(event, context):
    
    #define bucket and dataset
    bucket = "amazontextractbucket"
    filename = "airport_iata.csv"
    
    client = boto3.client('location')
    locations = event['locations']
    # print(locations)
    indexName = 'PlaceIndex'
    indexNameCreated = False
    all_place_indexes = client.list_place_indexes(
        MaxResults=50,
    )
    
    for i in all_place_indexes['Entries']:
        if i['IndexName'] == indexName:
            indexNameCreated = True
            break
    if indexNameCreated == False:
        response = client.create_place_index(
            DataSource='Here',
            IndexName='PlaceIndex',
            PricingPlan='RequestBasedUsage',
        )
        indexName = response['IndexName']
        indexNameCreated = False
    s3_client = boto3.client('s3') # example client, could be any
    
    region = s3_client.meta.region_name
    resp = s3_client.get_object(Bucket=bucket, Key=filename)
    df = pd.read_csv(resp['Body'], sep=',')
    df = df[df['iata_code'].notna()]
    df = df[df['coordinates'].notna()]
    # local_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone()
    
    analysedLocations = []
    for i in locations:
        print(i)
        coords = df.loc[df['name'] == i, 'coordinates'].item().split(",")
        print(coords)
        coord1 = float(coords[0])
        coord2 = float(coords[1])
        
        response = client.search_place_index_for_position(
            IndexName=indexName, 
            Position=[
                coord1, coord2
            ],
            MaxResults= 1
        )
    # print(local_timezone)
        location = response['Results'][0]['Place']['TimeZone']['Name']
        print(location)
        if region[0].lower() == location[0].lower():
            analysedLocations.append((i, True))
        else:
            analysedLocations.append((i, False))
            
            
        # for i in response['Results'][0]['Place']['TimeZone']['Name']:
        #     if i['Place']['TimeZone']['Name'] not in regions:
        #         regions.append(i['Place']['TimeZone']['Name'])
    
    response = client.delete_place_index(
        IndexName=indexName
    )
    
    if len(analysedLocations) == 0:
        return {
            'statusCode': 200,
            'error' : "no analysis could be possible"
        }
    else:
        return {
            'statusCode': 200,
            'locations': analysedLocations
        }
