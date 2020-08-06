import glob
import os


""" This class loads an entire directory into a dictionary so we don't have to open a file every request.
    Convenient for very small websites!
"""
def load_all(dir):
	original_dir = os.getcwd()
	os.chdir(dir)
	accumulator = {}
	for p in glob.glob("*"):
		if (os.path.isfile(p) and "jpeg" not in p):
			with open(p) as f:
				accumulator[p]=f.read()
		if (os.path.isdir(p)):
			accumulator[p]=load_all(p)
	os.chdir(original_dir)
	return accumulator
