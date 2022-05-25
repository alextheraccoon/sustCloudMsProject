public with sharing class AirportsController {
    //Account search method
    @AuraEnabled
    public static Decimal getAirportsFrom (){
        
        HttpRequest request = new HttpRequest();
            //String textractEndpoint = 'https://tno9rdnt25.execute-api.eu-central-1.amazonaws.com/prod/dynamodbmanager';
        request.setEndpoint('callout:retrieveAirportsAWS');
        request.setMethod('GET');
        request.setTimeout(120000);
        Http httpLambda = new Http();
        // request to start analysis for pdf doc -- lambda func = myFunction2
        HttpResponse response = httpLambda.send(request);
        if (response.getstatuscode() == 200){

            Map<String, Object> d = (Map<String, Object>)JSON.deserializeUntyped(response.getBody());
            system.debug(d);
            List<Object> airports = (List<Object>) d.get('airports');
            List<Airport__c> airports_obj_1 = new List<Airport__c>();
            List<Airport__c> airports_obj_2 = new List<Airport__c>();
            List<Airport__c> airports_obj_3 = new List<Airport__c>();
            List<Airport__c> airports_obj_4 = new List<Airport__c>();
            List<Airport__c> airports_obj_5 = new List<Airport__c>();
            Decimal count = 0;
            for (Object airport : airports) {
                Map<String, Object> airport_obj = (Map<String, Object>) airport;
                // str.split('-', 2);
                String name = (String)airport_obj.get('name');
                String iata = (String)airport_obj.get('iata');
                String coord = (String)airport_obj.get('coord');
                if (count < 1000){
                    airports_obj_1.add(createAirportRecord(name, iata, coord));
                    
                } else if (count >= 1000 && count < 2000){
                    airports_obj_2.add(createAirportRecord(name, iata, coord));
                    
                } else if (count >= 2000 && count < 3000){
                    airports_obj_3.add(createAirportRecord(name, iata, coord));
                    
                } else if (count >= 3000 && count < 4000){
                    airports_obj_4.add(createAirportRecord(name, iata, coord));
                    
                } else {
                    airports_obj_5.add(createAirportRecord(name, iata, coord));
                   
                }
                count++;
                
                // String s = '-158.617996216, 59.2826004028';
                // List<String> ss = s.split(',', 2);
                // String lat1 = ss[0];
                // Double lat = double.valueOf(lat1);
                // Double lon = double.valueOf(ss[1]);
            }
            // system.debug(airports_obj.size());
            try {
                if(!airports_obj_1.isEmpty() && !airports_obj_2.isEmpty() && !airports_obj_3.isEmpty() && !airports_obj_4.isEmpty()
                && !airports_obj_5.isEmpty()){
                    Database.SaveResult[] result_1 = database.insert(airports_obj_1);
                    Database.SaveResult[] result_2 = database.insert(airports_obj_2);
                    Database.SaveResult[] result_3 = database.insert(airports_obj_3);
                    Database.SaveResult[] result_4 = database.insert(airports_obj_4);
                    Database.SaveResult[] result_5 = database.insert(airports_obj_5);
                    
                }
            } catch (Exception e) {
                System.debug(e);
                return 0;
            }
            return 1;
        }
        return 0;
    }

    //This method inserts file information to Custom Attachment object
    public static Airport__c createAirportRecord (String name, String iata, String coords){
        Airport__c airport = new Airport__c();
        airport.Name = name;
        airport.Iata_Code__c = iata;
        airport.Coordinates__c = coords;
        return airport;                                          
    }

    @AuraEnabled(cacheable=true)
    public static List<Airport__C> retrieveAirports(String input){
        String KeyString = '%' +  input + '%';
        return [Select Id, Name From Airport__C Where Name like:KeyString];
    }

    @AuraEnabled(cacheable=true)
    public static String findCoords(String name){
        List<Airport__C> l = [Select Id, Name, Coordinates__c, Iata_Code__c From Airport__C Where Name like:name];
        return l[0].Coordinates__c;
    }
}
