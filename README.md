# bulk_item_receiver
Adding physical items to Alma via API, including designations and barcodes.


## Basic usage

There are effectively two user roles at the moment:

1. librarian practitioner
2. script deployer

There are a few variables that are set in the scripts to point to specific files and locations. These are listed below, with the shorter variable names used for the rest of the documentation.

<!--- What is the difference b/w 'finished' and 'completed'? AJ --->

    logs_folder - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk_item_receiver\logs
    spreadsheets_folder - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk_item_receiver\spreadsheets
    for_processing - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk_item_receiver\spreadsheets\for_processing
    completed - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk_item_receiver\spreadsheets\completed
    finished - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk_item_receiver\spreadsheets\finished
    title_lookup - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk_item_receiver\titles_reference.xlsx
    input_template - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk_item_receiver\input_template.xlsx

and finally, 

    secrets = c:\sources\secrets

This is a text file that the script deployer saves locally so that sensitive credentials like API keys are not shared. 

Make sure to add the following 3 lines to your personal 'secrets' file, replacing the `my_api_key` string with your own valid ALMA API keys:

    [configuration]
    PRODUCTION = my_production_key_key
    SANDBOX = my_sandbox_api_key


### 1. Librarian practitioner 

This is where the real work happens. 
The librarian starts with a fresh copy of the `input_template` spreadsheet. **IMPORTANT: DO NOT** change the order of the columns. 
They might also get a fresh copy of the `title_lookup` spreadsheet. This includes all the titles and their MMS IDs that are already logged in this system. <!---- Why 'might'? AJ --->

#### Building a spreadsheet of new items to add

<!-- there's nothing here about checking whether an item has already been received, missed issues, etc. AJ-->

1. Add barcode labels to physical items as needed. <!--For clarity, do we need to talk about any other marking and stamping here? AJ-->
2. Note the description / enumeration information for the item. 
3. Add the item to your copy of the `input_template` sheet, starting with the Alma MMS ID. The MMS ID is the most critical piece of information, so please make sure you have the right one. 
    If there isn't an MMS ID already in the `title_lookup` for your title, then look on Alma for the ID. Please make sure you have the right one. (See later on for how this works)
4. Scan in the barcodes. If you are only receiving one copy of an issue, leave the cell for the unrequired barcode blank. <!--Does this mean 'use a barcode scanner to add the barcodes to the appropriate cell in the input spreadsheet'? AJ-->
5. Add in the description/enumeration data as required, leaving cells blank where they are not required for the designation on the item. <!--Are there any rules here that the librarian needs to know about? AJ-->
6. Repeat as needed for all the items you want to receive. Save the file when you've finished. 
7. Copy or move the spreadsheet to `for_processing`, and rename it to something you can recognise/track. 

#### After your spreadsheet has been processed

When the script has fully processed your spreadsheet, it will move it to the `completed` folder. When your sheet has moved from `for_processing` to `completed`, you need to perform any agreed spot checks to make sure nothing is going wrong

If you're not sure, ask your line manager what the current sampling rate is for checking items have been added successfully. <!--What is the current sampling rate?! line manager--> Using the data in the spreadsheet, look up some of the barcodes in Alma, and double check that they exist and are associated with the correct record and holding.

##### Possible issues

a) Sometimes an item gets added twice. ALMA allows this to happen, but adds the 2nd item with no barcode. If you see any items without barcodes, you can withdraw them if you're comfortable they are an error, or email me and I'll check<!--Where would you see this? AJ-->
b) Sometimes the holding IDs get messed up... the ATL holding ID is duplicated as the WGN holding ID. I'm not 100% sure why. You will see both barcodes added to a single holding. From ALMA you can associate them with the right holding, and either update the titles_lookup, or email me. <!--Where would you see this? AJ-->

### 2. Script deployer

[This is beta. Things will change] <!--what need to happen to move from beta? AJ-->

#### Overview

There is one primary script: `add__items_beta.py`

