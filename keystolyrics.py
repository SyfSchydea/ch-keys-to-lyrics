#!/bin/python3

"""
This script will take a notes.chart file, and convert the Expert 
KeyBoard chart to lyric, phrase_start, and phrase_end events. 
 * Fret 2 (Red) becomes phrase_start
 * Fret 3 (Yellow) becomes an empty lyric
 * Fret 4 (Blue) becomes phrase_end

Expected notes.chart format:
[<section names>]
{
<stuff>
}
(repeat a few times)
[Events]
{
  <timestamp> = E "<event text>"
  ...
}
[<diff name>]
{
  <timestamp> = ([N|S] <fret id> <duration>|E <event name>)
}
"""

import re
from operator import attrgetter

class ChartEvent:
	def __init__(self, time, name):
		self.time = int(time)
		self.name = name
	
	def get_code(self):
		return '  {} = E "{}"'.format(self.time, self.name)

def convert_chart(file_in, file_out):
	# Echo stuff before events
	while True:
		line = file_in.readline()
		if line == "":
			raise Exception("Chart has no Events Section")
		
		if re.match(r"\[Events\]\s*", line):
			break
		
		file_out.write(line)
	
	# Read in current events
	open_brace_line = file_in.readline()
	if not re.match(r"\{\s*", open_brace_line):
		raise Exception('Line after "[Events]" should contain only "{"')
	
	global_events = []
	while True:
		line = file_in.readline()
		if line == "":
			raise Exception("Unexpected EOF during events section")
		event_match = re.match(r'\s*(\d+)\s*=\s*E\s*"([^"]*)"\s*', line)
		
		if event_match:
			event = ChartEvent(event_match[1], event_match[2])
			global_events.append(event)
		elif re.match(r"\}\s*", line):
			break
		else:
			raise Exception("Unexpected line in Events section: " + line)
	
	# Read and store diffs before ExpertKeyboard
	diff_text = ""
	while True:
		line = file_in.readline()
		if line == "":
			raise Exception("File has no ExpertKeyboard chart to convert")
		
		if re.match(r"\[ExpertKeyboard\]\s*", line):
			break
		
		diff_text += line
	
	# when we find ExpertKeyboard:
	# read in the notes, converting them to lyric events
	open_brace_line = file_in.readline()
	if not re.match(r"\{\s*", open_brace_line):
		raise Exception('Line after "[ExpertKeyboard]" should contain only "{"')
	
	while True:
		line = file_in.readline()
		if line == "":
			raise Exception("Unexpected EOF during ExpertKeyboard chart")
		
		# If it's a valid note, on an appropriate fret, log the relevant event
		# Matches a line like: 6912 = N 2 0
		# Only the timestamp (6912) and fret id (2) are captured
		note_match = re.match(r'\s*(\d+)\s*=\s*N\s*([1-3])\s*\d+\s*', line)
		if note_match:
			event_type = None
			if note_match[2] == "1":
				event_type = "phrase_start"
			elif note_match[2] == "2":
				event_type = "lyric "
			elif note_match[2] == "3":
				event_type = "phrase_end"
			
			event = ChartEvent(note_match[1], event_type)
			global_events.append(event)
			continue
		
		# If it's any other note, or star power etc, ignore it
		# Matches lines like: 6912 = N 2 0
		#                     6219 = S 2 120
		#                     6329 = E solo
		if re.match(r'\s*\d+\s*=\s*(?:[NS]\s*\d+\s*\d+|E\s*[a-zA-Z\d_]+)\s*', line):
			continue
		
		# If it's a closing brace, break
		if re.match(r"\}\s*", line):
			break
		
		# If it's anything else, throw an error
		raise Exception("Unexpected line during ExpertKeyboard chart: " + line)
	
	# Read and store any diffs after ExpertKeyboard
	while True:
		line = file_in.readline()
		if line == "":
			break
		
		diff_text += line
	
	# compile the existing events plus the new lyric events
	global_events = sorted(global_events, key=attrgetter("time"))
	
	# Print the events section
	file_out.write("[Events]\n{\n")
	for event in global_events:
		file_out.write(event.get_code() + "\n")
	file_out.write("}\n")
	
	# Print previously stored diffs
	file_out.write(diff_text)

if __name__ == "__main__":
	import sys
	import os
	import shutil
	from argparse import ArgumentParser

	parser = ArgumentParser(description="Convert notes to lyric events in a Clone Hero chart")

	parser.add_argument("input-file", nargs="?", help="Input chart location")
	parser.add_argument("output-file", nargs="?", help="Output chart location")

	args = parser.parse_args()

	input_path = getattr(args, "input-file")
	output_path = getattr(args, "output-file")

	files_closable = False
	created_backup = False

	if input_path is None:
		# No files specified, use stdin and stdout
		file_in = sys.stdin
		file_out = sys.stdout
	
	elif output_path is None:
		# One file specified, move to .bak, write to original location
		output_path = input_path
		input_path += ".bak"

		shutil.move(output_path, input_path)
		created_backup = True

		file_in = open(input_path)
		file_out = open(output_path, "w")
		files_closable = True
	
	else:
		# Two files specified, use those locations
		file_in = open(input_path)
		file_out = open(output_path, "w")
		files_closable = True

	try:
		convert_chart(file_in, file_out)
		err = None
	except Exception as e:
		err = e
	finally:
		if files_closable:
			file_in.close()
			file_out.close()

		if err:
			os.remove(output_path)

			if created_backup:
				shutil.move(input_path, output_path)

			raise err
