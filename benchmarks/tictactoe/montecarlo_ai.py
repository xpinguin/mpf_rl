"""
	Just simple random AI
"""

from numpy import random

SIDES_NOMINALS = {"cross" : 1.0, "nought" : 0.5}
my_side = None

def init(side_name):
	global my_side
	
	my_side = SIDES_NOMINALS[side_name]

def make_move(game_field, reinf = 0):
	while (True):
		r_ind = random.randint(0, len(game_field.flat))
			
		if (game_field.flat[r_ind] != 0.0): continue
		
		game_field.flat[r_ind] = my_side
		break
