public with sharing class AWSFileUploadController {
    
    //This method is used to post file to AWS
    @AuraEnabled
    public static boolean uploadFileToAWS(Id parentId,
                                        String strfileName, String fileType,
                                        String fileContent){
        System.debug('parentId=' + parentId);
        System.debug('strfileName=' + strfileName);
        System.debug('fileType=' + fileType);
        System.debug('fileContent= ' + fileContent);
                
        Blob contentBlob = EncodingUtil.base64Decode(fileContent);
        String formattedDateString = Datetime.now().formatGMT('EEE, dd MMM yyyy HH:mm:ss z');
        String dateString = Datetime.now().format('ddMMYYYYHHmmss');        
        String filename = strfileName.deleteWhitespace();        
        //AWS specific information
        String key = 'AKIA2PFLXDGXCWQQXBEK'; //AWS key
        String secret = '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'; //AWS Secret key
        String bucketname = 'amazontextractbucket'; //AWS bucket name
        String host = 's3.eu-central-1.amazonaws.com'; //'s3.amazonaws.com:443'
        String method = 'PUT';
        String endPoint = 'https://' + bucketname + '.' + host + '/'+ filename;
        system.debug('filename ' + filename );
        HttpRequest req = new HttpRequest();
        req.setMethod(method);
        req.setEndpoint('callout:amazonTextract'+ '/' + filename);
        req.setHeader('Host', bucketname + '.' + host);
        req.setHeader('Content-Encoding', 'UTF-8');
        req.setHeader('Content-type', fileType);
        req.setHeader('Connection', 'keep-alive');
        req.setHeader('Date', formattedDateString); 
        req.setHeader('ACL', 'public-read-write');
        req.setBodyAsBlob(EncodingUtil.base64Decode(fileContent));
        
        system.debug('req =' + req.getBody());
        system.debug('Endpoint='+endPoint);

        //finally send information to AWS        
        Http http = new Http();
        try {
        HTTPResponse res = http.send(req);
        System.debug('*Resp:' + String.ValueOF(res.getBody()));
        System.debug('RESPONSE STRING: ' + res.toString());
        System.debug('RESPONSE STATUS: ' + res.getStatus());
        System.debug('STATUS_CODE: ' + res.getStatusCode());

        if(res.getStatusCode() == 200){
            // insertAttachmentRecord (parentId,strfileName,endPoint);
            HttpRequest request = new HttpRequest();
            String textractEndpoint = 'https://q80f69uj52.execute-api.eu-central-1.amazonaws.com/default/myFunction2';
            request.setEndpoint(textractEndpoint);
            request.setMethod('POST');
            // request.setHeader('Content-Type', 'application/json;charset=UTF-8');
            
            // Set the body as a JSON object
            string sBody = '{  "key": "' + filename + '" }';
            request.setBody(sBody);

            Http httpLambda = new Http();
            HttpResponse response = httpLambda.send(request);

            System.debug('*Resp:' + String.ValueOF(response.getBody()));

            return true;
        }
        } catch (DmlException e) {
        System.debug('The following exception has occurred: ' + e.getMessage());
        }
       

        
        return false;
    }

    //This method inserts file information to Custom Attachment object
    public static void insertAttachmentRecord (Id parentId, String fileName, String fileURL){
        Attachment__c attachment = new Attachment__c();
        attachment.Opportunity__c = parentId;
        attachment.FileURL__c = fileURL;
        attachment.File_Name__c =  fileName;
        insert attachment;                                           
    }

    //This method retrieves Attachment record based on OpportunityId
    @AuraEnabled
    public static List<Attachment__c> displayUploadedFiles(Id parentId){
        return [SELECT Id, File_Name__c, FileURL__c FROM Attachment__c
                WHERE Opportunity__c =:parentId];
    }
}