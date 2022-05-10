public with sharing class IsSameRegion {
    @AuraEnabled
    public static Map<String,Object> checkRegion(String[] locations){
        Map<String, Object> results = new Map<String,Object>();
        String[] locationsString = new List<String>();
        for (String x : locations) {
            locationsString.add(String.valueOf(x));
        }
        HttpRequest req = new HttpRequest();
        req.setMethod('POST');
        req.setTimeout(120000);
        req.setEndpoint('callout:sameRegion');
        System.debug('locations:' + locationsString);
        String sbody = '{"locations": ' + JSON.serialize(locationsString) + '}';
        req.setBody(sbody);
        Http httpLambda = new Http();
        HttpResponse response = httpLambda.send(req);
        System.debug('*Lambda Resp:' + response.getBody());
        if (response.getstatuscode() == 200){
            results = (Map<String, Object>)JSON.deserializeUntyped(response.getBody());
            
        }
        return results;
    }
}