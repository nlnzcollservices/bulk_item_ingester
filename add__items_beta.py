import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup
from pprint import pprint
from openpyxl import Workbook, load_workbook
import tools.description_maker as description_maker
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
	"""Holds the master data items  / vars that are used through out the process."""
	def __init__(self):
		# self.mms_timeout_skip_list = self.get_mms_timeout_skip_list()
		self.mms_timeout_skip_list = []
		self.api_key = None
		self.system = None
		self.titles_lookup = {} 

	def get_mms_timeout_skip_list(self):
		"""List of titles that are blocked at MMS id level due to the API slowness bug"""
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

class Item(object):
	"""Holds all the tracking and data items for a single item - across both holdings"""
	def __init__(self):
		self.record_dict = {
					"WN":{"holding_id":"", "barcode":"", "policy_id":"STANDARD"}, 
					"ATL": {"holding_id":"", "barcode":"", "policy_id":"HERITAGE"},
					"po_line_id":"",
					"mms_id":"",
					"internal_note_1":"", 
					"public_note":"",
					"receiving_operator":"gattusoj_API",
					"description":"",
					"chron_i":"",
					"chron_j":"",
					"chron_k":"",
					"enum_a":"",
					"enum_b":"",
					"enum_c":"", 
					"title":""
					}

		self.dup = False
		self.success = False
		self.failed = False
		self.new_title = False
		self.checked_title = False
		self.processed_previously = False
		self.process_item = True
		self.valid_wn_barcode = True
		self.valid_atl_barcode = True		

