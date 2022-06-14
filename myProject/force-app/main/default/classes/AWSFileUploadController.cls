public with sharing class AWSFileUploadController {

    @AuraEnabled
    public static void deleteObject(String bucket, String filename){
        HttpRequest request = new HttpRequest();
        request.setMethod('POST');
        request.setTimeout(120000);
        request.setEndpoint('callout:awsDeleteObject');
        string body = '{ "object" : "' + filename + '", "bucket" : "' + bucket + '" }';
        request.setBody(body);
        Http http = new Http();
        // request to start analysis for pdf doc -- lambda func = myFunction2
        HttpResponse response = http.send(request);
        System.debug('*Lambda Resp:' + response.getBody());
    }

    @AuraEnabled
    public static Map<String,Object> analyzeObject(String format, String filename, String bucket){
        Map<String, Object> results = new Map<String,Object>();
       
        try {
            HttpRequest request = new HttpRequest();
            //String textractEndpoint = 'https://tno9rdnt25.execute-api.eu-central-1.amazonaws.com/prod/dynamodbmanager';
            request.setEndpoint('callout:awsLambda');
            request.setMethod('POST');
            request.setTimeout(120000);

            // String[] tokens = filename.split('\\.(?=[^\\.]+$)');
            // String format = tokens[1];
            Boolean isFirst = true;

            if (format.toLowerCase() == 'pdf'){
                string sBody = '{  "filename": "' + filename + '", "first": "' + isFirst + '" }';
                request.setBody(sBody);
                Http httpLambda = new Http();
                // request to start analysis for pdf doc -- lambda func = myFunction2
                HttpResponse firstResponse = httpLambda.send(request);

                System.debug('*Lambda Resp:' + firstResponse.getBody());
                
                if (firstResponse.getstatuscode() == 200){
                    HttpRequest sec_request = new HttpRequest();
                    //String textractEndpoint = 'https://tno9rdnt25.execute-api.eu-central-1.amazonaws.com/prod/dynamodbmanager';
                    sec_request.setEndpoint('callout:awsLambda');
                    sec_request.setMethod('POST');
                    sec_request.setTimeout(120000);
                    JSONParser parser = JSON.createParser(firstResponse.getBody());
                    // Advance to the start object marker, parse the string response object
                    parser.nextToken();
                    parser.nextValue();
                    parser.nextToken();
                    parser.nextValue();
                    String id = parser.getText();
                    parser.nextToken();
                    parser.nextValue();
                    String queue = parser.getText();
                    parser.nextToken();
                    parser.nextValue();
                    String topic = parser.getText();
                    String new_body = '{  "filename": "' + filename + '", "jobId": "' + id + '", "queueUrl": "'+ queue + '", "topicArn" : "' + topic +'" }';
                    sec_request.setBody(new_body);
                    Http httpLambda2 = new Http();
                    // wait some time
                    Long startingTime = System.now().getTime(); // Num milliseconds since Jan 1 1970
                    Integer delayInMilliseconds = 20000; // two-second delay
                    // while (System.now().getTime() - startingTime < delayInMilliseconds)  {
                    //      // Do nothing until desired delay has passed
                    // }
                    String timeoutResponse = 'Endpoint request timed out';
                    HttpResponse response = httpLambda2.send(sec_request);
                    // request to find pdf analysis job started and retrieve result -- lambda func = myFunction2
                    System.debug('second Lambda Resp:' + response.getBody());
                    JSONParser second_parser = JSON.createParser(response.getBody());
                    second_parser.nextToken();
                    second_parser.nextValue();
                    String response_body = second_parser.getText();
                    // check if the apex class timed out
                    if (response_body == timeoutResponse){
                        System.debug('the request timed out, splitting pdf now');
                        HttpRequest split_pdf_request = new HttpRequest();
                        // String endpoint = 'https://0oinlpnzq4.execute-api.eu-central-1.amazonaws.com/api/';
                        split_pdf_request.setEndpoint('callout:awsSplitPDF' + '/'+ filename);
                        split_pdf_request.setMethod('GET');
                        split_pdf_request.setTimeout(120000);
                        Http split_pdf_http = new Http();
                        // request to split pdf into images
                        HttpResponse split_pdf_response = split_pdf_http.send(split_pdf_request);
                        System.debug('Lambda Resp:' + split_pdf_response.getBody());
                        JSONParser split_pdf_parser = JSON.createParser(split_pdf_response.getBody());
                        List<String> images = new List<String>();
                        while (split_pdf_parser.nextToken() != null) {
                            // Start at the array of images
                            if (split_pdf_parser.getCurrentToken() == JSONToken.START_ARRAY) {
                                while (split_pdf_parser.nextToken() != null) {
                                    if (split_pdf_parser.getCurrentToken() != JSONToken.END_ARRAY && split_pdf_parser.getCurrentToken() != JSONToken.END_OBJECT){
                                        String image = split_pdf_parser.getText();
                                        images.add(image.substring(59,image.length()));
                                        system.debug('Image url ' + image);
                                    }
                                }
                            }
                        }
                        if (images.size() > 0){
                            String[] tokens = images[0].split('\\.(?=[^\\.]+$)');
                            String sec_format = tokens[1];
                            deleteObject(bucket, filename);
                            System.debug('object deleted: ' + filename);
                            results = analyzeObject(sec_format, images[0], bucket);
                            system.debug('results from images from pdf split');
                            deleteObject(bucket, images[0].substring(0, 14 + filename.length()));
                            System.debug('object deleted: ' + images[0].substring(0, 14 + filename.length()));
                            return results;
                        } else {
                            return results;
                        }

                    } else {
                        if (response.getstatuscode() == 200){
                            results = (Map<String, Object>)JSON.deserializeUntyped(response.getBody());
                            deleteObject(bucket, filename);
                            System.debug('object deleted: ' + filename);
                            return results;
                        }
                    }
                }
            } else {
                // Set the body as a JSON object
                string sBody = '{  "filename": "' + filename + '" }';
                request.setBody(sBody);
                system.debug(sBody);
                Http httpLambda = new Http();
                HttpResponse response = httpLambda.send(request);

                System.debug('*Lambda Resp:' + response.getBody());
                if (response.getstatuscode() == 200){
                    results = (Map<String, Object>)JSON.deserializeUntyped(response.getBody());
                    deleteObject(bucket, filename);
                    System.debug('object deleted: ' + filename);
                    return results;
                }
            }
            deleteObject(bucket, filename);
            System.debug('object deleted: ' + filename);
        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
        deleteObject(bucket, filename);
        System.debug('object deleted: ' + filename);
        return results;
    }
    
    //This method is used to post file to AWS
    @AuraEnabled
    public static Map<String,Object> uploadFileToAWS(Id parentId,
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
        String[] tokens = filename.split('\\.(?=[^\\.]+$)');
        String name = tokens[0].replaceAll('[^a-zA-Z0-9\\s+]', '');
        String format = tokens[1];
        filename = name + '.' + format;      
        //AWS specific information
        String bucketname = 'amazontextractbucket'; //AWS bucket name
        String host = 's3.eu-central-1.amazonaws.com'; //'s3.amazonaws.com:443'
        // awsexamplebucket1.us-west-1.s3.amazonaws.com
        String method = 'PUT';
        //String endPoint = 'https://' + bucketname + '.' + host + '/'+ filename;
        system.debug('filename ' + filename );
        HttpRequest req = new HttpRequest();
        req.setMethod(method);
        req.setTimeout(120000);
        req.setEndpoint('callout:amazonTextract'+ '/' + filename);
        req.setHeader('Host', bucketname + '.' + host);
        req.setHeader('Content-Encoding', 'UTF-8');
        req.setHeader('Content-type', fileType);
        req.setHeader('Connection', 'keep-alive');
        req.setHeader('Date', formattedDateString); 
        req.setHeader('ACL', 'public-read-write');
        String body = EncodingUtil.base64Encode(Blob.valueOf(fileContent));
        // req.setHeader('Content-Length', String.valueof(body));
        req.setBodyAsBlob(EncodingUtil.base64Decode(fileContent));
        system.debug('fileContent size ' + fileContent.length());
        // req.setHeader('Content-Length', String.valueOf(fileContent.length()));
        // system.debug('req =' + req.getBody());
        // system.debug('Endpoint='+endPoint);
        system.debug('request '+ req.getEndpoint());
        //finally send information to AWS        
        Http http = new Http();
        Map<String, Object> results = new Map<String,Object>();
        try {
            // request to upload file on bucket
            HTTPResponse res = http.send(req);
            System.debug('*Resp:' + String.ValueOF(res.getBody()));
            System.debug('RESPONSE STRING: ' + res.toString());
            System.debug('RESPONSE STATUS: ' + res.getStatus());
            System.debug('STATUS_CODE: ' + res.getStatusCode());

            if(res.getStatusCode() == 200){
                results = analyzeObject(format, filename, bucketname);
            }
        } catch (DmlException e) {
            System.debug('The following exception has occurred: ' + e.getMessage());
        }
        // Object o = new Object();
        // return o;
        return results;
    }

    

    //This method retrieves Attachment record based on OpportunityId
    @AuraEnabled
    public static List<Attachment__c> displayUploadedFiles(Id parentId){
        return [SELECT Id, File_Name__c, FileURL__c FROM Attachment__c
                WHERE Opportunity__c =:parentId];
    }
}
