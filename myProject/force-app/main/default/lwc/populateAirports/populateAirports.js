import { LightningElement, track } from 'lwc';
import getAirportsFrom from '@salesforce/apex/AirportsController.getAirportsFrom';
import {ShowToastEvent} from 'lightning/platformShowToastEvent';

export default class PopulateAirports extends LightningElement {
    @track showSpinner = false;
    @track isPopulated = false;
    // Handles click on the 'Random greek letter' button
    handleClick() {
        this.showSpinner = true;
        getAirportsFrom().then(result => {
            if (result == 1){
                this.dispatchEvent(
                    new ShowToastEvent({
                        title: 'Success!',
                        message: 'You successfully populate Airports!',
                        variant: 'success',
                    }),
                );
                this.showSpinner = false;
                this.isPopulated = true;
            }
            
        }).catch(error => {
            // Error to show during upload
            window.console.log(error);
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Error in populating Airports',
                    message: error.message,
                    variant: 'error',
                }),
            );
            this.showSpinner = false;
        }); 
    
    }

}