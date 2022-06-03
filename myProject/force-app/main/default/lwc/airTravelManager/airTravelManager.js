import { LightningElement, track, wire } from 'lwc';
import retrieveAirports from '@salesforce/apex/AirportsController.retrieveAirports';
import findCoords from '@salesforce/apex/AirportsController.findCoords';
import createRecord from '@salesforce/apex/AirTravelEnergyUseRecordCreator.createRecord';
import {ShowToastEvent} from 'lightning/platformShowToastEvent';
const DELAY = 100;

export default class AirTravelManager extends LightningElement {
    @track showSpinner = false
    @track showModal = false;
    @track showNegativeButton;
    @track showPositiveButton = true;
    @track positiveButtonLabel = 'Save trip to Net Zero';
    @track distance;
    @track returnTrip = false;

    addReturn(event) {
        if (event.target.checked){this.returnTrip = true;}
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

    closeModal() {
        this.showModal = false;
        this.showSpinner = true;
        this.distance = this.findDistance(this.dep_lon, this.dep_lat, this.arr_lon, this.arr_lat)
        try {
            if (dep_airportName != "" && this.arr_airportName != ""){
                this.createEnergyUseRecord();
                // add return trip
                if (this.returnTrip == true) {
                    this.createEnergyUseRecord();
                }
            } else {
                
                this.dispatchEvent(
                    new ShowToastEvent({
                        title: 'Please select the two locations',
                        message: "Could not crate any record",
                        variant: 'error',
                    }),
                );
                
            }
            
        } catch {
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Could not create trip',
                    message: "Could not crate any record",
                    variant: 'error',
                }),
            );
        }
    
    }

    closeModalNoSave(){
        this.showModal = false;
    }
    
    showModalPopup() {
        this.showModal = true;
        this.showPositiveButton = true;
    }
    // handle creation of new trip from scratch
    @track airportList_dep= [];
    @track dep_airportName = "";
    @wire (retrieveAirports,{input:'$dep_airportName'})
    retrieveDep({error, data}){
        if(data){
            this.airportList_dep=data;          
        }
        else if(error){

        } 
    }
    @track airportList_arr= [];
    @track arr_airportName = "";
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
}