class Logger(object):
	"""holds all the logger parts for a processing run
	manages the full audit - a comprehensive log of all interactions with a spreadsheet
	manages the 'this_run' log - a record of all processing attempts at an item level for each run. 
	manages the 'existing_log_data' - a record of all items that have been logged as successful. 
	manages the 'new_titles' list - a record of all new titles that require a human check before sign off
	manages the checking process that checks if all barcodes have been processed, and the sheet can be moved to the completed folder"""

	def __init__(self, name, log_root):
		self.log_root = log_root
		if not os.path.exists(self.log_root):
			os.mkdir(self.log_root)
		self.audit = os.path.join(self.log_root, name.replace(".txt","_full_audit.txt"))
		self.successfully_added = os.path.join(self.log_root, name.replace(".txt",f"_success.txt")) 
		self.dup_log_file = os.path.join(self.log_root, name.replace(".txt",f"_dup.txt"))
		self.bad_item_file = os.path.join(self.log_root, name.replace(".txt",f"_bad_item.txt"))
		self.unknown_error_file = os.path.join(self.log_root, name.replace(".txt",f"_unknown_error.txt"))

		self.items = []
		self.new_titles = []
		self.existing_log_data = []
		self.checks_needed = []
		self.succesful = []
		self.found_barcodes = []
		self.existing_log_data = []
		self.completed = False 
		self.dumped = False
		self.preflight_check = False
		self.get_exisiting_succesfuls_from_logs()


	def log_successful_item(self, mms_id, holding_id, description, barcode, item_id, item_url):
		self.succesful.append(str(barcode))
		item = {'mms_id':mms_id,
			'system':master.system,
			'holding_id':holding_id,
			'barcode':barcode,
			'description':description}

		if item['mms_id'] not in self.existing_log_data:
			with open(self.successfully_added, 'a') as data:
				data.write(f"{mms_id} | {master.titles_lookup[item['mms_id']]['title']} | {item['system']} | {item['holding_id']} | {item_id} | {barcode} | {description}\n")
		with open(self.audit, 'a') as data:
			data.write(f"{mms_id} | {master.titles_lookup[item['mms_id']]['title']} | {item['system']} | {item['holding_id']} | {item_id} | {barcode} | {description} | Outcome: Added OK\n")

	def log_dup_item(self, mms_id, holding_id, description, barcode):
		self.succesful.append(str(barcode))
		item = {'mms_id':mms_id,
			'system':master.system,
			'holding_id':holding_id,
			'barcode':barcode,
			'description':description}

		if item['mms_id'] not in self.existing_log_data:
			with open(self.dup_log_file, 'a') as data:
				data.write(f"{mms_id} | {master.titles_lookup[item['mms_id']]['title']} | {item['system']} | {item['holding_id']} | {barcode} | {description}\n")
		with open(self.audit, 'a') as data:
			data.write(f"{mms_id} | {master.titles_lookup[item['mms_id']]['title']} | {item['system']} | {item['holding_id']} | {barcode} | {description} | Outcome: Dup barcode\n")

	def log_bad_item(self, mms_id, holding_id, description, barcode):
		item = {'mms_id':mms_id,
			'system':master.system,
			'holding_id':holding_id,
			'barcode':barcode,
			'description':description}

		if item['mms_id'] not in self.existing_log_data:
			with open(self.bad_item_file, 'a') as data:
				data.write(f"{mms_id} | {master.titles_lookup[item['mms_id']]['title']} | {item['system']} | {item['holding_id']} | {barcode} | {description}\n")
		with open(self.audit, 'a') as data:
			data.write(f"{mms_id} | {master.titles_lookup[item['mms_id']]['title']} | {item['system']} | {item['holding_id']} | {barcode} | {description} | Outcome: Bad Holding ID\n")

	def log_unknown_item_error(self, mms_id, holding_id, description, barcode, my_response, status_code):

		item = {'mms_id':mms_id,
			'system':master.system,
			'holding_id':holding_id,
			'barcode':barcode,
			'description':description}

		if item['mms_id'] not in self.existing_log_data:
			with open(self.unknown_error_file, 'a') as data:
				data.write(f"{mms_id} | {master.titles_lookup[item['mms_id']]['title']} | {item['system']} | {item['holding_id']} | {barcode} | {description}\n")
				data.write(f"{status_code}") 
				data.write(f"{my_response}")
				data.write("\n\n\n\n\n")
		with open(self.audit, 'a') as data:
			data.write(f"{mms_id} | {master.titles_lookup[item['mms_id']]['title']} | {item['system']} | {item['holding_id']} | {barcode} | {description} | Outcome: unknown error\n")
			
	def get_exisiting_succesfuls_from_logs(self):
		"""reads the master audit log file, and establishes if any found barcode has been set was 'successful' 
		records list of succesfully processed barcodes"""

		if os.path.exists(self.successfully_added):
			with open(self.successfully_added) as data:
				for line in [x for x in data.read().split("\n") if x != '']:
					parts = line.split(" | ")
					barcode = parts[5]
					self.existing_log_data.append(str(barcode))
					self.succesful.append(str(barcode))

		if os.path.exists(self.dup_log_file):
			with open(self.dup_log_file) as data:
				for line in [x for x in data.read().split("\n") if x != '']:
					parts = line.split(" | ")
					barcode = parts[4]
					self.existing_log_data.append(str(barcode))
					self.succesful.append(str(barcode))

	def add_item(self, mms, system, holding_id, library, item_id, barcode, description, success, dup_barcode):
		"""basic data model for an item that will be rcved"""

		self.items.append({'mms_id':mms,
			'system':system,
			'holding_id':holding_id,
			'library':library,
			'item_id':item_id,
			'barcode':barcode,
			'description':description,
			'success':success,
			'dup_barcode':dup_barcode, 
			'written_to_file':False})

	def move_if_all_items_in_sheet_successful(self):
		"""compares the number of barcodes that have been found as successful (either in flight, or via the audit logger) with the number of barcodes its found on the sheet
		if the same, it moves the worksheet off to the completed folder."""
		if len(list(set(self.succesful) ^ set(self.found_barcodes))) == 0:
			self.completed == True
			print (f"Workbook {my_workbook} fully processed. Moved to completed folder")
			if not os.path.exists(os.path.join(completed_sheets_root, my_workbook)):
				shutil.move(os.path.join(sheets_root,my_workbook), completed_sheets_root)
			else:
				os.remove(os.path.join(sheets_root,my_workbook))
		else:
			print (f"Workbook {my_workbook} not fully processed. {len(list(set(self.succesful) ^ set(self.found_barcodes)))} barcode(s) remain unprocessed")
			print (f"{list(set(self.succesful) ^ set(self.found_barcodes))}")

