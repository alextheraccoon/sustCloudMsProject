import { LightningElement, track } from 'lwc';
import createRecord from '@salesforce/apex/TrainTravelEnergyUseRecordCreator.createRecord';
import {ShowToastEvent} from 'lightning/platformShowToastEvent';


export default class TrainTravelManager extends LightningElement {
    @track priceValue;
    @track showSpinner = false;
    // Handles click on the 'Random greek letter' button
    handleClick() {
        this.showSpinner = true;
        createRecord({price: this.priceValue}).then(result => {
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Success!',
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
                    title: 'Error in creating the record',
                    message: error.message,
                    variant: 'error',
                }),
            );
            this.showSpinner = false;
        });   
        
    }

    handleInputChange(event) {
        this.priceValue = event.detail.value;
    }
}