It doesn't need any arguments. Everything is hardcoded with the locations listed above. 

It can be run from `cmd` (`c:\bulk_ingester_folder>python add__items_beta.py`) or an IDE. NB: it seems to be slightly less stable via `cmd`. <!--What does 'stable' mean in this context? AJ-->

The script runs and prints a basic text log of each item's outcome to terminal. There is a more noisy logger, accessed by setting the variable `verbose` to `True`. There is also a few log files made in the `logs` folder. `full_audit` is useful for debugging as it captures every interaction outcome. `success` logs only items that it has successfully added; it is used by the processing script itself to speed up repeat processing of a partially-completed sheet.

Watch the logger, its not unusual for one item to take 10 mins to update. This down to the API call, and should be sorted out in the June 2020 release.<!--Has it been sorted? AJ-->

When the script is triggered, at will attempt to process any sheet in the `for_processing` folder three times. This is required due to the slow API. Sometimes the item is added, but we don't get a clean `200` reply from ALMA. In this case, we park the item for now, and move on. Running each sheet three times helps to clear up these partially completed items. 

The script should 'fail' to add an item gracefully. If it has a problem with an item it eventually gives up and moves on.

Once it has checked all the items on in an input spreadsheet, it checks how many barcodes it started with, and how many it has logged as 'successful', and updates to terminal <!--what does 'updates to terminal' mean here? AJ-->. This is also the process that triggers the move of the whole spreadsheet to the `completed` directory if all the items have been added. 

Worst case for a processing call is that the API fails to return, and the item doesn't get added. This is rare, but happens on occasions. This is best addressed by adding the MMS ID to the file `mms_time_out_skip_list.txt`  (add one MMS ID per line). Any item that uses an MMS ID found in this file will not have an attempt made to process that item. <!--then what happens to the item? AJ--> It's worth periodically turning this off <!--how? AJ--> and seeing if the items go through. Sometimes it just works...

This means that any sheets that contain items in the skip list will remain in `for_processing` until the situation is fixed. The sheet will be picked up for processing, but all the skipped items will not be processed. All other items will be. It is therefore recommended that problem items are split out into their own spreadsheet. 

#### Process steps

This is the basic workflow, and sub processes that are used. 

##### Main process

The script carries out the following steps:

1. Make list of all workbooks in the `for_processing` folder. Then process them one by one. 
2. For a workbook: check if a `success` log exists for that workbook filename. If yes, collect all the barcodes that are logged as successful. <!--make a list?-->
3. Read each row of sheet. Check each barcode. If barcode is in the `success` log, it has already been processed and will be skipped.
4. If barcode has not already been successfully processed, get MMSID from row and look it up in the `title_lookup` sheet. If not found, do [missing MMS](#missing-mms) process.
5. Create data object, using the template xml file. <!--is this an Alma Item object?-->
6. Check if barcode exists in ALMA - if no, add new item
7. Check item has been updated. This is required because the "make new item" API call is a bit funny: some data is overwritten in the first pass, so it needs a second pass to update. This is determined by checking the "policy" value in the object data item: if its blank, the item needs to be updated. 
8. Log outcome to file. Log all transactions to `full_audit`, successes to `success`, and errors to `errors`. 
9. Print outcome to screen, depending on setting (verbose / not verbose).
10. Add barcode to `success` list.
11. When all rows have been processed, check if all barcodes are now successful. If yes, move spreadsheet to `completed` directory.

##### Missing MMS
This is a sub routine that adds new titles to the `look up`. 

Requires the MMS ID of the new title to add, and whether it is in Alma PROD or SANDBOX. 

1. Get the record from ALMA. 
2. From the record, get the POL
3. From the record, get either of the two holding IDs from the location data item. <!--does this mean it only gets one? AJ-->
4. Add new line to `title_lookup`. 
5. Move current title_lookup.xlsx file to backups location, renaming with today's date.
6. Save new `title_lookup` to include new row. 
