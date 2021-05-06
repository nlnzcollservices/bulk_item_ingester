

# enum_a = "1" ### vol 
# enum_b = "12" ### number
# enum_c = "2323" ### issue
# chron_i = "2000" ### yyyy or yyyy/yyyy
# chron_j = "01" ### mm or [seasons]
# chron_k = "02-31" ### dd pr dd-dd



def description_parts_validator(enum_a, enum_b, enum_c, chron_i, chron_j, chron_k, verbose=False):
	controlled_terms = ["Spring", "Summer", "Autumn", "Winter", "Christmas", "term 1", "term 2", "term 3", "term 4", "quarter 1", "quarter 2", "quarter 3", "quarter 4"]
	months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
	days = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31"]
	zero_pad_lookup = {"1":"01", "2":"02", "3":"03", "4":"04", "5":"05", "6":"06", "7":"07", "8":"08", "9":"09" }


	if not any([enum_a, enum_b, enum_c, chron_i, chron_j, chron_k]):
		if verbose:
			print ("No data given")
		return False, "No data given"

	if enum_a:
		if "/" in enum_a:
			vol_a, vol_b = enum_a.split("/")
			if not (vol_a.isdigit() and vol_b.isdigit()):
				if verbose:
					print ("Volume data with range indicator is not correct")
				return False, "Volume data with range indicator is not correct"

		else:
			if not enum_a.isdigit():
				if verbose:
					print ("Volume data is not numerical")
				return False, "Volume data is not numerical"
	
	if enum_b:
		if "-" in enum_b :
			num_a, num_b = enum_b.split("-")
			if not (num_a.isdigit() and num_b.isdigit()):
				if verbose:
					print ("Number data with range indicator is not correct")
				return False, "Number data with range indicator is not correct" 

		elif "/" in enum_b :
			num_a, num_b = enum_b.split("/")
			if not (num_a.isdigit() and num_b.isdigit()):
				if verbose:
					print ("Number data with range indicator is not correct")
				return False, "Number data with range indicator is not correct" 

		else:	
			if not enum_b.isdigit():
				if verbose:
					print ("Number data is not numerical")
				return False, "Number data is not numerical"
	
	if enum_c:
		if not enum_c.isdigit():
			if verbose:
				print ("Issue data is not numerical")
			return False, "Issue data is not numerical" 
	
	if chron_i:
		if "/" in chron_i:
			year_a, year_b = chron_i.split("/")
			if not (year_a.isdigit() and len(year_a) == 4 and year_b.isdigit() and len(year_b) == 4):
				if verbose:
					print ("Year data with range indicator is not correct")
				return False, "Year data with range indicator is not correct"
		else:
			if not (chron_i.isdigit() and len(chron_i) == 4):
				if verbose:
					print ("Year data is not numerical or in the YYYY form")
				return False, "Year data is not numerical or in the YYYY form"

	if chron_j:
		if chron_j.isdigit():
			if not chron_j in months:
				if verbose:
					print ("Month data is not in MM form (check zero padding)")
				return False, "Month data is not in MM form (check zero padding)"
		else:
			if not chron_j in controlled_terms:
				if verbose:
					print ("Month data appears to be a controlled term, but is not in controlled list")
				return False,  "Month data appears to be a controlled term, but is not in the controlled list"

	if chron_k:
		if "-" in chron_k:
			day_a, day_b = chron_k.split("-")
			if not (day_a in days and day_b in days):
				if verbose:
					print ("Day data with range indicator is not correct")
				return False, "Day data with range indicator is not correct"
		else:
			if not chron_k in days:
				if verbose:
					print ( "Day data is not numerial or in zero padded form")
				return False,  "Day data is not numerial or in zero padded form"

	return True, "OK"


def description_parts_checker(enum_a, enum_b, enum_c, chron_i, chron_j, chron_k, verbose=False):
	assert enum_a or enum_b or enum_c or chron_i or chron_j or chron_k, "No data is being given" 

	seasons = ["Spring", "Summer", "Autumn", "Winter"]
	months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
	days = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31"]

	if enum_a:
			assert enum_a.isdigit(), "vol data is not numerical"
	
	if enum_b:

			assert enum_b.isdigit(), "number data is not numerical"
	
	if enum_c:
			assert enum_c.isdigit(), "number data is not numerical"
	
	if chron_i:
		if "/" in chron_i:
			year_a, year_b = chron_i.split("/")
			assert year_a.isdigit() and len(year_a) == 4 and year_b.isdigit() and len(year_b) == 4, "Year data with range indicator is not correct"
		else:
			assert chron_i.isdigit() and len(chron_i) == 4, "Year data is not numerical or in the YYYY form"

	if chron_j:
		if chron_j.isdigit():
			assert chron_j in months, "Month data is not in MM form (check zero padding)"
		else:
			assert chron_j in seasons,  "Month data appears to be a season, but is not in controlled list"

	if chron_k:
		if "-" in chron_k:
			day_a, day_b = chron_k.split("-")
			assert day_a in days and day_b in days, "Day data with range indicator is not correct"
		else:
			assert chron_k in days, "Day data is not numerial or in zero padded form"