def get_xlsx_spreadsheet(f):
	"""picks up a spreadsheet and converts it into date
	WARNING: only reads the first 13 cells
	tries to ignore empty rows
	requires sheet layout to be fixed as is currently set out in the template file.... 
	todo make the data model driven by the header text to allow for column position changing..."""
	len_data = 13
	my_data = []
	wb = load_workbook(f)
	ws = wb.active
	row_counter = 0
	cell_counter = 0
	for i, row in enumerate(ws):
		my_row = []
		row_counter  += 1
		if row_counter == 1:
			pass
		else:
			for cell in row[0:len_data]:
				try:
					my_row.append(cell.value.strip())
				except:
					my_row.append(cell.value) 

			if my_row != [None for x in range(len_data)]:
				my_data.append(my_row[0:len_data])
	return my_data

def barcode_in_alma(barcode):
	"""checks if ALMA has seen this barcode before
	returns True/False"""
	if verbose:
		print (f"Checking if {barcode} is in ALMA")
	if "No items found for barcode" in requests.get(f'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/items?item_barcode={barcode}&apikey={master.api_key}').text:
		return False
	else:
		return True

def has_no_policy(item_as_xml):
	"""Checks an item in ALMA - is the "policy" element populated?"""
	try:
		policy = BeautifulSoup(item_as_xml, 'lxml').find('policy').text
	except AttributeError:
		policy = ""
	if policy  == "":
		return True
	else:
		return False

def get_item_by_barcode(barcode):
	"""Gets an item data object from ALMA via its barcode"""
	if verbose:
		print (f"Getting {barcode} from ALMA")
	return requests.get(f'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/items?item_barcode={barcode}&apikey={master.api_key}').text

def has_no_description(item_as_xml):
	"""Checks an item in ALMA - is the "description" element populated?"""
	try:
		description = BeautifulSoup(item_as_xml, 'lxml').find('description').text
	except AttributeError:
		description = ""
	if description == "":
		return True
	else:
		return False

def make_atl_item(my_item_dict):
	"""returns the ATL item data object"""
	with open("template_xml.xml") as data:
		atl_item = data.read()
	atl_item = atl_item.replace("<holding_id></holding_id>", f'<holding_id>{my_item_dict["ATL"]["holding_id"]}</holding_id>')
	atl_item = atl_item.replace("<barcode></barcode>", f'<barcode>{my_item_dict["ATL"]["barcode"]}</barcode>')
	atl_item = atl_item.replace("<policy></policy>", f'<policy>{my_item_dict["ATL"]["policy_id"]}</policy>')
	atl_item = atl_item.replace("<chronology_i></chronology_i>",f'<chronology_i>{my_item_dict["chron_i"]}</chronology_i>') 
	atl_item = atl_item.replace("<chronology_j></chronology_j>",f'<chronology_j>{my_item_dict["chron_j"]}</chronology_j>') 
	atl_item = atl_item.replace("<chronology_k></chronology_k>",f'<chronology_k>{my_item_dict["chron_k"]}</chronology_k>')
	atl_item = atl_item.replace("<enumeration_a></enumeration_a>",f'<enumeration_a>{my_item_dict["enum_a"]}</enumeration_a>')
	atl_item = atl_item.replace("<enumeration_b></enumeration_b>",f'<enumeration_b>{my_item_dict["enum_b"]}</enumeration_b>')
	atl_item = atl_item.replace("<enumeration_c></enumeration_c>",f'<enumeration_c>{my_item_dict["enum_c"]}</enumeration_c>')
	""""""
	if my_item_dict["public_note"]:
		atl_item = atl_item.replace("<public_note></public_note>", f'<public_note>{my_item_dict["public_note"]}</public_note>')
	if my_item_dict["internal_note_1"]:
		atl_item = atl_item.replace("<internal_note_1></internal_note_1>", f'<internal_note_1>{my_item_dict["internal_note_1"]}</internal_note_1>')
	atl_item = atl_item.replace("<receiving_operator>API</receiving_operator>", f'<receiving_operator>{my_item_dict["receiving_operator"]}</receiving_operator>')
	atl_item = atl_item.replace("<description></description>", f'<description>{my_item_dict["description"]}</description>')
	return (atl_item)

