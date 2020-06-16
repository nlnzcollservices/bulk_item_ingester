# bulk_item_ingester
Adding physical items by system identifiers (MMS ID and a unique barcode) to ALMA via  API


## Basic usage

There are effectively two users at the moment. One is the library practicioner, one is the script deployer. I hope to merge these roles closer together in time. 

There are a few variables that are set in the scripts to point to some specifc files and locations. I'll list them here and use a shorter variable name for the rest of the documentation. 

    logs_folder - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\logs
    spreadsheets_folder - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets
    for_processing - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets\for_processing
    completed - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets\completed
    finished - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets\finished
    title_lookup - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\titles_reference.xlsx
    template - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\input_template.xlsx

and finally, 

    secrets = c:\sources\secrets

This is a special file - its so we can share code without exposing each others API keys internally, or publically. 

The file can live anywhere - its just a text file. 

Make sure to add the following 3 lines, replacing the my_api_key string with your valid ALMA api keys:

    [configuration]
    PRODUCTION = my_production_key_key
    SANDBOX = my_sandbox_api_key


### 1. Library practitioner 

This is where the real work happens. 
The librarian starts with a fresh copy of the `template` spreadsheet. For now, its important that they don't change the order of the columns. 
They might also get a fresh copy of the title_lookup spreadsheet. This includes all the MMS_ids/titles that are already logged in the system.

#### The process for adding a new item:

1. Add barcode labels to physical items as needed.
2. Note the description / enumeration information for the item. 
3. Add item to sheet strating with the MMS ID. The MMS ID is the most critical piece of information. Please make sure you have the right one. 
    If there isnt an MMS ID already in the look up for your title, then look on ALMA for the ID. Please make sure you have the right one. (See later on for how this works)
4. Beep in the barcodes. If you only have one, leave the other blank. 
5. Add in the description/enumeration data as required. These columns reflect how this information is stored  in ALMA. 
6. Repeat as needed for any items you have. Saving the file when you've finished. 
7. Copy or move the spreadsheet to `for_processing`, and rename it to something you can recognise/track. 

#### The process for finalising a sheet

When the script as fully processed a spreadsheet, it will move the sheet to the `completed` folder. When your sheet has moved from `for_processing` to `completed` we need to perform any agreed spot checks to make sure nothing is going wrong

If you're not sure, ask your line manager what the current sampling rate is for checking items have been added succesfully. 

1. using the data in the spreadsheet - look up any barcodes, and double check the barcodes exist, 
2. and are associated with the correct record / holding

#### Possible issues:

a) Sometimes an item gets added twice. ALMA allows this to happen, but adds the 2nd item with no barcode. If you see any items without barcodes, you can withdraw them if you're comfortable they are an error, or email me and I'll check
b) Sometimes the holding IDs get messed up... the ATL holding ID is duplicated as the WGN holding ID. I'm not 100% sure why. You will see both barcodes added to a single holding. From ALMA you can associate them with the right holding, and weither update the titles_lookup, or email me. 

## 2. Script deployer

[This is beta. Things will change]

There one primary script `add__items_beta.py`

It doesn't need any arguments - everything is hardcoded per the above locations. 

It can be run from `cmd` (`c:\bulk_ingester_folder>python add__items_beta.py`) or and IDE. I have noticed it seems to be slighty less stable via `cmd`, but that could be my build... 

The script runs and dumps a basic text log of each items outcome to terminal. There is a more noisy logger, accessed by setting the variable `verbose` to `True`. There is also a few log files made in the `logs` folder. `full_audit` captures every interaction outcome, useful for debugging. `success` logs only items that it has succesfully added, used by processing scripts to speed up repeat processing of a sheet.  

Watch the logger, its not unusual for one item to take 10 mins to update. This down to the API call, and should be sorted out in the June 2020 release.

It should 'fail' to add an item gracefully. If it has a problem with an item it eventually gives up, and moves on.

Once its checked all the items on a list, it checks how many barcodes it started with, and how many its logged as sucesssful, and updates to terminal. This is also the process that triggers the move of the whole spreadsheet to `completed` if all the items are added. 

While the sheet resides in the `for_processing` folder, and the script is triggered, each sheet is processed 3 times. This is a result of the slow API. Sometimes the item is added, but we don't get a clean `200` reply from ALMA. In this case, we park the item for now, and move on. Running sheet 3 times helps to clear up these partially complete items. As soon as the sheet is moved (through being fully completed) it moves on anyway. 

Worst case for a processing call is that the API fails to return, and the item doesn't get added. This is rare, but happens on occasions. This is best addressed by adding the MMS ID to the file `mms_time_out_skip_list.txt` put one MMS ID on one line. Any item that uses an MMS ID found in this file will not have an attempt made to process that item. Its worth periodically turning this off and seeing if the items go through. Sometimes it just works...

This means that any sheets that contain items in the skip list will remain in the `for_processing` until the situation is fixed. The sheet will be picked up for processing, but all the skipped items will not be processed. All other items will be. It is therefor recommended that problem items are split out into their own spreadsheet. 

### Process steps

This is the basic workflow, and sub processes that are used. 

#### Main process

1. Make list of all workbooks in the `for_processing` folder. Process one by one. 
2. Check if a `success` log exists for that workbook filename. If yes, collect all the barcodes that are logged as successful.
3. Read each row of sheet. check each barcode. If already seen (found via parsing the `success` log) skip barcode.
4. If new barcode, get mms id from sheet and look it up in the `title_lookup` item. If not found, do missing MMS process. 
5. Create data object, using the template xml file.
6. Check if barcode exists in ALMA - if no, add new item
7. Check item has been updated (this a product of the API "make new item" call being a bit funny. Some data is overwritten in the first pass, so it needs a 2nd pass to update. I'm checking the "policy" value in the object data item. If its blank, it needs to be updated. 
8. Log outcome to file. Any transaction in to `full_audit` and successes into ` success`, and errors into errors. 
9. Log outcome to screen, depending on setting (verbose / not verbose)
10. Add barcode to success list
11. When all rows processed, check if all barcodes are now succesfull. If yes move spreadsheet to `completed'  

#### Missing MMS
This is a sub routine that added new titles to the look up. 

Needs to know an MMS ID, and if its PROD or SANDBOX. 

1. Get the record from ALMA. 
2. From the record, pick up the POL
3. From the record pick up either of the two holding IDs from the location data item.
4. Add new line to title_lookup. 
5. Move current title_lookup xlsx file to backups location, renaming with todays date
6. Save new title_lookup to include new row. 
