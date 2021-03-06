import { LightningElement, api, wire, track} from 'lwc';
import retrieveAirports from '@salesforce/apex/AirportsController.retrieveAirports';
import findCoords from '@salesforce/apex/AirportsController.findCoords';
import uploadFileToAWS from '@salesforce/apex/AWSFileUploadController.uploadFileToAWS'; 
import checkRegion from '@salesforce/apex/IsSameRegion.checkRegion';
import displayUploadedFiles from '@salesforce/apex/AWSFileUploadController.displayUploadedFiles';  
import createRecord from '@salesforce/apex/AirTravelEnergyUseRecordCreator.createRecord';     
import {ShowToastEvent} from 'lightning/platformShowToastEvent';
const DELAY = 100;
export default class fileUploadLWC extends LightningElement {
    @api recordId; //get the recordId for which files will be attached.
    selectedFilesToUpload = []; //store selected files
    @track showSpinner = false; //used for when to show spinner
    @track fileName; //to display the selected file name
    @track tableData; //to display the uploaded file and link to AWS
    @track showModal = false;
    @track showNegativeButton;
    @track showPositiveButton = true;
    @track positiveButtonLabel = 'Save trip to Net Zero';
    @track distance;
    @track startPoint = "";
    @track endPoint = "";
    @track possibleRoutes = [];
    @track all_airports = []
    @track more_options = false;
    @track returnTrip = false;
    @track analyzedAirports = [];
    @track wrongTrip = false;

    @track airportList_dep= [];
    @track dep_airportName = "";
    @track airportList_arr= [];
    @track arr_airportName = "";


    file; //holding file instance
    myFile;    
    fileType;//holding file type
    fileReaderObj;
    base64FileData;
    responseData;
    selectedDepartureValue = "";
    selectedDestinationValue = "";

    // handle creation of new trip from scratch
    
    @wire (retrieveAirports,{input:'$dep_airportName'})
    retrieveDep({error, data}){
        if(data){
            this.airportList_dep=data;          
        }
        else if(error){

        } 
    }
    
    @wire (retrieveAirports,{input:'$arr_airportName'})
    retrieveArr({error, data}){
        if(data){
            this.airportList_arr=data;          
        }
        else if(error){

        } 
    }
    dep_lat = 0
    dep_lon = 0
    arr_lat = 0
    arr_lon = 0
    handleGetSelectedDeparture(event){
        console.log(event.target.value);
        this.dep_airportName = event.target.value;
        findCoords({name: this.dep_airportName}).then(result => {
            console.log(result)
            
            let x = result.split(',');
            this.dep_lat = parseFloat(x[0])
            this.dep_lon = parseFloat(x[1])
            // console.log(lat)
            // console.log(lon)
        })
        
    }
    handleGetSelectedArrival(event){
        console.log(event.target.value);
        this.arr_airportName = event.target.value;
        findCoords({name: this.arr_airportName}).then(result => {
            console.log(result)
            
            let x = result.split(',');
            this.arr_lat = parseFloat(x[0])
            this.arr_lon = parseFloat(x[1])
            // console.log(lat)
            // console.log(lon)
        })
    }

    searchDeparture(event) {
        // this.searchValue = event.target.value;
        const searchString = event.target.value;
        window.clearTimeout(this.delayTimeout);
        this.delayTimeout = setTimeout(() => {
            this.dep_airportName = searchString; 
        }, DELAY);
    }

    searchArrival(event) {
        // this.searchValue = event.target.value;
        const searchString = event.target.value;
        window.clearTimeout(this.delayTimeout);
        this.delayTimeout = setTimeout(() => {
            this.arr_airportName = searchString; 
        }, DELAY);
    }
    

    handleOnselectDeparture(event) {
        this.selectedDepartureValue = event.detail.value;
    }

    handleOnselectDestination(event) {
        this.selectedDestinationValue = event.detail.value;
    }

    addReturn(event) {
        if (event.target.checked){this.returnTrip = true;}
    }
    

     // get the file name from the user's selection
     handleSelectedFiles(event) {
        if(event.target.files.length > 0) {
            this.selectedFilesToUpload = event.target.files;
            this.fileName = this.selectedFilesToUpload[0].name;
            this.fileType = this.selectedFilesToUpload[0].type;
            console.log('fileName=' + this.fileName);
            console.log('fileType=' + this.fileType);
        }
    }
    
