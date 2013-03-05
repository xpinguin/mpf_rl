"""
Protected randint in here to prevent bugs in game with incorrect intervals
"""

from numpy import random

def randint(low, high):
	if (low > high):
		t = low
		low = high
		high = t
		
	if (low == high): high += 1
		
	return random.randint(low, high)