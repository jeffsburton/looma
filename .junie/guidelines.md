# Project Guidelines
    
* Primevue form components TextInput, TextArea, and Select should be wrapped in FloatLabel variant="on"

* On the frontend, all fetch calls should be wrapped in the api wrapper found in api.js

* when a form type UI is loaded, there should be no changes to the database unless iniated by the user. 

* All api endpoint return payloads should be wrapped in pydantic schemas that enforce encryption of database id's. 