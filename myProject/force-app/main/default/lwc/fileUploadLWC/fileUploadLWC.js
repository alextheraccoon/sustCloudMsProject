import { LightningElement, api, track } from 'lwc';
import uploadFileToAWS from '@salesforce/apex/AWSFileUploadController.uploadFileToAWS'; 
import displayUploadedFiles from '@salesforce/apex/AWSFileUploadController.displayUploadedFiles';       
import {ShowToastEvent} from 'lightning/platformShowToastEvent';

export default class fileUploadLWC extends LightningElement {
    @api recordId; //get the recordId for which files will be attached.
    selectedFilesToUpload = []; //store selected files
    @track showSpinner = false; //used for when to show spinner
    @track fileName; //to display the selected file name
    @track tableData; //to display the uploaded file and link to AWS
    file; //holding file instance
    myFile;    
    fileType;//holding file type
    fileReaderObj;
    base64FileData;
    

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

    //this method calls Apex's controller to upload file in AWS
    fileUpload(){
        
        //implicit call to apex
        uploadFileToAWS({ parentId: this.recordId, 
                        strfileName: this.file.name, 
                        fileType: this.file.type,
                        fileContent: this.base64FileData})
        .then(result => {
            console.log('Upload result = ' +result);            
            this.fileName = this.fileName + ' - Uploaded Successfully';
            //call to show uploaded files
            this.getUploadedFiles(); 
            this.showSpinner = false;
            // Showing Success message after uploading
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Success!!',
                    message: this.file.name + ' - Uploaded Successfully!!!',
                    variant: 'success',
                }),
            );
        })
        .catch(error => {
            // Error to show during upload
            window.console.log(error);
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Error in uploading File',
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