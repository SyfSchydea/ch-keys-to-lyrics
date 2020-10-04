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

import sys
import re
from operator import attrgetter

class ChartEvent:
	def __init__(self, time, name):
		self.time = int(time)
		self.name = name
	
	def get_code(self):
		return '  {} = E "{}"'.format(self.time, self.name)

def main():
	# input = None
	# output = None
	# if sys 
	# TODO: Add the option to pass a filename to modify that file instead of using stdin and stdout
	
	# Echo stuff before events
	while True:
		line = sys.stdin.readline()
		if line == "":
			# TODO: this could be handled better, but at the same time it's not really a likely issue
			raise Exception("Chart has no Events Section")
		
		if re.match(r"\[Events\]\s*", line):
			break
		
		sys.stdout.write(line)
	
	# Read in current events
	open_brace_line = sys.stdin.readline()
	if not re.match(r"\{\s*", open_brace_line):
		raise Exception('Line after "[Events]" should contain only "{"')
	
	global_events = []
	while True:
		line = sys.stdin.readline()
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
		line = sys.stdin.readline()
		if line == "":
			raise Exception("File has no ExpertKeyboard chart to convert")
		
		# TODO: provide a parameter/flag to specify a different diff to convert to lyrics
		if re.match(r"\[ExpertKeyboard\]\s*", line):
			break
		
		diff_text += line
	
	# when we find ExpertKeyboard:
	# read in the notes, converting them to lyric events
	open_brace_line = sys.stdin.readline()
	if not re.match(r"\{\s*", open_brace_line):
		raise Exception('Line after "[ExpertKeyboard]" should contain only "{"')
	
	while True:
		line = sys.stdin.readline()
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
		line = sys.stdin.readline()
		if line == "":
			break
		
		diff_text += line
	
	# compile the existing events plus the new lyric events
	global_events = sorted(global_events, key=attrgetter("time"))
	
	# Print the events section
	print("[Events]")
	print("{")
	for event in global_events:
		print(event.get_code())
	print("}")
	
	# Print previously stored diffs
	sys.stdout.write(diff_text)

if __name__ == "__main__":
	main()
