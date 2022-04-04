import json
import boto3
import pandas as pd

def find_airport_coord(x, df):
    item = df.loc[df['iata_code'] == x, 'coordinates'].item()
    coords = item.split(',')
    coords = [float(s) for s in coords]
    coords = (coords[0], coords[1])
    return coords

def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    bucket = 'amazontextractbucket'
    filename = 'airport_iata.csv'
    region = 'eu-central-1'
    body = "{\"DATA DEL VIAGGIO / TRAVEL DATE \": \"24 JUL 2021 \", \"ORARIO DI CHIUSURA USCITA DI IMBARCO / GATE CLOSES \": \"10:45 \", \"POSTO NUMERO / SEAT NUMBER \": \"21E \", \"PASSEGGERO / PASSENGER \": \"VICINI, ALESSANDRA Sig.a \", \"NUMERO DEL VOLO / FLIGHT NUMBER \": \"EJU2717 \", \"A / TO \": \"(LIS) Lisbona (T2) \", \"DA / FROM \": \"(MXP) Milano Malpensa (T1) \", \"ORARIO DI PARTENZA DEL VOLO / FLIGHT DEPARTS \": \"11:15 \"}"
    try:
        translate = boto3.client(service_name='translate', region_name=region, use_ssl=True)
        result = translate.translate_text(Text=body, SourceLanguageCode="auto" , TargetLanguageCode="en")
        translated_body = str(result.get('TranslatedText'))
        print('TranslatedText: ' + str(result.get('TranslatedText')))
        print('SourceLanguageCode: ' + result.get('SourceLanguageCode'))
        print('TargetLanguageCode: ' + result.get('TargetLanguageCode'))
  
        resp = s3_client.get_object(Bucket=bucket, Key=filename)
        df = pd.read_csv(resp['Body'], sep=',')
        df = df[df['iata_code'].notna()]
        translated_body = translated_body.split(" ")
        
        spec_chars = "\.[]{}()<>*+-=!?^$|/:,\"“”"
        
        new_body = []
        for x in translated_body:
        #     print(x)
            for c in spec_chars:
                x = x.replace(c, "")
            new_body.append(x.lower())
        print(new_body)
        coords = []
        for x in new_body:
            if len(x) == 3 and x.upper() in df.iata_code.values:
                # print(airport)
                airport = df.loc[df['iata_code'] == x.upper(), 'name'].item()
                airport_list = airport.split(" ")
                for name in airport_list:
                    for char in spec_chars:
                        name = name.replace(char, "")
                    print(name)
        #             print(new_body)
                    if name.lower() in new_body:
                        print(name)
                        r = find_airport_coord(x.upper(), df)
                        print(r)
                        if r not in coords:
                            coords.append((r,airport))
                            break
        distances = []
        if len(coords) == 2:
            distance = geopy.distance.distance(coords[0][0], coords[1][0]).km
            print("Distance: " + distance + "from " + coords[0][1] + "to " + coords[1][1])
        elif len(coords) < 2:
            print("we could not find your trip points")
        else:
            for i in coords:
                for j in coords:
                    if i != j:
                        distances.append((geopy.distance.distance(coords[i][0], coords[j][0]).km, (coords[i][1], coords[j][1])))
                        
        
    except Exception as err:
      print(err)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