def make_wg_item(my_item_dict):
	"""returns the WN item data object"""
	with open("template_xml.xml") as data:
		wg_item = data.read()
	wg_item = wg_item.replace("<holding_id></holding_id>", f'<holding_id>{my_item_dict["WN"]["holding_id"]}</holding_id>')
	wg_item = wg_item.replace("<barcode></barcode>", f'<barcode>{my_item_dict["WN"]["barcode"]}</barcode>')
	wg_item = wg_item.replace("<policy></policy>", f'<policy>{my_item_dict["WN"]["policy_id"]}</policy>')
	wg_item = wg_item.replace("<chronology_i></chronology_i>",f'<chronology_i>{my_item_dict["chron_i"]}</chronology_i>') 
	wg_item = wg_item.replace("<chronology_j></chronology_j>",f'<chronology_j>{my_item_dict["chron_j"]}</chronology_j>') 
	wg_item = wg_item.replace("<chronology_k></chronology_k>",f'<chronology_k>{my_item_dict["chron_k"]}</chronology_k>')
	wg_item = wg_item.replace("<enumeration_a></enumeration_a>",f'<enumeration_a>{my_item_dict["enum_a"]}</enumeration_a>')
	wg_item = wg_item.replace("<enumeration_b></enumeration_b>",f'<enumeration_b>{my_item_dict["enum_b"]}</enumeration_b>')
	wg_item = wg_item.replace("<enumeration_c></enumeration_c>",f'<enumeration_c>{my_item_dict["enum_c"]}</enumeration_c>') 

	""""""
	if my_item_dict["public_note"]:
		wg_item = wg_item.replace("<public_note></public_note>", f'<public_note>{my_item_dict["public_note"]}</public_note>')
	if my_item_dict["internal_note_1"]:
		wg_item = wg_item.replace("<internal_note_1></internal_note_1>", f'<internal_note_1>{my_item_dict["internal_note_1"]}</internal_note_1>')
	wg_item = wg_item.replace("<receiving_operator>API</receiving_operator>", f'<receiving_operator>{my_item_dict["receiving_operator"]}</receiving_operator>')
	wg_item = wg_item.replace("<description></description>", f'<description>{my_item_dict["description"]}</description>')


	return (wg_item)