def make_description(enum_a, enum_b, enum_c, chron_i, chron_j, chron_k, verbose=False):
	zero_pad_lookup = {"1":"01", "2":"02", "3":"03", "4":"04", "5":"05", "6":"06", "7":"07", "8":"08", "9":"09", }

	if enum_a == None:
		enum_a = ""
	else:
		enum_a = str(enum_a)

	if enum_b == None:
		enum_b = ""
	else:
		enum_b = str(enum_b)

	if enum_c == None:
		enum_c = ""
	else:
		enum_c = str(enum_c)

	if chron_i == None:
		chron_i = ""
	else:
		chron_i = str(chron_i)


	if chron_j == None:
		chron_j = ""
	else:
		chron_j = str(chron_j)

	if chron_k == None:
		chron_k = ""
	else:
		chron_k = str(chron_k)

	if chron_j in zero_pad_lookup:
		chron_j = zero_pad_lookup[chron_j]
	if chron_k in zero_pad_lookup:
		chron_k = zero_pad_lookup[chron_k]

	parts_OK, message = description_parts_validator(enum_a, enum_b, enum_c, chron_i, chron_j, chron_k, verbose=False)

	if parts_OK:


		# used for testing 
		# if 1 == 2:
		# 	pass
		## case 1 YYYY MMM - year month only
		if not enum_a and not enum_b and not enum_c and chron_i and chron_j and not chron_k:
			if verbose:
				print ("#1")
				# print (not enum_a and not enum_b and not enum_c and chron_i and chron_j and not chron_k)
			return f"{chron_i} {chron_j}"

		### case 2 YYYY - year only
		elif not enum_a and not enum_b and not enum_c and not chron_j  and chron_i and not chron_k:
			if verbose:
				print ("#2")
				# print (not enum_a and not enum_b and not enum_c and not chron_j  and chron_i and not chron_k)
			return f"{chron_i}"

		### case 3 	YYYY MMM DD - Year Month Day only
		elif not enum_a and not enum_b and not enum_c and chron_i and chron_j and chron_k:
			if verbose:
				print ("#3")
				# print (not enum_a and not enum_b and not enum_c and chron_i)
			return f"{chron_i} {chron_j} {chron_k}"

		### case 4 iss.(YYYY) - issue year
		elif not enum_a and not enum_b and enum_c and chron_i and not chron_j and not chron_k:
			if verbose:
				print ("#4")
				# print (not enum_a and not enum_b and enum_c and chron_i and not chron_j and not chron_k)
			return f"iss. {enum_c} ({chron_i})"

		### case 5 iss. (YYYY MM/TTTTT) - Issue, Year, Month or Term  ## description!
		elif not enum_a and not enum_b and enum_c and chron_i and chron_j and not chron_k:
			if verbose:
				print ("#5")
				# print (not enum_a and not enum_b and enum_c and chron_i and chron_j and not chron_k)
			return f"iss. {enum_c} ({chron_i} {chron_j})"

		### case 6  iss. (YYYY MM/TTTTT DD) - Issue, Year, Month or Term & Day
		elif not enum_a and not enum_b and enum_c and chron_i and chron_j and chron_k:
			if verbose:
				print ("#6")
				# print (not enum_a and not enum_b and enum_c and chron_i and chron_j and chron_k)
			return f"iss. {enum_c} ({chron_i} {chron_j} {chron_k})"

		### case 7 no. (YYYY) - Number & Year only
		elif not enum_a and enum_b and not enum_c and chron_i and not chron_j and not chron_k:
			if verbose:
				print ("#7")
				# print (not enum_a and enum_b and not enum_c and chron_i and not chron_j and not chron_k)
			return f"no. {enum_b} ({chron_i})"

		### case 8 no. (YYYY MMM) - Number, Year & Month
		elif not enum_a and enum_b and not enum_c and chron_i and chron_j and not chron_k:
			if verbose:
				print ("#8")
				# print (not enum_a and enum_b and not enum_c and chron_i and chron_j and not chron_k)
			return f"no. {enum_b} ({chron_i} {chron_j})"

		### case 9 no. (YYYY MMM DD) - Number, Year, Month & Day
		elif not enum_a and enum_b and not enum_c and chron_i and chron_j and chron_k:
			if verbose:
				print ("#9")
				# print (not enum_a and enum_b and not enum_c and chron_i and chron_j and chron_k)
			return f"no. {enum_b} ({chron_i} {chron_j} {chron_k})"

		# ### case 10 no. (YYYY) - Number & Year only
		# elif not enum_a and enum_b and enum_c and chron_i and not chron_j and not chron_k:
		# 	if verbose:
		# 		print ("#10")
		# 		# print (not enum_a and enum_b and not enum_c and chron_i and not chron_j and not chron_k)
		# 	return f"no. {enum_b}, iss. {enum_c} ({chron_i})"

		### case 11 v. (YYYY) - Volume & Year only
		elif enum_a and not enum_b and not enum_c and chron_i and not chron_j and not chron_k:
			if verbose:
				print ("#11")
				# print (enum_a and not enum_b and not enum_c and chron_i and not chron_j and not chron_k)
			return f"v. {enum_a} ({chron_i})"

		### case 12 no. v. (YYYY MMM/SSS) - Volume, Year & Month/Season
		elif enum_a and not enum_b and not enum_c and chron_i and chron_j and not chron_k:
			if verbose:
				print ("#12")
				# print (enum_a and not enum_b and not enum_c and chron_i and chron_j and not chron_k)
			return f"v. {enum_a} ({chron_i} {chron_j})"

		### case 13 v., no. (YYYY) - Volume, Number & Year
		elif enum_a and enum_b and not enum_c and chron_i and not chron_j and not chron_k:
			if verbose:
				print ("#13")
				# print (enum_a and enum_b and not enum_c and chron_i and not chron_j and not chron_k)
			return f"v. {enum_a}, no. {enum_b} ({chron_i})"

		### case 14 v., no. (YYYY S/T/M) - Volume, Number, Year & Season, Term or Month:
		elif enum_a and enum_b and not enum_c and chron_i and chron_j and not chron_k:
			if verbose:
				print ("#14")
				# print (enum_a and enum_b and not enum_c and chron_i and chron_j and not chron_k)
			return f"v. {enum_a}, no. {enum_b} ({chron_i} {chron_j})"

		### case 15 v., no. (YYYY MM DD) - Volumn, Number, Year, Month Day
		elif enum_a and enum_b and not enum_c and chron_i and chron_j and chron_k:
			if verbose:
				print ("#15")
				# print (enum_a and enum_b and not enum_c and chron_i and chron_j and chron_k)
			return f"v. {enum_a}, no. {enum_b} ({chron_i} {chron_j} {chron_k})"

		### case 16 v., # (YYYY) - Volume, other number & Year #### same as #12?
		elif enum_a and enum_b and not enum_c and chron_i and not chron_j and not chron_k:
			if verbose:
				print ("#16")
				# print (enum_a and enum_b and not enum_c and chron_i and not chron_j and not chron_k)
			return f"v. {enum_a}, {enum_b} ({chron_i})"

		### case 17 v. iss. (YYYY) - Volume, Issue & Year
		elif enum_a and not enum_b and enum_c and chron_i and not chron_j and not chron_k:
			if verbose:
				print ("#17")
				# print (enum_a and not enum_b and enum_c and chron_i and not chron_j and not chron_k)
			return f"v. {enum_a}, iss. {enum_c} ({chron_i})"

		### case 18 v., iss. (YYYY MM) - Volume, Issue, Year & Month
		elif enum_a and not enum_b and enum_c and chron_i and chron_j and not chron_k:
			if verbose:
				print ("#18")
				# print (enum_a and not enum_b and enum_c and chron_i and chron_j and not chron_k)
			return f"v. {enum_a}, iss. {enum_c} ({chron_i} {chron_j})"

		### case 19 v., no., iss. (YYYY) - Volume, Number, Issue, Year ### description 
		elif enum_a and enum_b and enum_c and chron_i and not chron_j and not chron_k:
			if verbose:
				print ("#19")
				# print (enum_a and enum_b and enum_c and chron_i and not chron_j and not chron_k)
			return f"v. {enum_a}, no. {enum_b}, iss. {enum_c} ({chron_i})"

		### case 20 v., no., iss. (YYYY MM/SS) - Volume, Number, Issue, Year & Month/Season ### description 
		elif enum_a and enum_b and enum_c and chron_i and chron_j and not chron_k:
			if verbose:
				print ("#20")
				# print (enum_a and enum_b and enum_c and chron_i and chron_j and not chron_k)
			return f"v. {enum_a}, no. {enum_b},  iss. {enum_c} ({chron_i} {chron_j})"

		else: ### Three Enumerations & three Chronologies
			if verbose:
				print ("Catch-all")
			basic_all =  f"v. {enum_a}, no. {enum_b},  iss. {enum_c} ({chron_i} {chron_j} {chron_k})"
			cleaned_all = basic_all[:]
			while "  " in cleaned_all:
				cleaned_all = cleaned_all.replace("  ", " ")

			cleaned_all = cleaned_all.replace(" )", ")").replace("v. , ", "").replace("no. , ", "").replace("iss. (", "(").replace(", ()", "").replace("()", "").replace(", (", " (").strip()
			return cleaned_all

	else:
		print (message)


# enum_a, enum_b, enum_c, chron_i, chron_j, chron_k = 12, None, 1, 1990, None, 2
# print (make_description(enum_a, enum_b, enum_c, chron_i, chron_j, chron_k, verbose = True)) 