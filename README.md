# ch-keys-to-lyrics

This script aims to make charting lyrics in Clone Hero charts easier. Instead of directly adding lyric events, 
notes can be placed temporarily in an unused chart, then converted using this script into lyric, phrase_start, 
and phrase_end events. This makes it easier to visualise, or hear the lyric timing in editors like Moonscraper.

## Usage

	./keystolyrics.py <chart in> <chart out>

This usage will read a script in from the first file, and output to the second file, overwriting an existing file if neccessary.

	./keystolyrics.py <chart>

This usage will modify the chart in place. And create a backup appended with `.bak`.

	./keystolyrics.py

This usage will read a chart file in from stdin and output to stdout.
