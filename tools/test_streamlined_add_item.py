import requests
import time
from datetime import datetime
import description_maker
from bs4 import BeautifulSoup
from openpyxl import Workbook, load_workbook
from title_ref_updater import update_titles
from title_lookup import titles_lookup, add_new_title_to_spreadsheet
import configparser
import shutil
import os

secret_file = r"c:\source\secrets"
config = configparser.ConfigParser()
config.read(secret_file)
prod_key = config.get("configuration", "PRODUCTION")
sand_key = config.get("configuration", "SANDBOX") 

def check_description(barcode):
	record = requests.get(f'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/items?item_barcode={barcode}&apikey={api_key}').text
	try:
		description = BeautifulSoup(record, 'lxml').find('description').text
	except AttributeError:
		description = None
	if description == "" or description == None:
		return False
	else:
		return True


def make_atl_item(my_item_dict):
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
	if records_dict["public_note"]:
		atl_item = atl_item.replace("<public_note></public_note>", f'<public_note>{my_item_dict["public_note"]}</public_note>')
	if records_dict["internal_note_1"]:
		atl_item = atl_item.replace("<internal_note_1></internal_note_1>", f'<internal_note_1>{my_item_dict["internal_note_1"]}</internal_note_1>')
	atl_item = atl_item.replace("<receiving_operator>API</receiving_operator>", f'<receiving_operator>{my_item_dict["receiving_operator"]}</receiving_operator>')
	atl_item = atl_item.replace("<description></description>", f'<description>{my_item_dict["description"]}</description>')
	return (atl_item)

def make_wg_item(my_item_dict):
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
	if records_dict["public_note"]:
		wg_item = wg_item.replace("<public_note></public_note>", f'<public_note>{records_dict["public_note"]}</public_note>')
	if records_dict["internal_note_1"]:
		wg_item = wg_item.replace("<internal_note_1></internal_note_1>", f'<internal_note_1>{records_dict["internal_note_1"]}</internal_note_1>')
	wg_item = wg_item.replace("<receiving_operator>API</receiving_operator>", f'<receiving_operator>{records_dict["receiving_operator"]}</receiving_operator>')
	wg_item = wg_item.replace("<description></description>", f'<description>{records_dict["description"]}</description>')
	return (wg_item)

def submit_item(mms_id, holding_id, item_as_xml):

	success = False
	dup_barcode = False
	in_system = False
	error = False
	headers = {'content-type':'application/xml'}
	url = f'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/{mms_id}/holdings/{holding_id}/items?apikey={api_key}'
	r = requests.post( url, headers=headers, data=item_as_xml.encode('utf-8'))
	return r.text, r.status_code, r.url

def add_item(my_item_dict):
	atl_item = None
	wg_item = None
	barcodes = [x for x in [my_item_dict['ATL']['barcode'], my_item_dict['WN']['barcode']] if x != None ]
	items = []
	for barcode in barcodes:
		if str(barcode).startswith("7"):
			atl_item = make_atl_item(records_dict)
		if str(barcode).startswith("3"):
			wg_item = make_wg_item(records_dict)

	if my_item_dict['ATL']['barcode']:
		items.append((my_item_dict['mms_id'], my_item_dict['ATL']['holding_id'], atl_item,my_item_dict['ATL']['barcode']))

	if my_item_dict['WN']['barcode']:
		items.append((my_item_dict['mms_id'], my_item_dict['WN']['holding_id'], wg_item, my_item_dict['WN']['barcode']))

	for mms, holding, data_item, barcode in items:
		my_response, status_code, my_url = submit_item(mms, holding, data_item)

		if status_code == 200:
			soup = BeautifulSoup(my_response, "xml")	
			item_id = soup.find("item")
			item_url = item_id['link']
			__, item_id = item_url.rsplit("/", 1)
			# print ("SUCCESS!")
			# print (item_url+f"?apikey={api_key}")
			print (f"Added: {barcode}")
			# log.successful_item(mms, holding, my_item_dict['description'], barcode, item_id, item_url)

		elif status_code == 400 and "already exists" in my_response:
			print (f"Dup barcode: {barcode}")
			# log.dup_barcode_item(mms, holding, my_item_dict['description'], barcode)

		elif status_code == 400 and "Check holdings" in my_response:
			print (f"Bad holding ID: {holding} for item: {barcode}")
			# log.bad_request_item(mms, holding, my_item_dict['description'])
		else:
			print ("Unexpected status reponse")
			print (mms, holding, my_item_dict['description'])
			# log.error_item(mms, holding, my_item_dict['description'])

def set_prod(set_prod=False):
	""" PROD / SANDBOX switcher
	for API key management
	for title lookup - (mms / holding ids etc) """
	if set_prod:
		api_key = prod_key
		system = "PROD"
	else:
		api_key = sand_key
		system = "SAND"

	return api_key, system

api_key, system = set_prod(False)


records_dict = { 'WN': {'holding_id': 22264567620002836, 'barcode': 322220009265479, 'policy_id': 'STANDARD'}, 
				'ATL': {'holding_id': 22264481340002836, 'barcode': 744440133175829, 'policy_id': 'HERITAGE'}, 
				'po_line_id': '218187-ilsdb', 
				'mms_id': 0, 
				'internal_note_1': 'ASLKDJA:SODAS', 
				'public_note': 'blah', 
				'receiving_operator': 'gattusoj_API', 
				'description': 'v. 17, no. 1 (2020 01 09)', 
				'chron_i': 2020, 'chron_j': 1, 'chron_k': 9, 'enum_a': 17, 'enum_b': 1, 'enum_c': '', 
				'title': 'Mandarin pages	'}


print ()

add_item(records_dict)
		
if not check_description(322220009265479):
	print ("need desc")
else:
	print ("have desc")



			
