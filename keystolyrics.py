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
from collections import deque

class ChartEvent:
	def __init__(self, time, name):
		self.time = int(time)
		self.name = name
	
	def get_code(self):
		return '  {} = E "{}"'.format(self.time, self.name)

# Regexes used in parsing lyric files
word_boundary = re.compile(r"\s+")
syllable_boundary = re.compile(r"-")

blank_line = re.compile(r"\s*\n")

# Manages the song's lyric file, which provides the lyric text to the events
class LyricFile:
	__slots__ = [
		"file",

		"line",
		"syllable_buffer",
	]

	def __init__(self, path):
		self.file = open(path)

		self.line = 0
		self.syllable_buffer = deque()
	
	# Read the next line of syllables from the file. This should coincide with phrase_start events.
	def start_line(self):
		# Read a line, skipping any blank lines
		while True:
			line = self.file.readline()
			self.line += 1

			if not blank_line.fullmatch(line):
				break

		line = line.strip()

		# Nested list of syllables in each word
		words = [syllable_boundary.split(word) for word in word_boundary.split(line)]

		# Append dashes to syllables
		for word in words:
			for i in range(0, len(word) - 1):
				word[i] += "-"

		# Flatten the list
		self.syllable_buffer.extend(s for w in words for s in w)

	# Fetch the next syllable from the lyric file
	def next_syllable(self):
		if len(self.syllable_buffer) <= 0:
			raise Exception(f"Line {self.line} is too short")

		return self.syllable_buffer.popleft()

	# Check that a line has ended when it should. This should coincide with phrase_end events
	def end_line(self):
		if len(self.syllable_buffer) > 0:
			raise Exception(f"Line {self.line} ended too early")

	def close(self):
		self.file.close()

# Dummy class following the same interface as LyricFile
# Used when no lyric file is given
class DummyLyricFile:
	def __init__(self, path=None):
		pass
	
	def next_syllable(self):
		return ""
	
	def close(self):
		pass

def convert_chart(file_in, file_out, lyric_file):
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
				lyric_file.start_line()
				event_type = "phrase_start"
			elif note_match[2] == "2":
				event_type = "lyric " + lyric_file.next_syllable()
			elif note_match[2] == "3":
				lyric_file.end_line()
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

	parser.add_argument("-l", "--lyrics", help="File containing the lyrics of the song")

	args = parser.parse_args()

	input_path = getattr(args, "input-file")
	output_path = getattr(args, "output-file")

	if args.lyrics is not None:
		lyric_file = LyricFile(args.lyrics)
	else:
		lyric_file = DummyLyricFile()

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
		convert_chart(file_in, file_out, lyric_file)
		err = None
	except Exception as e:
		err = e
	finally:
		if files_closable:
			file_in.close()
			file_out.close()

		lyric_file.close()

		if err:
			os.remove(output_path)

			if created_backup:
				shutil.move(input_path, output_path)

			raise err
