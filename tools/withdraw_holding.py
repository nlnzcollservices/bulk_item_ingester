import requests
import math
from bs4 import BeautifulSoup as bs
import configparser
from openpyxl import Workbook, load_workbook
import pymarc

secret_file = r"c:\source\secrets"
config = configparser.ConfigParser()
config.read(secret_file)
prod_key = config.get("configuration", "PRODUCTION")
sand_key = config.get("configuration", "SANDBOX")

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

def get_xlsx_spreadsheet(f):
	len_data = 18
	my_data = []
	wb = load_workbook(f)
	ws = wb.active
	row_counter = 0
	cell_counter = 0
	for i, row in enumerate(ws):
		my_row = []
		row_counter  += 1
		for cell in row[0:len_data]:
			my_row.append(cell.value)
		if my_row != [None for x in range(len_data)]:
			my_data.append(my_row[0:len_data])
	return my_data[1:]


def get_853(holding_id, mms_id, mms_look_up):
	my_853 = None 
	url = f"""https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/{mms_id}/holdings/{holding_id}?apikey={api_key}"""
	marc_xml = requests.get(url).text
	soup = bs(marc_xml, 'lxml')

	datafield = soup.find("datafield", {"tag":'853'})
	mms_look_up[mms_id] = datafield

	# if mms_look_up[mms_id]:
	# 	print (mms_look_up[mms_id].text)
	return mms_look_up



def check_ALMA_report_for_my_items(my_report):

	mms_look_up = {}

	my_data = get_xlsx_spreadsheet(my_report)

	for line in my_data:
		item_id = line[15]
		holding_id = line[16]
		mms_id = line[17]

		if mms_id not in mms_look_up:
			mms_look_up = get_853(holding_id, mms_id, mms_look_up)



		# quit()
		item = requests.get(f"""https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/{mms_id}/holdings/{holding_id}/items/{item_id}?apikey={api_key}""")

		soup = bs(item.text, "lxml")
		# print (item.url)

		try:
			date = soup.find('creation_date').text
		except AttributeError:
			date = None
		

		if soup.find('receiving_operator') and soup.find('receiving_operator').text == "import":
			pass

		elif date and date.startswith("2017"):
			pass
		elif date and date.startswith("2018"):
			pass
		elif date and date.startswith("2019-0"):
			pass
		elif date and date.startswith("2019-10"):
			pass
		



		elif date and not mms_look_up[mms_id]:
			print (item.url)
			print (date, str(soup.find('receiving_operator')).replace("</receiving_operator>", "").replace("<receiving_operator>", ""))
			print ()
		# print (soup)
		# quit()
		
		# withdraw: DELETE /almaws/v1/bibs/{mms_id}/holdings/{holding_id}/items/{item_id}

		# quit()




def get_all_holdings(mms_id, holding_id, verbose=False):
	"""returns a list of all the item URLS for a holding""" 
	my_item_urls = []
	limit = 100
	url = f"""https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/{mms_id}/holdings/{holding_id}/items?apikey={api_key}&limit=1&offset=0"""
	headers = {'content-type':'application/xml'}
	r = requests.get(url, headers=headers)
	if verbose:
		print (r.url)
	qty = int(bs((r.text),'lxml').find("items")["total_record_count"])
	for call in range(math.ceil(qty/limit)):
		offset = (call*limit)
		url = f"""https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/{mms_id}/holdings/{holding_id}/items?apikey={api_key}&limit={limit}&offset={offset}"""
		r = requests.get(url, headers=headers)
		my_items = bs((r.text), 'lxml').find_all("item")
		for item in my_items:
			my_item_urls.append(item['link']) 
	if verbose:
		print (f"expected: {qty}, found:{len(my_item_urls)}")
	return my_item_urls

def withdraw_all_holdings_on_holding_id(mms_id, holding_id, verbose=False):
	"""deletes all the itmes attached to a holding""" 
	my_item_urls = []
	limit = 100
	url = f"""https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/{mms_id}/holdings/{holding_id}/items?apikey={api_key}&limit=1&offset=0"""
	headers = {'content-type':'application/xml'}
	r = requests.get(url, headers=headers)
	if verbose:
		print (r.url)
	qty = int(bs((r.text),'lxml').find("items")["total_record_count"])
	print (f"Found {qty} records. Withdrawing.")
	for call in range(math.ceil(qty/limit)):
		url = f"""https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/{mms_id}/holdings/{holding_id}/items?apikey={api_key}&limit=100&offset=0"""
		r = requests.get(url, headers=headers)
		my_items = bs((r.text), 'lxml').find_all("item")
		for item in my_items:
			r = requests.delete(item['link']+f"?apikey={api_key}", headers=headers)
			if r.status_code == 204:
				if verbose:
					print (f"{item['link']} withdrawn OK")
			else:
				print (r.status_code)
				print (r.text)
				print (r.url)
				print ("Something went wrong. Quitting")
				quit()

