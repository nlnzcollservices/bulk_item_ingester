
import os
import requests
import configparser
from bs4 import BeautifulSoup as Soup
from make_issues_month import make_month_by_issues_days
from title_lookup import titles_lookup

secret_file = r"c:\source\secrets"
config = configparser.ConfigParser()
config.read(secret_file)
prod_key = config.get("configuration", "PRODUCTION")
sand_key = config.get("configuration", "SANDBOX") 




prod = True

if prod:
	api_key = prod_key
	system = "PROD"
	titles_lookup = titles_lookup[system]
else:
	api_key = sand_key
	system = "SAND"
	titles_lookup = titles_lookup[system]

# _______________________________________________________________________

def chunks(l, n):
    """Yield n number of striped chunks from l."""
    for i in range(0, n):
        yield l[i::n]

def make_cal_view(mms, holding_id, title, issue_count_limit=25):

	# title = "Advocate south"
	# mms = "9918183771802836"

	# record_ui_page = "https://natlib-primo.hosted.exlibrisgroup.com/primo-explore/fulldisplay?vid=NLNZ&docid=NLNZ_ALMA21301261480002836&context=L&search_scope=NLNZ"
	# url = f"https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs?view=full&expand=d_avail&apikey={api_key}&mms_id={mms}"

	url = f'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/{mms}/holdings/{holding_id}/items?limit={issue_count_limit}&offset=0&order_by=description&direction=desc&apikey={api_key}'

	### results in a BeautifulSoup item that can searched etc
	r = requests.get( url, headers={'content-type': 'application/xml' })

	my_issues = {}
	my_soup = Soup((r.text), 'lxml')
	issues = my_soup.find_all("item_data")

	for issue in issues:
		year = issue.find("chronology_i").text
		month = issue.find("chronology_j").text
		day = issue.find("chronology_k").text
		enum_a = issue.find("enumeration_a").text
		enum_b = issue.find("enumeration_b").text
		enum_c = issue.find("enumeration_c").text
		description = issue.find("description").text



		if year not in my_issues:
			my_issues[year] = {}

		if month not in my_issues[year]:
			my_issues[year][month] = []

		if day not in my_issues[year][month]:
			my_issues[year][month].append(day)

	print (title)
	print (mms)

	print ()

	years = list(my_issues.keys()) 
	years.sort()
	# try:
	my_month_blocks = []
	for year in years:
		months = list(my_issues[year].keys())
		months.sort()
		for month in months:
			issue_days = [int(x) for x in my_issues[year][month]]
			my_month = make_month_by_issues_days(year, month, issue_days)
			my_month_blocks.append(my_month)
	pairs = chunks(my_month_blocks, 2)
	for pair in pairs:
		print (pair[0])
		print (pair[1])
		print (pair[2])
		print (pair[3])
		try:
			a, b = pair
		except:
			a_lines = pair[0].split("\n")
			b_lines   = [[]*len(a_lines)]


		a_lines = a.split("\n")
		b_lines = b.split("\n")

		for i, l in enumerate(a_lines):
			print (a_lines[i],b_lines[i])

	
		print ()
	quit()
	# except:
	### remove empty days
	months_only_dict = {}
	for year in my_issues:
		if year not in months_only_dict:
			months_only_dict[year] = []
		for month in my_issues[year]:
			if month not in months_only_dict:
				months_only_dict[year].append(month)
				months_only_dict[year].sort()


	print (months_only_dict)

				# quit()



skip_list = [9910097593502836]
for mms, data in titles_lookup.items():
	if mms not in skip_list:
		print (mms, data['title'], data["ATL"])
		make_cal_view(mms, data["ATL"], data['title'], issue_count_limit=25)

		print ("\n\n_________________\n\n")