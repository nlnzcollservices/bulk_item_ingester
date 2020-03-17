import requests
from tools.title_ref_updater import update_titles
from tools.title_lookup import titles_lookup, add_new_title_to_spreadsheet
import configparser
import shutil
import os

secret_file = r"c:\source\secrets"
config = configparser.ConfigParser()
config.read(secret_file)
prod_key = config.get("configuration", "PRODUCTION")
sand_key = config.get("configuration", "SANDBOX") 
print ()

class Master_Data(object):
    def __init__(self):
        self.mms_timeout_skip_list = self.get_mms_timeout_skip_list()
        self.api_key = None
        self.system = None
        self.titles_lookup = {} 

    def get_mms_timeout_skip_list(self):
        with open("mms_time_out_skip_list.txt") as data:
            return [int(x) for x in data.read().split("\n") if x != ""]
            # return []

    def set_prod(self, set_prod=False):
        """ PROD / SANDBOX switcher
        for API key management
        for title lookup - (mms / holding ids etc) """
        if set_prod:
            self.api_key = prod_key
            self.system = "PROD"
            self.titles_lookup = titles_lookup[self.system]
        else:
            self.api_key = sand_key
            self.system = "SAND"
            self.titles_lookup = titles_lookup[self.system]

master = Master_Data()

def barcode_in_alma(barcode):
    """checks if ALMA has seen this barcode before
    returns True/False"""
    if verbose:
        print (f"Checking if {barcode} is in ALMA")
    if "No items found for barcode" in requests.get(f'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/items?item_barcode={barcode}&apikey={master.api_key}').text:
        return False
    else:
        return True

def get_item_by_barcode(barcode):
    return requests.get(f'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/items?item_barcode={barcode}&apikey={master.api_key}').text

def get_done_barcodes():
    with open(r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets\testing\done.txt") as data:
        dones = [x for x in data.read().split("\n") if x != ""]
    return dones

def find_spreadsheet_from_logs(barcode):
    folder = r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\log_files"

    files = os.listdir(folder)
    for f in [x for x in files if x != "archive"]:
        my_file = os.path.join(folder, f)

        with open (my_file) as data:
            lines = data.read().split("\n")
            for line in [x for x in lines if x != ""]:
                if str(barcode) in line.lower():
                    print (f)


def add_to_done(barcode):
    with open(r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets\testing\done.txt", 'a') as data:
        data.write(f"{barcode}\n")

def get_barcodes_from_file(my_file):
    with open(my_file) as data:
        barcodes = data.read().split("\n")
    return barcodes

def get_barcodes_that_are_processed():
    barcodes = []
    folder = r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\log_files"

    files = [x for x in os.listdir(folder) if "success" in x]
    for f in files:
        my_file = os.path.join(folder, f)

        with open (my_file) as data:
            lines = data.read().split("\n")
            for line in [x for x in lines if x != ""]:
                parts = line.split(" | ")
                barcodes.append(parts[5])
    return barcodes


master.set_prod(True)
verbose = False
done = get_done_barcodes()

print ("Already checked: ", len (done))
processed_barcodes = get_barcodes_that_are_processed()


barcodes_file = r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets\testing\WN_barcode_test.txt"

barcodes_to_check = get_barcodes_from_file(barcodes_file)  
for barcode in barcodes_to_check:
    
    if barcode not in done and barcode != '': 
        in_alma = barcode_in_alma(barcode)
        seen = barcode in processed_barcodes

        print (f"{barcode} - in success list: {seen} - in ALMA: {in_alma }")
        if not seen or not in_alma:
            print (f"\t\t\t\t\t\t\t\t\t\t\t - {barcode}")

            find_spreadsheet_from_logs(barcode)
            print()

        add_to_done(barcode)


print ("Processed:", len(processed_barcodes), "barcodes")


# find_spreadsheet_from_logs(74444000286597)
# find_spreadsheet_from_logs(74444000286593)
# find_spreadsheet_from_logs(74444000286595)
# find_spreadsheet_from_logs(74444000286596)
# find_spreadsheet_from_logs(74444000286599)

# find_spreadsheet_from_logs(32222000926870)
# find_spreadsheet_from_logs(32222000960552)


find_spreadsheet_from_logs(994622103502836)