def withdraw_holding_by_item_url(item_url, verbose=False):
	"""deletes a single item from its item url"""
	headers = {'content-type':'application/xml'}
	r = requests.delete(item_url+f"?apikey={api_key}", headers=headers)
	if r.status_code == 204:
		if verbose:
			print (f"{item_url} withdrawn OK")
	else:
		print (r.status_code)
		print (r.text)
		print (r.url)
		print ("Something went wrong. Quitting")
		quit()

def withdraw_holdings_by_list_of_urls(item_urls, verbose=False):
	"""deletes a batch of items from their item urls"""
	for item_url in item_urls:
		headers = {'content-type':'application/xml'}
		r = requests.delete(item_url+f"?apikey={api_key}", headers=headers)
		if r.status_code == 204:
			if verbose:
				print (f"{item['link']} withdrawn OK")
		else:
			print (r.status_code)
			print (r.text)
			print (r.url)
			print ("Something went wrong. Quitting")
			quit()

def withdraw_holding_by_ids(item, holding, mms, verbose=False):
	"""deletes a batch of items from their item urls"""
	url = f"https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/{mms}/holdings/{holding}/items/{item}"

	headers = {'content-type':'application/xml'}
	r = requests.delete(url+f"?apikey={api_key}", headers=headers)
	if r.status_code == 204:
		if verbose:
			print (f"{item} withdrawn OK")
	else:
		print (r.status_code)
		print (r.text)
		print (r.url)
		print ("Something went wrong. Quitting")
		quit()

def withdraw_holding_by_log_file(my_log_file, verbose=False):


	with open(my_log_file) as data:
		lines = data.read().split("\n")

		for line in [x for x in lines if x != ""]:
			parts = line.split(" | ")

			item =  parts[4]
			holding = parts[3]
			mms = parts[0]

			url = f"https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/{mms}/holdings/{holding}/items/{item}"

			headers = {'content-type':'application/xml'}
			r = requests.delete(url+f"?apikey={api_key}", headers=headers)
			if r.status_code == 204:
				if verbose:
					print (f"{item} withdrawn OK")
			elif "No Item found for" in r.text:
				print (f"{item} either already withdrawn, or not in {system}")
			else:
				print (r.status_code)
				print (r.text)
				print (r.url)
				print ("Something went wrong. Quitting")
				quit()

def withdraw_holding_by_barcode(my_barcode, verbose=False):
	url = f'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/items?item_barcode={my_barcode}&apikey={api_key}'
	r = requests.get(url)

	if "found for barcode" in r.text:
		if verbose:
			print (f"{my_barcode} either already withdrawn, or not in {system}")
	else:
		soup = bs(r.text, "lxml")
		mms = soup.find("mms_id").text
		holding_id = soup.find("holding_id").text
		item_url = soup.find("item")["link"]
		withdraw_holding_by_item_url(item_url, verbose=verbose) 

def withdraw_holding_by_test_file_of_barcodes(my_file):
	with open(my_file) as data:
		barcodes = [x for x in data.read().split("\n") if x != ""]
		for barcode in barcodes:
			withdraw_holding_by_barcode(barcode, True)

def withdraw_holding_by_list_of_barcodes(barcodes):
	for barcode in barcodes:
		withdraw_holding_by_barcode(barcode, True)

# withdraw_all_holdings("9918872173602836", "22336182980002836")  
# withdraw_holding("https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/996354203502836/holdings/22194150670002836/items/23341455810002836")
# withdraw_holding_by_log_file(my_log_file, True)
# withdraw_holding_by_ids(23343325540002836,22184035470002836,999252763502836, True)

# my_log_file = r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\log_files_new\10_Our Auckland 2020 - Paige.xlsx_SAND_full_audit.txt")
# withdraw_holding_by_log_file(my_log_file, True)



api_key, system = set_prod(True)

# withdraw_holding_by_barcode(74444000286795, True)

# my_text_file_of_barcodes = "barcodes.txt"
# withdraw_holding_by_test_file_of_barcodes(my_text_file_of_barcodes)

# withdraw_holding_by_list_of_barcodes([32222000926502,74444000175757, 32222000926503,74444000175758])
# withdraw_holding_by_list_of_barcodes([74444000175778,32222000926522,74444000175779,32222000926523,74444000175780,32222000926524])
check_ALMA_report_for_my_items("results.xlsx")