def make_new_item_in_alma(po_line_id, item_as_xml, barcode, holding_id, my_item_dict):
	"""does most the heavy lifting..."""
	make_item_request = None
	time_out_counter = 0
	item_in_alma = False
	item_is_updated = False
	new_item_url = f"""https://api-eu.hosted.exlibrisgroup.com/almaws/v1/acq/po-lines/{po_line_id}/items?apikey={master.api_key}"""
	headers = {'content-type':'application/xml'}

	if not barcode_in_alma(barcode):
		if verbose:
			print (f"{barcode} - Not in ALMA - adding item... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

		make_item_request = requests.post(new_item_url, headers=headers, data=item_as_xml.encode('utf-8'))



		if verbose:
			print (f"Request made...{make_item_request.status_code} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

		if make_item_request.status_code == 400:
			print ("err02: something went wrong")
			print ()
			print (new_item_url)
			print ()
			print (item_as_xml)
			quit()

		elif make_item_request.status_code != 200:
			if verbose:
				print (f"Done adding - moving to cleanup. {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
		elif make_item_request.status_code == 200:
			item_in_alma = True

	else:
		if verbose:
			print (f"{barcode} already in ALMA. Attempting cleanup")
		item_in_alma = True
	

	##### clean up

	if verbose:
		print (f"Getting updated item object from ALMA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
	item_from_alma_as_xml = get_item_by_barcode(barcode)

	# print (item_from_alma_as_xml)

	# quit()
	if verbose:
		print (f"Got item object from ALMA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
	soup = BeautifulSoup(item_from_alma_as_xml, "xml")

	item_id = soup.find("item")
	if soup.find("item") != None:
		item_url = item_id['link']+f"?apikey={master.api_key}"
		__, item_id = item_id['link'].rsplit("/", 1)
		
		if has_no_policy(item_from_alma_as_xml):
			
			item_from_alma_as_xml  = item_from_alma_as_xml.replace("<public_note></public_note>", f'<public_note>{my_item_dict["public_note"]}</public_note><is_magnetic>false</is_magnetic>')
			item_from_alma_as_xml  = item_from_alma_as_xml.replace("<receiving_operator>API</receiving_operator>", f'<receiving_operator>{my_item_dict["receiving_operator"]}</receiving_operator>')
			item_from_alma_as_xml  = item_from_alma_as_xml.replace("<internal_note_1></internal_note_1>", f'<internal_note_1>{my_item_dict["internal_note_1"]}</internal_note_1>')
			item_from_alma_as_xml  = item_from_alma_as_xml.replace("<description></description>", f'<description>{my_item_dict["description"]}</description>')
			if str(barcode).startswith("7"):	
				item_from_alma_as_xml  = item_from_alma_as_xml.replace("<policy></policy>", f'<policy>{my_item_dict["ATL"]["policy_id"]}</policy>')
			elif str(barcode).startswith("3"):
				item_from_alma_as_xml  = item_from_alma_as_xml.replace("<policy></policy>", f'<policy>{my_item_dict["WN"]["policy_id"]}</policy>')
			if verbose:
				print (f"Item updated request made - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
			r = requests.put(item_url, headers=headers, data=item_from_alma_as_xml.encode('utf-8'))



			if r.status_code == 200:
				print (f"Item {barcode} is in ALMA and was updated.")
				item_is_updated = True
		else:
			item_is_updated = True
			print (f"Item {barcode} is in ALMA and updated.")
	else:
		if verbose:
			print ("Item not found for updating")

	if item_in_alma and item_is_updated:
		log.log_successful_item( my_item_dict['mms_id'], holding_id, my_item_dict['description'], barcode, item_id, item_url)
		if verbose:
			print ("Item is in, and up to date")
	
	elif item_in_alma and not item_is_updated:
		if verbose:
			print ("THIS IS A GOOD CASE TO KNOW ABOUT _________________________________  ITEM IN BUT NOT UPDATED. DOES IT NEED LOGGING?")

	elif not item_in_alma:
		log.log_bad_item(my_item_dict['mms_id'], holding_id, my_item_dict["description"], barcode)


	if verbose:
		print (f"item_in_alma (got a 200): {item_in_alma}, item_is_updated (got a 200): {item_is_updated}")
		print (f"Item process complete - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
		print ("____________________")

def rvc_new_item_old_method(my_item_dict):
	time_out_counter = 0
	atl_item = None
	wg_item = None

	barcodes = [x for x in [my_item_dict['ATL']['barcode'], my_item_dict['WN']['barcode']] if x != None ]
	items = []
	for barcode in barcodes:
		if str(barcode).startswith("7"):
			atl_item = make_atl_item(my_item_dict)
		if str(barcode).startswith("3"):
			wg_item = make_wg_item(my_item_dict)

	if my_item_dict['ATL']['barcode']:
		items.append((my_item_dict['mms_id'], my_item_dict['ATL']['holding_id'], atl_item, str(my_item_dict['ATL']['barcode'])))

	if my_item_dict['WN']['barcode']:
		items.append((my_item_dict['mms_id'], my_item_dict['WN']['holding_id'], wg_item, str(my_item_dict['WN']['barcode'])))

	for mms, holding_id, data_item, barcode in items:
		make_new_item_in_alma(my_item_dict['po_line_id'], data_item, barcode, holding_id, my_item_dict)

def process_sheet(my_spreadsheet_file, titles_lookup, test_run=False):
	"""over arching sheet processing step. 
	Takes a completed spreadsheet and converts each line into an item data modeled object
	tracks new titles
	tracks if item has been processed before
	"""
	fname, __ = my_spreadsheet_file.rsplit(".", 1)
	my_spreadsheet_data = get_xlsx_spreadsheet(os.path.join(sheets_root, my_spreadsheet_file))

	for i, my_item in enumerate(my_spreadsheet_data):
		my_item  = ["" if x == None else x for x in my_item] 
		mms = int(f"{my_item[0]}".strip())
		if str(mms).endswith("0"):
			mms += 6

		# get barcodes from sheet 
		# used to check if already logged locally 
		# this saves time asking ALMA if its seen the barcode before.

		if my_item[7]:
			wn_barcode = str(my_item[7])
			log.found_barcodes.append(wn_barcode)
		else:
			wn_barcode = None
		if my_item[8]:
			atl_barcode = str(my_item[8])
			log.found_barcodes.append(atl_barcode) 
		else:
			atl_barcode = None
		
		# if barcode not local list of already processed from the log, start processing
		
		item = Item()

		### deal with the MMS - resolve or make title listing. 

		if mms in master.mms_timeout_skip_list:
			print (f"MMS {mms} in skip list. Moving on. ")
			continue 

		if mms not in master.titles_lookup:
			item.new_title = False
			print (f"{mms} Not in titles look up - looking up details")
			master.titles_lookup = fish_for_new_record(mms, master.titles_lookup)
		else:
			item.new_title = True

		# make item data model object
		item.record_dict["po_line_id"] = master.titles_lookup[mms]["pol"]
		item.record_dict["mms_id"] = mms
		item.record_dict["enum_a"] = my_item[1]
		item.record_dict["enum_b"] = my_item[2]
		item.record_dict["enum_c"] = my_item[3]
		item.record_dict["chron_i"] = my_item[4]
		item.record_dict["chron_j"] = my_item[5]
		if len(str(item.record_dict["chron_j"])) == 1:
			item.record_dict["chron_j"] = "0"+str(item.record_dict["chron_j"])
		item.record_dict["chron_k"] = my_item[6]
		if len(str(item.record_dict["chron_k"])) == 1:
			item.record_dict["chron_k"] = "0"+str(item.record_dict["chron_k"])
		item.record_dict["ATL"]["barcode"] = my_item[7]
		item.record_dict["ATL"]["holding_id"] = master.titles_lookup[mms]["ATL"]
		item.record_dict["WN"]["barcode"] = my_item[8]
		item.record_dict["WN"]["holding_id"] = master.titles_lookup[mms]["WN"]
		item.record_dict["description"] = description_maker.make_description(
													item.record_dict["enum_a"], 
													item.record_dict["enum_b"], 
													item.record_dict["enum_c"], 
													item.record_dict["chron_i"], 
													item.record_dict["chron_j"], 
													item.record_dict["chron_k"], 
													verbose=False)
		item.record_dict["public_note"] = my_item[9]
		item.record_dict["internal_note_1"] = my_item[10]
		item.record_dict["title"] = my_item[11]

		# check that barcodes are valid (ie. wn is a wn number, atl is an atl number)

		both_records_added = False
		if (atl_barcode and str(atl_barcode) in log.existing_log_data) and (wn_barcode and str(wn_barcode)  in log.existing_log_data):
			both_records_added = True

		if not both_records_added:
			#valid barcodes
			if not str(item.record_dict["ATL"]["barcode"]).startswith("7") and item.record_dict["ATL"]["barcode"]!="":
				if item.record_dict["ATL"]["barcode"] != None:
					print (f'{item.record_dict["ATL"]["barcode"]} - Barcode value does not match the type expected for ATL holding')
					item.valid_atl_barcode = False
					item.process_item = False

			if not str(item.record_dict["WN"]["barcode"]).startswith("3") and item.record_dict["WN"]["barcode"]!="":
				if item.record_dict["WN"]["barcode"] != None:
					print (f'{item.record_dict["WN"]["barcode"]} - Barcode value does not match the type expected for WN holding')
					item.valid_wn_barcode = False
					item.process_item = False

			
			# new_title?
			if [master.titles_lookup[mms]['title']] not in log.checks_needed and master.titles_lookup[mms]['signed_off'] == None:
				log.checks_needed.append(item.record_dict['title'])

			# only do the commit if not test run
			if not test_run:
				print (master.titles_lookup[mms]["title"], "|", item.record_dict["description"],  "| ATL:", atl_barcode,  "| WN: ", wn_barcode, f" | started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" )

				### actually adding the item. 
				# if item.record_dict["mms_id"] not in log.mms_timeout_skip_list and item.process_item:
				if item.process_item:
					#old process with added safety checks. 
					rvc_new_item_old_method(item.record_dict)
					#new method that doesn't work at the moment... 
					# rvc_new_item(item.record_dict)

				else:
					log.succesful = False

		
				if master.titles_lookup[mms]['title'] not in log.checks_needed and master.titles_lookup[mms]['signed_off'] == None:
						log.checks_needed.append(master.titles_lookup[mms]['title'])

			if test_run:
				if master.titles_lookup[mms]['title'] not in log.checks_needed and master.titles_lookup[mms]['signed_off'] == None:
					log.checks_needed.append(master.titles_lookup[mms]['title'])
				
		else:
			print (f"Skipping {master.titles_lookup[mms]['title']} | {item.record_dict['description']} | ATL: {atl_barcode} | WN: {wn_barcode} - already logged.")

	# Add title to list of titles that need checking.
	# get list of existing titles on list so we don't add them again! 
	if os.path.exists(r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisi tions Team\bulk item ingest\log_files\titles_for_checking.txt"):
		with open(r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\log_files\titles_for_checking.txt") as data:
			existing_titles_for_checks = data.read().split("\n")
	else:
		existing_titles_for_checks = []
	# add new item to the list
	for title in [x for x in set(log.checks_needed) if x not in existing_titles_for_checks]:
		print (f"Checks needed for {title}")
		with open(r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\log_files\titles_for_checking.txt", 'a') as data:
			data.write(f"{title}\n")
	return

def fish_for_new_record(mms_id, titles_lookup):
	"""searches alma for the correct POL id, and two holding ids (WN and ATL) for a given MMS id
	the process is a little assumative, but has tested 100%..."""

	# POL line notes: 
	# GET https://api-eu.hosted.exlibrisgroup.com/almaws/v1/acq/po-lines?q=mms_id~9916997193502836&status=ACTIVE&limit=10&offset=0&order_by=title&direction=desc&apikey=l8xxcc5a1f43073d4755898a66faaab1a44d&expand=NOTES

	nl_holding_id = None
	atl_holding_id = None

	if str(mms_id).endswith("0"):
		mms_id += 6

	headers = {'content-type':'application/xml'}
	url =  f"https://api-eu.hosted.exlibrisgroup.com/almaws/v1/acq/po-lines?q=mms_id~{mms_id}&status=ACTIVE&limit=100&offset=0&order_by=title&direction=desc&apikey={master.api_key}&expand=LOCATIONS"
	r = requests.get(url, headers=headers)
	soup = BeautifulSoup(r.text, "lxml")
	
	if verbose:
		print (f"Getting records data from: {r.url}")
		print (r.text)
		print ()

	if 'po_lines total_record_count="0"' in r.text:
		print (f"Check mms id {mms_id}" )
		quit()
	elif soup.find("title").text == None:
		if verbose:
			stand_down = 30
			print (f"Look up failed - waiting for {stand_down} seconds to try again")
		time.sleep(stand_down ) 
		r = requests.get(url, headers=headers)
		soup = BeautifulSoup(r.text, "lxml")
	else:

		title = soup.find("title").text
		pol_id = soup.find("number").text
		locations = soup.find_all("location")

		for location in locations:
			library = location.find("library").text
			shelving_location = location.find("shelving_location").text
			holding_id = location.find("holdings").find("id").text

			if library == "NL":
				nl_holding_id = holding_id

			if library == "ATL":
				atl_holding_id = holding_id

		if atl_holding_id == nl_holding_id:
			print ("Holding ID picking went wrong, WN is the same as ATL ")
			print ({'mms': mms_id, 'ATL': atl_holding_id, 'WN': nl_holding_id, 'pol': pol_id, 'title': title})
			quit()

		titles_lookup[mms_id] =  {'mms': mms_id, 'ATL': atl_holding_id, 'WN': nl_holding_id, 'pol': pol_id, 'title': title, 'system': master.system, 'signed_off': None}
		add_new_title_to_spreadsheet(titles_lookup[mms_id])
	return titles_lookup



def setup_folders():
	"""makes the folders needed for logs and finished sheets"""
	if not os.path.exists(completed_sheets_root):
		os.makedirs(completed_sheets_root)
	if not os.path.exists(log_root ):
		os.makedirs(log_root)

def preflight_check(my_f):
	file_path = os.path.join(sheets_root, my_f)
	my_spreadsheet_data = get_xlsx_spreadsheet(file_path)
	for i, my_item in enumerate(my_spreadsheet_data):
		my_item  = ["" if x == None else x for x in my_item]
		try:
			mms = int(f"{my_item[0]}".strip())
		except ValueError:
			print ("Missing MMS id in spreadsheet")
			return False

		if my_item[7]:
			wn_barcode = str(my_item[7])
			log.found_barcodes.append(str(wn_barcode)) 
		if my_item[8]:
			atl_barcode = str(my_item[8])
			log.found_barcodes.append(str(atl_barcode)) 
	# except:
		# return False
	# print (len(log.found_barcodes))
	log.preflight_check = True


# sheets_root = r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets\for_processing"
# sheets_root = r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets\in_flight"
# sheets_root = r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets\testing"
# completed_sheets_root = r'E:\work\bulk_issue_ingester\completed_worksheets'


log_root = r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\log_files"
sheets_root = r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets\for_processing"
completed_sheets_root = r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\spreadsheets\completed"
setup_folders()

my_workbooks = [x for x in os.listdir(sheets_root) if (not x.startswith("~") and x.endswith(".xlsx"))]
my_workbooks.sort()
if len(my_workbooks) == 0:
	quit(print (f"\nNo workbooks found in: {sheets_root}\n"))


master.set_prod(True)
verbose = True
test_run = False

for my_workbook in my_workbooks:
	log=Logger(f"{my_workbook}_{master.system}.txt", log_root)
	preflight_check(my_workbook)
	print (my_workbook)
	if log.preflight_check:
		
		process_sheet(my_workbook, master.titles_lookup, test_run=test_run)
		log.move_if_all_items_in_sheet_successful()

		if os.path.exists(os.path.join(sheets_root, my_workbook)):
			log.get_exisiting_succesfuls_from_logs()
			print ("\n2nd Pass\n")
			process_sheet(my_workbook, master.titles_lookup, test_run=test_run)
			log.move_if_all_items_in_sheet_successful()

		if os.path.exists(os.path.join(sheets_root, my_workbook)):
			log.get_exisiting_succesfuls_from_logs()
			print ("\n3rd Pass\n")
			process_sheet(my_workbook, master.titles_lookup, test_run=test_run)
			log.move_if_all_items_in_sheet_successful()


	else:
		print (f"Workbook wasn't processed as it contains errors. Please fix and try again!" )
	print ("\n\n")