    //parsing the file and prepare for upload.
    handleFileUpload(){
        if(this.selectedFilesToUpload.length > 0) {
            this.showSpinner = true;
            
            this.file = this.selectedFilesToUpload[0];
            //create an intance of File
            this.fileReaderObj = new FileReader();

            //this callback function in for fileReaderObj.readAsDataURL
            this.fileReaderObj.onloadend = (() => {
                //get the uploaded file in base64 format
                let fileContents = this.fileReaderObj.result;
                fileContents = fileContents.substr(fileContents.indexOf(',')+1)
                
                //read the file chunkwise
                let sliceSize = 1024;           
                let byteCharacters = atob(fileContents);
                let bytesLength = byteCharacters.length;
                let slicesCount = Math.ceil(bytesLength / sliceSize);                
                let byteArrays = new Array(slicesCount);
                for (let sliceIndex = 0; sliceIndex < slicesCount; ++sliceIndex) {
                    let begin = sliceIndex * sliceSize;
                    let end = Math.min(begin + sliceSize, bytesLength);                    
                    let bytes = new Array(end - begin);
                    for (let offset = begin, i = 0 ; offset < end; ++i, ++offset) {
                        bytes[i] = byteCharacters[offset].charCodeAt(0);                        
                    }
                    byteArrays[sliceIndex] = new Uint8Array(bytes);                    
                }
                
                //from arraybuffer create a File instance
                this.myFile =  new File(byteArrays, this.fileName, { type: this.fileType });
                
                //callback for final base64 String format
                let reader = new FileReader();
                reader.onloadend = (() => {
                    let base64data = reader.result;
                    this.base64FileData = base64data.substr(base64data.indexOf(',')+1); 
                    this.fileUpload();
                });
                reader.readAsDataURL(this.myFile);                                 
            });
            this.fileReaderObj.readAsDataURL(this.file);            
        }
        else {
            this.fileName = 'Please select a file to upload!';
        }
    }

