import sys

sys.path.append("../../")

from mpfrl.hierarchy import MPF_Hierarchy
from mpfrl.units import *
from mpfrl.SOM import Miller_SOM

mpf_h = None

SIDES_NOMINALS = {"cross" : 1.0, "nought" : 0.5}

my_side = SIDES_NOMINALS["nought"]

__reinf_adj = 0.0

# predicted game field state after opponent's move
# kept flat for convience
#
predicted_game_field = None

def init(side_name):
	global mpf_h
	global my_side
	
	my_side = SIDES_NOMINALS[side_name]
	
	l0_units = [
			MPF_Unit_RL(
				ss_class = Miller_SOM,
				ts_class = None,
				input_dim = 3,
				ss_shape = (5, 5),
				ts_shape = (6, 6),
				parent_unit = None,
				unit_type = MPF_UT_SENSOR
			),
			MPF_Unit_RL(
				ss_class = Miller_SOM,
				ts_class = None,
				input_dim = 3,
				ss_shape = (5, 5),
				ts_shape = (6, 6),
				parent_unit = None,
				unit_type = MPF_UT_SENSOR
			),
			MPF_Unit_RL(
				ss_class = Miller_SOM,
				ts_class = None,
				input_dim = 3,
				ss_shape = (5, 5),
				ts_shape = (6, 6),
				parent_unit = None,
				unit_type = MPF_UT_SENSOR
			)
	]
	
	"""
	l0_units = [
			MPF_Unit_RL(
				ss_class = Miller_SOM,
				ts_class = None,
				input_dim = 9,
				ss_shape = (30, 30),
				ts_shape = (6, 6),
				parent_unit = None,
				unit_type = MPF_UT_SENSOR
			)
	]
	"""
	
	mpf_h = MPF_Hierarchy(
			l0_units = l0_units,
			levels_num = 3,
			dump_period = 0,
			dump_path = "K:/__temp/mpf_rl_dumps/tictactoe_no_rules_no_l0-rsom_3levels_6units",
			ts_class = Miller_SOM
	)
	
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

def __correct_move_layout(prev_game_field, adj_new_layout, side = None):
	"""
	Corrects new layout to be proper move from 'prev_game_field'
	with minimal alterations being done
	
	NOTE: 'adj_new_layout' MUST be passed as view
	"""
	
	if (side == None): side = my_side
	
	move_made = False
	
	# STAGE 1: Proper move
	for i in xrange(len(prev_game_field.flat)):
		if (prev_game_field.flat[i] != adj_new_layout[i]):
		
			if (prev_game_field.flat[i] != 0.0):
				adj_new_layout[i] = prev_game_field.flat[i]
			else:
				
				# Whether to alternate AI's side or just ignore improper side?
				# Try to IGNORE at first pass
				# Then try to ALTERNATE in second pass
				#
				# NOTE: Random move is the last "fail-over" option thus
				##
				# NOTE: This will probably lead to random move (see below)
				
				#"""
				if ((move_made) or (adj_new_layout[i] != side)):
					adj_new_layout[i] = 0.0
				else:
					move_made = True
				#"""
				
				"""
				if (move_made):
					adj_new_layout[i] = 0.0
				elif (adj_new_layout[i] == side):
					move_made = True
				"""	
	"""			
	# STAGE 2: try to alternate wrong side (i.e. hierarchy put opponent's side somewhere)
	if (not move_made):
		for i in xrange(len(prev_game_field.flat)):
			if ((prev_game_field.flat[i] != adj_new_layout[i]) and 		
				(prev_game_field.flat[i] == 0.0)):
				
				if (move_made):
					adj_new_layout[i] = 0.0
				else:
					adj_new_layout[i] = side
					move_made = True
	
						
	# -- clean garbage
	for i in xrange(len(prev_game_field.flat)):
		if ((prev_game_field.flat[i] != adj_new_layout[i]) and 		
			(prev_game_field.flat[i] == 0.0) and (adj_new_layout[i] != side)):
				adj_new_layout[i] = 0.0
	"""
	
	
	# STAGE 3: still no move, make it in first empty space
	if (not move_made):
		for i in xrange(adj_new_layout.shape[0]):
			if (adj_new_layout[i] == 0.0):
				adj_new_layout[i] = side
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
	
	global predicted_game_field
	global __reinf_adj
	
	if (predicted_game_field != None):
		diff = predicted_game_field - game_field.flat
		if (dot(diff, diff) == 0): 
			__reinf_adj = 0.2
			print "\n+++++\n++++++\n++++++++\n+++++++\tWow!\n++++++\n++++++\n++++++++\n++++++++++++\n"
		else:
			__reinf_adj = 0.0
	
	mpf_h.evaluate(game_field.flatten(), reinforcement + __reinf_adj)
		
	__adjust_move_layout(mpf_h.output_vec[:])
	__correct_move_layout(game_field, mpf_h.output_vec[:])
	
	game_field[:] = mpf_h.output_vec.reshape((3,3)).copy()
	
	"""
	# predict next game field
	# TODO: decide something about reinforcement!
	mpf_h.evaluate(game_field.flatten(), 0.0)
	
	__adjust_move_layout(mpf_h.output_vec[:])
	__correct_move_layout(game_field, mpf_h.output_vec[:], (((my_side * 2) % 2) + 1) / 2.0)
	
	predicted_game_field = mpf_h.output_vec[:]
	"""
	
	