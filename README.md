# bulk_item_ingester
Adding physical items by system identifiers (MMS ID and a unique barcode) to ALMA via  API



# Basic usage

There are effectively two users at the moment. One is the library practicioner, one is the script deployer. I hope to merge these roles closer together in time. 

There are a few variables that are set in the scripts to point to some specifc files and locations. I'll list them here and use a shorter vriable name for the rest of the documentation. 

logs_folder - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\logs
spreadsheets_folder - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets
for_processing - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets\for_processing
completed - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets\completed
finished - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets\finished
title_lookup - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\titles_reference.xlsx
template - G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\input_template.xlsx

1. Library practitioner 

This is where the real work happens. 
The librarian starts with a fresh copy of the template spreadsheet. For now, its important that they don't change the order of the columns. 
They might also get a fresh copy of the title_lookup spreadsheet. This includes all the MMS_ids/titles that are already logged in the system.

## The process for adding a new item:

1. Add barcode labels to physical items as needed.
2. Note the description / enumeration information for the item. 
3. Add item to sheet strating with the MMS ID. The MMS ID is the most critical piece of information. Please make sure you have the right one. 
    If there isnt an MMS ID already in the look up for your title, then look on ALMA for the ID. Please make sure you have the right one. 
4. Beep in the barcodes. If you only have one, leave the other blank. 
5. Add in the description/enumeration data as required. These columns reflect how this information is stored  in ALMA. 
6. Repeat as needed for any items you have. Saving the file when you've finished. 
7. Copy or move the spreadsheet to `for_processing`, and rename it to something you can recognise/track. 

## The process for finalising a sheet

When the script as fully processed a spreadsheet, it will move the sheet to the `completed` folder. When your sheet has moved from `for_processing` to `completed` we need to perform any agreed spot checks to make sure nothing is going wrong

If you're not sure, ask your line manager what the current sampling rate is for checking items have been added succesfully. 

1. using the data in the spreadsheet - look up any barcodes, and double check the barcodes exist, 
2. and are associated with the correct record / holding

Possible issues:

a) Sometimes an item gets added twice. ALMA allows this to happen, but adds the 2nd item with no barcode. If you see any items without barcodes, you can withdraw them if you're comfortable they are an error, or email me and I'll check
b) Sometimes the holding IDs get messed up... the ATL holding ID is duplicated as the WGN holding ID. I'm not 100% sure why. You will see both barcodes added to a single holding. From ALMA you can associate them with the right holding, and weither update the titles_lookup, or email me. 
