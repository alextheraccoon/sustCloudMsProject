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
    body = event['Body']
    print(body)
    # body = "PRIORITY VRYANAIR GETAWAY CAFE REGULAR CARTA D'IMBARCO Puoi rimuovere la maschera per goderti il pasto/l'offerta a bordo ITALIA ID/AY-2938 S SCARICA LA RIVISTA PRIORITÀ OFFERTA PASTO 1 Pasto a BGY - BCN I FR6354 10€ ALESSANDRA VICINI Risparmia fino al 13% Imbarco Posto * HARIBO Posteriore 18E Riferimento Centrale AHEF9B Seq 5 1 Bevanda 1 Spuntino 1 Piatto PROFUMI A soli 20€ Milano - X - Barcellona El (Bergamo) Prat Data Il gate chiude Partenze Covigion DSquared 50ml RED GREEN 05. feb 2022 08:05 08:35 WOOD WOOD Ralph Lauren Polo 50ml DSQUARIED2 DSQUARED2 CK Sheer Beauty 50ml Il Il Il ? 381 86:3HV INIOIA ojon lap OT:OT sons zzoz OLVEVS 'alle) uood un and oduan ieu 'nnuim"
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
        
        spec_chars = "\.[]{}()<>*+-=!?^$|/:,\"“” \' "
        
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
        distance = 0
        startPoint = 0
        endPoint = 0
        location = boto3.client('location')
        calculator = location.create_route_calculator(
            CalculatorName='HereCalculator',
            DataSource='Here',
        )
        # print('starting point ' + str(coords[0][0][0]) + " " + str(coords[0][0][1]))
        # print('end point ' + str(coords[1][0][0]) + " " + str(coords[1][0][1]))
        if len(coords) == 2:
            response = location.calculate_route(
                CalculatorName=calculator['CalculatorName'],
                DeparturePosition=[coords[0][0][0], coords[0][0][1]],
                DestinationPosition=[coords[1][0][0], coords[1][0][1]],
                IncludeLegGeometry=False,
                DistanceUnit='Kilometers'
            )
            distance = response['Summary']['Distance']
            startPoint = coords[0][1]
            endPoint = coords[1][1]
        # print(response['Summary'])
        elif len(coords) < 2:
            response = location.delete_route_calculator(
                CalculatorName=calculator['CalculatorName']
            )
            return {
                'statusCode': 400,
                'body': json.dumps('Departure and end point not recognized')
            }
        else:
            for i in coords:
                for j in coords:
                    if i != j:
                        response = location.calculate_route(
                            CalculatorName=calculator['CalculatorName'],
                            DeparturePosition=[coords[i][0][0], coords[i][0][1]],
                            DestinationPosition=[coords[j][0][0], coords[j][0][1]],
                            IncludeLegGeometry=False,
                            DistanceUnit='Kilometers'
                        )
                        distances.append((response['Summary']['Distance'], (coords[i][1], coords[j][1])))
        response = location.delete_route_calculator(
            CalculatorName=calculator['CalculatorName']
        )
        # if len(coords) == 2:
        #     distance = geopy.distance.distance(coords[0][0], coords[1][0]).km
        #     print("Distance: " + distance + "from " + coords[0][1] + "to " + coords[1][1])
        # elif len(coords) < 2:
        #     print("we could not find your trip points")
        # else:
        #     for i in coords:
        #         for j in coords:
        #             if i != j:
        #                 distances.append((geopy.distance.distance(coords[i][0], coords[j][0]).km, (coords[i][1], coords[j][1])))
                        
        
    except Exception as err:
      print(err)
      
    return {
        'statusCode' : 200,
        'Distance' : distance,
        'Possible routes' : distances,
        'StartPoint' : startPoint,
        'EndPoint' : endPoint
    }
        