    createEnergyUseRecord() {
        createRecord({distance : this.distance}).then(result => {
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Success!!',
                    message: 'Record cretaed successfully!',
                    variant: 'success',
                }),
            );
            this.showSpinner = false;
        }).catch(error => {
            // Error to show during upload
            window.console.log(error);
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Error in creating record',
                    message: error.message,
                    variant: 'error',
                }),
            );
            this.showSpinner = false;
        });

    }
    @track error_message = "Please select the missing fields"
    @track show_error_message = false;
    closeModal() {
        
        this.showSpinner = true;
        if (this.more_options == true) {
            try {
                // handle multiple choice
                if (this.selectedDepartureValue != "" && this.selectedDestinationValue != ""){
                    
                    let points = [this.selectedDepartureValue, this.selectedDestinationValue];
                
                    if (this.more_options == true) {

                        for (let i = 0; i < this.possibleRoutes.length ; ++i){
                            if (JSON.stringify(this.possibleRoutes[i][1]) === JSON.stringify(points)){
                                this.distance = this.possibleRoutes[i][0]
                            }
                        }
                    }

                    window.console.log("return variable " + this.returnTrip)
                    // add return trip
                    if (this.wrongTrip == false){
                        this.createEnergyUseRecord();
                        if (this.returnTrip == true) {
                            this.createEnergyUseRecord();
                        }
                        this.showModal = false;
                    } else {
                        if (this.dep_airportName != "" && this.arr_airportName != ""){
                            this.distance = this.findDistance(this.dep_lon, this.dep_lat, this.arr_lon, this.arr_lat)
                            this.createEnergyUseRecord();
                            this.show_error_message = false
                            // add return trip
                            if (this.returnTrip == true) {
                                this.createEnergyUseRecord();
                            }
                            this.showModal = false;
                            this.wrongTrip = false;
                            airportList_dep= [];
                            dep_airportName = "";
                            airportList_arr= [];
                            arr_airportName = "";
                        } else {
                            this.show_error_message = true
                        }
                    }
                    
                    this.more_options = false;
                    this.selectedDepartureValue = "";
                    this.selectedDestinationValue = "";
                    this.all_airports = [];
                    this.analyzedAirports = [];
                    this.show_error_message = false;
                } else {
                    this.show_error_message = true;
                }
            } catch (error) {
                console.log(error)
            }
        } else {
            try {
                if (this.wrongTrip == true){
                    
                    if (this.dep_airportName != "" && this.arr_airportName != ""){
                        this.distance = this.findDistance(this.dep_lon, this.dep_lat, this.arr_lon, this.arr_lat)
                        this.createEnergyUseRecord();
                        this.show_error_message = false
                        // add return trip
                        if (this.returnTrip == true) {
                            this.createEnergyUseRecord();
                        }
                        this.showModal = false;
                        this.wrongTrip = false;
                        airportList_dep= [];
                        dep_airportName = "";
                        airportList_arr= [];
                        arr_airportName = "";
                    } else {
                        this.show_error_message = true
                    }
                } else if (this.startPoint != "" && this.endPoint != ""){
                    // add return trip
                    this.createEnergyUseRecord();
                    if (this.returnTrip == true) {
                        this.createEnergyUseRecord();
                    }
                    this.showModal = false;
                } else {
                    this.show_error_message = true
                }
            } catch (error) {
                console.log(error)
            }
        }
    }

    closeModalNoSave(){
        this.showModal = false;
        this.more_options = false;
        this.selectedDepartureValue = "";
        this.selectedDestinationValue = "";
        this.all_airports = [];
        this.analyzedAirports = [];
    }
    
    showModalPopup() {
        this.showModal = true;
        this.showPositiveButton = true;
    }

    correctTrip() {
        this.wrongTrip = true;
    }

    findDistance(y1,x1, y2,x2){
        let R = 3958.76
        y1 *= Math.PI/180.0
        x1 *= Math.PI/180.0
        y2 *= Math.PI/180.0
        x2 *= Math.PI/180.0

        let x = Math.sin(y1) * Math.sin(y2) + Math.cos(y1) * Math.cos(y2) * Math.cos(x2 - x1)
        if (x >1) {
            x = 1
        }
        return Math.acos(x) * R
    }
    

    //this method calls Apex's controller to upload file in AWS
    fileUpload(){
        
        //implicit call to apex
        uploadFileToAWS({ parentId: this.recordId, 
                        strfileName: this.file.name, 
                        fileType: this.file.type,
                        fileContent: this.base64FileData})
        .then(result => {
            console.log('Upload result = ' +result); 
            this.responseData = JSON.parse(result['body']); 
            window.console.log(this.responseData)
            this.distance = this.responseData['Distance']
            this.startPoint = this.responseData['StartPoint']
            this.endPoint = this.responseData['EndPoint']
            this.possibleRoutes = this.responseData['PossibleRoutes']
            // console.log();
            if (this.responseData['PossibleRoutes'].length > 0){
                this.more_options = true
                // here handle the possible routes
                window.console.log(this.possibleRoutes)

                window.console.log(this.responseData['PossibleRoutes'])
                window.console.log(this.responseData['StartPoint'])
                for (let i = 0; i < this.responseData['PossibleRoutes'].length; ++i) {
                    let airports = this.responseData['PossibleRoutes'][i][1]
                    if (this.all_airports.includes(airports[0]) == false) {
                        this.all_airports.push(airports[0])
                    }
                    if (this.all_airports.includes(airports[1]) == false) {
                        this.all_airports.push(airports[1])
                    }
                }
                window.console.log(this.all_airports)
                // index the list based on region
                checkRegion({locations: this.all_airports}).then(result => {
                    console.log('analysis result = ' +result); 
                    let locs = result['locations']; 
                    for (let i = 0; i < locs.length; ++i) {
                        if (locs[i][1] == true && this.analyzedAirports.includes(locs[i][0]) == false) {
                            this.analyzedAirports.push(locs[i][0])
                        }
                    }
                    for (let i = 0; i < locs.length; ++i) {
                        if (this.analyzedAirports.includes(locs[i][0]) == false ) {
                            this.analyzedAirports.push(locs[i][0])
                        }
                    }
                    this.fileName = this.fileName + ' - Uploaded Successfully';
                    this.showSpinner = false;
                    // Showing Success message after uploading
                    this.showModalPopup();
                }).catch(error => {
                    // Error to show during upload
                    window.console.log(error);
                    this.dispatchEvent(
                        new ShowToastEvent({
                            title: 'There has been an error, please try again',
                            message: error.message,
                            variant: 'error',
                        }),
                    );
                    this.showSpinner = false;
                });

            } else {
                this.fileName = this.fileName + ' - Uploaded Successfully';
                this.showSpinner = false;
                // Showing Success message after uploading
                this.showModalPopup();
            }
            
        })
        .catch(error => {
            // Error to show during upload
            window.console.log(error);
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Error in reading the File',
                    message: error.message,
                    variant: 'error',
                }),
            );
            this.showSpinner = false;
        });        
    }

    
    //retrieve uploaded file information to display to the user
    getUploadedFiles(){
        displayUploadedFiles({parentId: this.recordId})
        .then(data => {
            this.tableData = data;
            console.log('tableData=' + this.tableData);
        })
        .catch(error => {
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Error in displaying data!!',
                    message: error.message,
                    variant: 'error',
                }),
            );
        });
    }
}


// -- (SUM(travel_count)) AS "travel_c", (SUM(travel_emissions)) AS "emissions", (SUM(avg_emission)) AS "avg"
// -- FROM (
// -- UNION ALL
// -- SELECT COUNT(*) as "travel_count", SUM("Scope3EmissionsInTco2e") AS "travel_emissions", SUM("Scope3EmissionsInTco2e")/COUNT(*) as "avg_emission" FROM "TravelEnergyUse") 