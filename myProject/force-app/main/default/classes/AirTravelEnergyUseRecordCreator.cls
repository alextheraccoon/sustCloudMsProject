public with sharing class AirTravelEnergyUseRecordCreator {
    @AuraEnabled
    public static void createRecord(String distance){
        try {
            AirTravelEnrgyUse ateu = new AirTravelEnrgyUse();
            String recordName = 'trip' + system.today().format();
            System.debug(recordName);
            ateu.Name = recordName;
            ateu.SegmentDistance = Decimal.valueOf(distance);
            ateu.StartDate = system.today();
            ateu.EndDate = system.today();

            // Scope3EmssnSrcId = scope 3 emission source
            Scope3EmssnSrc s3es;
            s3es = [SELECT FIELDS(STANDARD) FROM Scope3EmssnSrc
            WHERE Name='test'
            LIMIT 1];
            ateu.Scope3EmssnSrcId = s3es.Id;

            // scope 3 carbon footprint
            Scope3CrbnFtprnt s3cfp;
            s3cfp = [SELECT FIELDS(STANDARD) FROM Scope3CrbnFtprnt
            WHERE Name='test'
            LIMIT 1];
            ateu.Scope3CrbnFtprntId = s3cfp.Id;

            // air travel emission factor
            AirTravelEmssnFctr atef;
            atef = [SELECT Name FROM AirTravelEmssnFctr
            WHERE Name='test'
            LIMIT 1];
            ateu.AirTravelEmssnFctrId = atef.Id;



            insert ateu;

        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
    }
}