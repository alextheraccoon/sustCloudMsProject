import json
import boto3
import pandas as pd
from math import pi , acos , sin , cos
import itertools
from isSameRegion import isSameRegion

def calcd(y1,x1, y2,x2):
   #
   y1  = float(y1)
   x1  = float(x1)
   y2  = float(y2)
   x2  = float(x2)
   #
   R   = 3958.76 # miles
   #
   y1 *= pi/180.0
   x1 *= pi/180.0
   y2 *= pi/180.0
   x2 *= pi/180.0
   #
   # approximate great circle distance with law of cosines
   #
   x = sin(y1)*sin(y2) + cos(y1)*cos(y2)*cos(x2-x1)
   if x > 1:
       x = 1
   return acos( x ) * R

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
    
    
    # body = "EXPOC2020DUBAIEmiratesTicket number: 176 2343157838UAETicket & receiptScan the bar code or use the ticket number above atOFFICIAL PREMIER PARTNERthe self check-in points in the airport.Passenger nameEmirates Skywards numberIssued by / DateBRAMBILLA/EK670542235AGT 86491845 AEURSULAMISS06NOV2021EKWWWWV DUBAI / EMIRATES IBEYour booking reference: P525NJYour ticket is stored in our booking system. This receipt is yourYou might need to show this receipt to enter the airport or to proverecord of your ticket and is part of your conditions of carriage.your return or onwards travel to immigration. Check with yourFor more information you can read the notices and conditions ofdeparture airport for restrictions on the carriage of liquids, aerosolscontract (Opens a new window).and gels in hand baggage and check your visa requirements.Check in online, orit3 hours60 minutes45 minutesCheck in at the airport. ArriveIf you're checking in bags, go toOnce you have checked in, goArrive at the boarding gate 45between 3 to 4 hours before yourour check-in counters at least 3through security. You should dominutes before departure. Theflight and follow the signs to ourhours before your flight.this at least 60 minutes beforegates close 20 minutes beforecheck-in counters.your flight.the flight leaves.Your travel informationAll times shown are local for each cityDeparting >> From Milan, ItalyLeg 1 of 2 Milan (MXP) to Dubai (DXB) | Operated by Emirates (equipment owner Emirates)FlightCheck-inDepartureEK 09210Nov202110Nov2021on)oMILAN18:3521:35Departing MXP, Malpensa AirportEconomyTerminal 1SaverSeatStatusArrivalConfirmed11Nov2021onfooDUBAI06:50Arriving DXB, Dubai International AirportTerminal 3Coupon validity: not before 10Nov2021 / not after 10Nov2021Baggage 25KgsYour travel informationAll times shown are local for each cityDeparting >> From Dubai, United Arab EmiratesLeg 2 of 2 | Dubai (DXB) to Milan (MXP) | Operated by Emirates (equipment owner Emirates)FlightCheck-inDepartureEK 09120Nov202120Nov2021on)DUBAI12:5515:55Departing DXB, Dubai International AirportEconomyTerminal 3SaverSeatStatusArrivalConfirmed20Nov2021ontoMILAN19:50Arriving MXP, Malpensa AirportTerminal 1Coupon validity: not before 20Nov2021 / not after 20Nov2021Baggage 25KgsC Emirates. All rights reserved Emirates Experience I Check-in Online | Manage a Booking | Baggage | Contact usPage 1 of 2"
    # body = "KOREAN AIR 5C yeors e-Ticket & Itinerary 2357 /08MAR19 Passenger Name Ticket Number Booking Reference GALLIDABINO/ANDREAPAOLO 1802326906507 88347367 (RG2S7L) MR Itinerary From To Flight MXP ICN KE 928 Milan(Malpensa) Seoul/Incheon(Incheon) Operated by KE 09JUN19(SUN) 22:00 (Local Time) 10JUN19(MON) 16:00 (Local Time) KSREANAIR Terminal No : 1 Terminal No : 2 Class : K (Economy) Status : OK (Confirmed) Seat number : Fare Basis : KLEOZRUK/5 Baggage : 1 Piece Validity : -09JUN20 Aircraft Type : Boeing 777-300ER Flight Duration : 11H 00M SKYPASS Miles : 5,509 From To Flight ICN MXP KE 927 Seoul/Incheon(Incheon) Milan (Malpensa) Operated by KE 16JUN19(SUN) 15:05 (Local Time) 16JUN19(SUN) 19:45 (Local Time) KSREANAIR Terminal No : 2 Terminal No : 1 Korean Air operates in Terminal 2 of Incheon Airport Class : U (Economy) Status : OK (Confirmed) Seat number : Fare Basis : ULEOZRUK/5 Baggage : 1 Piece Validity : -09JUN20 Aircraft Type : Boeing 777-300ER Flight Duration : 11H 40M SKYPASS Miles : 5,509 Schedules and aircraft type maybe changed without prior notice. For discounted or free tickets, mileage may not be provided or mileage accrual may be different depending on the booking class."
    # body = '{"Validity : ": "-09JUN20 ", "Fare Basis : ": "ULEOZRUK/5 ", "SKYPASS Miles : ": "5,509 ", "Status : ": "OK (Confirmed) ", "Aircraft Type : ": "Boeing 777-300ER ", "Flight Duration : ": "11H 40M ", "Booking Reference ": "88347367 (RG2S7L) ", "Baggage : ": "1 Piece ", "Terminal No : ": "1 ", "Class : ": "K (Economy) ", "Flight ": "KE 928 ", "Passenger Name ": "GALLIDABINO/ANDREAPAOLO MR ", "Seoul/Incheon(Incheon) ": "16JUN19(SUN) 15:05 (Local Time) ", "Milan (Malpensa) ": "16JUN19(SUN) 19:45 (Local ", "Seat number : ": "", "ICN ": "Seoul/Incheon(Incheon) 10JUN19(MON) 16:00 (Local ", "Ticket Number ": "1802326906507 ", "Operated by KE ": "X KSREANAIR ", "From ": "", "Itinerary ": "From "}'
    distances = []
    distance = 0
    startPoint = 0
    endPoint = 0
    resp = s3_client.get_object(Bucket=bucket, Key=filename)
    df = pd.read_csv(resp['Body'], sep=',')
    df = df[df['iata_code'].notna()]
    df = df[df.type != 'closed']
    df = df[df.type != 'small_airport'] 
    df = df[df.type != 'heliport']
    df = df[df.type != 'seaplane_base']
    df = df[df.type != 'balloonport']
    indexName = 'PlaceIndex'
    indexNameCreated = False
    if "text" in event:
        body = event["text"]
    else:
        if "point1" in event and "point2" in event:
            loc1 = event["point1"]
            loc2 = event["point2"]
            client_location = boto3.client('location')
            
            all_place_indexes = client_location.list_place_indexes(
                MaxResults=50,
            )
            for i in all_place_indexes['Entries']:
                if i['IndexName'] == indexName:
                    indexNameCreated = True
                    break
            if indexNameCreated == False:
                response_location = client_location.create_place_index(
                    DataSource='Here',
                    IndexName='PlaceIndex',
                    PricingPlan='RequestBasedUsage',
                )
                indexNameCreated = True
                indexName = response_location['IndexName']
                
            response_loc1 = client_location.search_place_index_for_text(
                IndexName=indexName,
                Text=loc1,
                MaxResults=1
            )
            try:
                # type = array
                coords1 = response_loc1['Results'][0]['Place']['Geometry']['Point']
                response_loc2 = client_location.search_place_index_for_text(
                    IndexName=indexName,
                    Text=loc2,
                    MaxResults=1
                )
                coords2 = response_loc2['Results'][0]['Place']['Geometry']['Point']
                response_deletion = client_location.delete_place_index(
                    IndexName=indexName
                )
                if len(coords2) == 2 and len(coords1) == 2:
                    distance_coords = calcd(coords1[0], coords1[1], coords2[0], coords2[1])
                    return {
                        'statusCode' : 200,
                        'Distance' : distance_coords,
                        'PossibleRoutes' : distances,
                        'StartPoint' : loc1,
                        'EndPoint' : loc2
                    }
                else:
                    return {
                        'statusCode' : 400,
                        'body': json.dumps('Departure and end point not recognized')
                    }
            except:
                return {
                        'statusCode' : 400,
                        'body': json.dumps('Departure and end point not recognized')
                    }
            
            
            
                
    print(body)
    
    try:
        translate = boto3.client(service_name='translate', region_name=region, use_ssl=True)
        result = translate.translate_text(Text=body, SourceLanguageCode="auto" , TargetLanguageCode="en")
        translated_body = str(result.get('TranslatedText'))
        print('TranslatedText: ' + str(result.get('TranslatedText')))
        print('SourceLanguageCode: ' + result.get('SourceLanguageCode'))
        print('TargetLanguageCode: ' + result.get('TargetLanguageCode'))
  
        
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
    
        print("coordinates size " + str(len(coords)))
        
        
        if len(coords) == 2:
            distance = calcd(coords[0][0][0], coords[0][0][1], coords[1][0][0], coords[1][0][1])
            # distance = response['Summary']['Distance']
            startPoint = coords[0][1]
            endPoint = coords[1][1]
        # print(response['Summary'])
        elif len(coords) < 2:
    
            return {
                'statusCode': 400,
                'body': json.dumps('Departure and end point not recognized')
            }
        else:
            
            combs = [subset for subset in itertools.combinations(coords, 2)]
            print("Combinations " + str(len(combs)))
            for i in combs:
                # print(i)
                distance = calcd(i[0][0][0],i[0][0][1], i[1][0][0], i[1][0][1] )
                if (distance, (i[0][1], i[1][1])) not in distances:
                    # isClose1 =isSameRegion(i[0][0][0],i[0][0][1])
                    # isClose2 = isSameRegion(i[1][0][0], i[1][0][1])
                    # print("isSameRegion " + i[0][1] + str(isClose1))
                    # print("isSameRegion " + i[1][1] + str(isClose2))
                    distances.append((distance, (i[0][1], i[1][1])))
                
            return {
                'statusCode' : 200,
                'Distance' : -1,
                'PossibleRoutes' : distances,
                'StartPoint' : -1,
                'EndPoint' : -1
            }   
            
                
    except Exception as err:
      print(err)
   
    
      
    return {
        'statusCode' : 200,
        'Distance' : distance,
        'PossibleRoutes' : distances,
        'StartPoint' : startPoint,
        'EndPoint' : endPoint
    }
        
