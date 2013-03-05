import sys

sys.path.append("../../")

from mpfrl.hierarchy import MPF_Hierarchy
from mpfrl.units import *
from mpfrl.SOM import Miller_SOM

mpf_h = None

SIDES_NOMINALS = {"cross" : 1.0, "nought" : 0.5}

my_side = SIDES_NOMINALS["nought"]

__reinf_adj = 0.0

def init(side_name):
	global mpf_h
	global my_side
	
	my_side = SIDES_NOMINALS[side_name]
	
	l0_units = [
			MPF_Unit_RL(
				ss_class = Miller_SOM,
				ts_class = Miller_SOM,
				input_dim = 3,
				ss_shape = (6, 6),
				ts_shape = (6, 6),
				parent_unit = None,
				unit_type = MPF_UT_SENSOR
			),
			MPF_Unit_RL(
				ss_class = Miller_SOM,
				ts_class = Miller_SOM,
				input_dim = 3,
				ss_shape = (6, 6),
				ts_shape = (6, 6),
				parent_unit = None,
				unit_type = MPF_UT_SENSOR
			),
			MPF_Unit_RL(
				ss_class = Miller_SOM,
				ts_class = Miller_SOM,
				input_dim = 3,
				ss_shape = (6, 6),
				ts_shape = (6, 6),
				parent_unit = None,
				unit_type = MPF_UT_SENSOR
			)
	]
	
	mpf_h = MPF_Hierarchy(l0_units, 2, 10, "K:/__temp/mpf_rl_dumps/tictactoe_no_rules")
	
def __adjust_move_layout(layout):
	"""
	adjust generated layout to contain proper categorical values
	
	NOTE: 'layout' MUST be passed by view
	"""
	
	for i in xrange(len(layout.flat)):
		if (layout.flat[i] <= 0.25):
			layout.flat[i] = 0.0
		elif (layout.flat[i] > 0.25) and (layout.flat[i] <= 0.75):
			layout.flat[i] = 0.5
		elif (layout.flat[i] > 0.75):
			layout.flat[i] = 1.0
			
def __validate_move_layout(prev_game_field, adj_new_layout):
	if (sum(adj_new_layout) - sum(prev_game_field) != my_side):
		return False
	
	for i in xrange(len(prev_game_field.flat)):
		if ((prev_game_field.flat[i] != 0.0) and
			(prev_game_field.flat[i] != adj_new_layout[i])):
			
			return False
		
	return True

def __correct_move_layout(prev_game_field, adj_new_layout):
	"""
	Corrects new layout to be proper move from 'prev_game_field'
	with minimal alterations being done
	
	NOTE: 'adj_new_layout' MUST be passed as view
	"""
	
	move_made = False
	
	for i in xrange(len(prev_game_field.flat)):
		if (prev_game_field.flat[i] != adj_new_layout[i]):
		
			if (prev_game_field.flat[i] != 0.0):
				adj_new_layout[i] = prev_game_field.flat[i]
			else:
				
				# Whether to alternate AI's side or just ignore improper side?
				# Try to IGNORE for now
				##
				# NOTE: This will probably lead to random move (see below)
				
				if ((move_made) or (adj_new_layout[i] != my_side)):
					adj_new_layout[i] = 0.0
				else:
					move_made = True
	
	# still no move, make it in first empty space
	if (not move_made):
		for i in xrange(adj_new_layout.shape[0]):
			if (adj_new_layout[i] == 0.0):
				adj_new_layout[i] = my_side
				break

"""	
def make_move(game_field, reinforcement):
	
	global __reinf_adj
	
	while (True): # NOTE: Is such approach valid???
		mpf_h.evaluate(game_field.flatten(), reinforcement + __reinf_adj)
		
		__adjust_move_layout(mpf_h.output_vec[:])
		#print mpf_h.output_vec
		
		
		if (__validate_move_layout(game_field, mpf_h.output_vec)):
			break
		
		reinforcement -= 0.2
	
	__reinf_adj += 0.2
	
	game_field[:] = mpf_h.output_vec.reshape((3,3)).copy()
"""

def make_move(game_field, reinforcement):
	
	mpf_h.evaluate(game_field.flatten(), reinforcement + __reinf_adj)
		
	__adjust_move_layout(mpf_h.output_vec[:])
	__correct_move_layout(game_field, mpf_h.output_vec[:])
	
	game_field[:] = mpf_h.output_vec.reshape((3,3)).copy()	
	
	
	