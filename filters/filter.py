#!/usr/bin/python
# encoding: utf-8
import sys
import os.path
from workflow.workflow import (Workflow, MATCH_ALL, MATCH_ALLCHARS)

def main(wf):
	import os.path
	
	# First, ensure that Configuration has taken place
	if os.path.exists(wf.datafile(u"first-run.txt")):
		import _zotquery as z
		import json

		# Get Zotero data from JSON cache
		with open(wf.datafile(u"zotero_db.json"), 'r') as f:
			zot_data = json.load(f)
			f.close()
		
		# Get user query and filter's scope
		query = wf.args[0]
		scope = wf.args[1]

		# Query needs to be at least 3 characters long
		if len(query) <= 2:
			wf.add_item(u"Error!", u"Need at least 3 letters to execute search", 
				icon=u"icons/n_delay.png")
			wf.send_feedback()
		# If long enough query
		else:

			if scope in ['general', 'creators', 'titles', 'notes']:
				# Fuzzy search against relavant search scope
				res = wf.filter(query, zot_data, key=lambda x: z.zot_string(x, scope), match_on=MATCH_ALL ^ MATCH_ALLCHARS)
				if res != []:
					# Format matched items for display
					alp_res = z.prepare_feedback(res)	
					for a in alp_res:
						wf.add_item(**a)
				else:
					# If no results
					wf.add_item(u"Error!", u"No results found.", 
						icon=u"icons/n_error.png")
				wf.send_feedback()

			elif scope in ['collections', 'tags']:
				import sqlite3
				# Connect to cloned sqlite db
				conn = sqlite3.connect(wf.datafile(u"zotquery.sqlite"))
				cur = conn.cursor()	
				# Prepare appropriate sqlite query and relavant info
				if scope == 'collections':
					sql_query = """
						select collections.collectionName, collections.key
						from collections
						"""
					_sub = u"Collection"
					_icon = u'icons/n_collection.png'
				elif scope == 'tags':
					sql_query = """
						select tags.name, tags.key
						from tags
						"""
					_sub = u"Tag"
					_icon = u'icons/n_tag.png'

				# Get all items
				_data = cur.execute(sql_query).fetchall()
				conn.close()

				if _data != []:
					# Fuzzy search against relavant search scope
					res = wf.filter(query, _data, key=lambda x: x[0], match_on=MATCH_ALL ^ MATCH_ALLCHARS)
	
					if res != []:
						for item in res:
							wf.add_item(item[0], _sub, 
								arg=item[1], 
								valid=True, 
								icon=_icon)
				else:
					# If no results
					wf.add_item(u"Error!", u"No results found.", 
						icon=u"icons/n_error.png")
				wf.send_feedback()
		
			elif scope in ['in-collection', 'in-tag']:
				# get type name
				term = scope.split('-')[1]
				# Read the inputted tag/collection name from temporary file
				with open(wf.cachefile(u"{0}_query_result.txt").format(term), 'r') as f:
					_inp = f.read().decode('utf-8')
					f.close()
				
				# Prepare sub-list of only those items in that collection or with that tag
				_items = []
				for item in zot_data:
					for jtem in item['zot-{0}s'.format(term)]:
						if _inp == jtem['key']: 
							_items.append(item)
				
				# Fuzzy search against relavant search scope
				res = wf.filter(query, _items, key=lambda x: z.zot_string(x), match_on=MATCH_ALL ^ MATCH_ALLCHARS)

				if res != []:
					# Format matched items for display
					alp_res = z.prepare_feedback(res)	
					for a in alp_res:
						wf.add_item(**a)
				else:
					# If no results
					wf.add_item(u"Error!", u"No results found.", 
						icon=u"icons/n_error.png")
				wf.send_feedback()

			elif scope == 'attachments':
				_items = []
				for item in zot_data:
					if item['attachments'] != []:
						_items.append(item)
				# Fuzzy search against relavant search scope
				res = wf.filter(query, _items, key=lambda x: z.zot_string(x), match_on=MATCH_ALL ^ MATCH_ALLCHARS)

				if res != []:
					for item in res:
						info = z.info_format(item)
						title = item['data']['title']
						sub = info[0] + ' ' + info[1]
						wf.add_item(title, sub, 
							arg=item['attachments'][0]['path'], 
							valid=True,
							type='file',
							icon='icons/n_pdf.png')
				else:
					# If no results
					wf.add_item(u"Error!", u"No results found.", 
						icon=u"icons/n_error.png")
				wf.send_feedback()

	# Not configured
	else:
		import applescript
		a_script = """
				tell application "Alfred 2" to search "z:config"
				"""
		applescript.asrun(a_script)
				
if __name__ == '__main__':
	wf = Workflow(fold_input=True, libraries=[os.path.join(os.path.dirname(__file__), 'dependencies')])
	sys.exit(wf.run(main))
   