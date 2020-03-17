import hashlib
import os
import shutil
from datetime import datetime

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def update_titles():
	shared_file = r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\titles_reference.xlsx"
	local_file = "titles_reference.xlsx"
	shared_file_fixity = md5(shared_file)
	local_file_fixity = md5(local_file)

	if shared_file_fixity != local_file_fixity:
		print ("Updating 'Title Reference'.")
		new_local_name = os.path.join("titles_reference_backups", local_file.replace(".xlsx", f"_{datetime.now().strftime('%Y-%m-%d %H_%M_%S')}.xlsx"))
		if os.path.exists(new_local_name):
			os.remove(new_local_name)
		os.rename(local_file, new_local_name)
		
		new_remote_name = os.path.join(r"G:\Fileplan\Bib_Services\Non-Clio_formats\Acquisitions Team\bulk item ingest\titles_reference_backups", local_file.replace(".xlsx", f"_{datetime.now().strftime('%Y-%m-%d %H_%M_%S')}.xlsx"))
		shutil.copy(new_local_name, new_remote_name )

		shutil.copy(shared_file, ".")
	else:
		print ("Using Local 'Titles Reference'.")

update_titles()