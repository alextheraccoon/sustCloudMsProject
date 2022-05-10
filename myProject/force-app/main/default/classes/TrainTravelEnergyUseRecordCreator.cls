public with sharing class TrainTravelEnergyUseRecordCreator {
    @AuraEnabled
    public static void createRecord(Decimal price){
        try {
            GroundTravelEnrgyUse gteu = new GroundTravelEnrgyUse();
            String recordName = 'trip' + system.today().format();
            System.debug(recordName);
            gteu.Name = recordName;
            gteu.TripCost = price;
            Schema.DescribeFieldResult F = GroundTravelEnrgyUse.CurrencyCode.getDescribe();
            List<Schema.PicklistEntry> P = F.getPicklistValues();
            for (Schema.PicklistEntry x : P) {
                if (x.getLabel() == UserInfo.getDefaultCurrency()){
                    gteu.CurrencyCode = x.getValue();
                }
            }
            gteu.StartDate = system.today();
            gteu.EndDate = system.today();
            gteu.ExpenseType = 'SubwayCrossState';

            // Scope3EmssnSrcId = scope 3 emission source
            Scope3EmssnSrc s3es;
            s3es = [SELECT FIELDS(STANDARD) FROM Scope3EmssnSrc
            WHERE Name='test'
            LIMIT 1];
            gteu.Scope3EmssnSrcId = s3es.Id;

            // scope 3 carbon footprint
            Scope3CrbnFtprnt s3cfp;
            s3cfp = [SELECT FIELDS(STANDARD) FROM Scope3CrbnFtprnt
            WHERE Name='test'
            LIMIT 1];
            gteu.Scope3CrbnFtprntId = s3cfp.Id;

            // air travel emission factor
            GroundTravelEmssnFctr gtef;
            gtef = [SELECT Name FROM GroundTravelEmssnFctr
            WHERE Name='Scope 3 Ground Travel - EMEA - DEFRA 2021'
            LIMIT 1];
            gteu.GroundTravelEmssnFctrId = gtef.Id;

            insert gteu;

        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
    }
}