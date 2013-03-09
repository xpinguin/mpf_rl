import numpy as np
import cPickle as pickle
import gzip

from copy import deepcopy

FIELD_SIZE = 9
SIDES_NOMINALS = {"cross" : 1.0, "nought" : 0.5}

my_side = None
my_side_name = ""

__b3_b10 = np.array([3**i for i in xrange(FIELD_SIZE)])

# prebuild Wald's maximin tree
# used for two purposes:
#	1. AI move making
#	2. Opponents moves scoring
# Each dict value has following structure
# [
# 	(0) payout, 
# 	(1) [children layouts],
#	(2) next moving side nominal,
# 	(3) best child layout (i.e. best move),
#	(4) ndarray[layouts relative score (best == 1; worst == 0)]
# ]
# last two elements exists only when next moving side == tree's side
#
full_maximin_decision_tree = {"cross" : None, "nought" : None}

def __ndarray_to_dec_layout(arr):
	"""
	converts ndarray into base3 number
	which is then converted to base10 number
	
	NOTE: array elements should be:
			0 - empty cell,
			1 - nought
			2 - cross
	"""
	
	return int(np.dot(arr.flatten(), __b3_b10))

def __dec_layout_to_ndarray(dec_layout):
	"""
	converts ndarray into base3 number
	which is then converted to base10 number
	
	NOTE: array elements should be:
			0 - empty cell,
			1 - nought
			2 - cross
	"""
	
	layout = np.zeros((np.sqrt(FIELD_SIZE), np.sqrt(FIELD_SIZE)))
	
	for i in xrange(0, FIELD_SIZE):
		layout.flat[i] = dec_layout % 3
		dec_layout /= 3
		
	return layout

def __build_field_layouts_dec(side):
	"""
	Build game field layouts tree and convert them to decimals along with payouts
	Payouts are calculated according to 'side' variable
	"""
	
	### --- Helper functions ---
	def __next_move_side(dec_layout):
		"""
		return nominal of side which will move next assuming given game layout
		"""
		
		nominals_counter = [0, 0, 0]
		
		for i in xrange(0, FIELD_SIZE):
			nominals_counter[dec_layout % 3] += 1
			dec_layout /= 3
			
		if (nominals_counter[1] == nominals_counter[2]):
			return SIDES_NOMINALS["cross"]
		
		return SIDES_NOMINALS["nought"]
	
	
	def __evolve_layout(arr, empty_skip = 0):
		current_side = 2 # cross
		
		if ((arr[arr == 2].shape[0] - arr[arr == 1].shape[0]) > 0):
			current_side = 1 # naught
			
		for i in xrange(arr.shape[0] * arr.shape[1]):
			if (arr.flat[i] == 0):
				if (empty_skip <= 0):
					arr.flat[i] = current_side
					return arr
				
				empty_skip -= 1
				
		return None
	
	def __layout_payout(arr):
		prod_hvd = []
		
		# diagonals
		prod_hvd.append(np.prod(np.diag(arr)))
		prod_hvd.append(np.prod(np.diag(arr[::-1])))
		
		# verticals and horizontals
		for i in xrange(arr.shape[0]):
			prod_hvd.append(np.prod(arr[i, :]))
			prod_hvd.append(np.prod(arr[:, i]))
		
		for _prod in prod_hvd:
			if (_prod == (side * 2)**3):
				return 1.0
			elif (_prod == (((side * 2) % 2) + 1)**3):
				return -1.0
			
		return None
			
	### ---
	
	res_layouts = dict()
	
	# initial layouts queue of one empty layout
	layouts_queue = [np.zeros((np.sqrt(FIELD_SIZE), np.sqrt(FIELD_SIZE)))]
	
	#empty_layout = np.zeros((np.sqrt(FIELD_SIZE), np.sqrt(FIELD_SIZE)))
	#layouts_queue = [__evolve_layout(empty_layout.copy(), i) for i in xrange(9)]
	
	# build moves tree ("game end" moves are leaves)
	#
	while (len(layouts_queue) > 0):
		cur_layout = layouts_queue.pop()
		cur_layout_dec = __ndarray_to_dec_layout(cur_layout)
		
		res_layouts[cur_layout_dec] = [
							__layout_payout(cur_layout),
							[], # child layouts
							__next_move_side(cur_layout_dec),
		]
		if (res_layouts[cur_layout_dec][0] != None): continue
		
		
		for i in xrange(9):
			child_layout = __evolve_layout(cur_layout.copy(), i)
			if (child_layout == None): break
			
			res_layouts[cur_layout_dec][1].append(
										__ndarray_to_dec_layout(child_layout)
			)
			
			layouts_queue.insert(0, child_layout)
			
		# handle drawn game (nobody wins)
		if (len(res_layouts[cur_layout_dec][1]) == 0):
			res_layouts[cur_layout_dec][0] = 0.0
			
	return res_layouts
		
	
	
def build_maximin_decision_tree(side, raw_dec_layouts):
	"""
	builds Wald's maximin decision tree from prebuilt layouts
	"""
	
	if (raw_dec_layouts == None): return False
	
	raw_dec_layouts = deepcopy(raw_dec_layouts)
	
	# build full maximin tree against given side nominal
	#
	layouts_queue = [
					dec_layout for (dec_layout, props) in \
						 raw_dec_layouts.iteritems() if props[0] == None
	]
	
	while (len(layouts_queue) > 0):
		cur_layout_dec = layouts_queue.pop()
		
		if (raw_dec_layouts[cur_layout_dec][2] == side):
			""" choose maximumum minimal payout at my turn """
			
			if (len(raw_dec_layouts[cur_layout_dec]) < 4):
				raw_dec_layouts[cur_layout_dec].extend([None, None])
			
			raw_dec_layouts[cur_layout_dec][3] = None
			raw_dec_layouts[cur_layout_dec][4] = np.zeros(
							len(raw_dec_layouts[cur_layout_dec][1])
			)
			
			max_payout = -1e+99
			max_payout_children = None
			
			child_index = 0
			for child_layout_dec in raw_dec_layouts[cur_layout_dec][1]:
				if (raw_dec_layouts[child_layout_dec][0] == None):
					layouts_queue.insert(0, cur_layout_dec)
					max_payout = None
					
					break
				
				if (raw_dec_layouts[child_layout_dec][0] > max_payout):
					max_payout = raw_dec_layouts[child_layout_dec][0]
					max_payout_children = child_layout_dec
					
				raw_dec_layouts[cur_layout_dec][4][child_index] = \
							raw_dec_layouts[child_layout_dec][0] + 1.0
				
				child_index += 1
			
			if (max_payout != None):
				raw_dec_layouts[cur_layout_dec][0] = max_payout
				raw_dec_layouts[cur_layout_dec][3] = max_payout_children
				
				if (max_payout > -1.0):
					raw_dec_layouts[cur_layout_dec][4] /= max_payout + 1
		
		else:
			"""
				find the worst situation of layout's evolution assuming
				opponent makes turn (i.e. something that we cannot affect);
				this worst situation (mimimal payout) is exactly the payout 
				for current layout
			"""
			
			min_payout = 1e+20
			
			for child_layout_dec in raw_dec_layouts[cur_layout_dec][1]:
				if (raw_dec_layouts[child_layout_dec][0] == None):
					layouts_queue.insert(0, cur_layout_dec)
					min_payout = None
					
					break
				
				if (raw_dec_layouts[child_layout_dec][0] < min_payout):
					min_payout = raw_dec_layouts[child_layout_dec][0]
					
			if (min_payout != None):
				raw_dec_layouts[cur_layout_dec][0] = min_payout
		
		
	return raw_dec_layouts
		
	
def load_cached_maximin_tree(data_dir):
	"""
	Reads maximin decision tree from cache,
	or build it and store, if no cache still exists
	"""
	
	global full_maximin_decision_tree
	
	try:
		dtree_f = gzip.open(data_dir + "/maximin_tree.gzpckl", "rb")
		full_maximin_decision_tree = pickle.load(dtree_f)
		dtree_f.close()
	except:
		try:
			declayouts_f = gzip.open(data_dir + "/raw_dec_layouts.gzpckl", "rb")
			both_raw_dec_layouts = pickle.load(declayouts_f)
			declayouts_f.close()
			
		except:
			both_raw_dec_layouts = __build_and_store_dec_layouts(data_dir)
			
		
		# build and store maximin decision tree	
		full_maximin_decision_tree = { 
				"cross" : build_maximin_decision_tree(
									SIDES_NOMINALS["cross"], 
									both_raw_dec_layouts["cross"]
				),
				"nought" : build_maximin_decision_tree(
									SIDES_NOMINALS["nought"], 
									both_raw_dec_layouts["nought"]
				)
		}
		
		dump_file = gzip.open(data_dir + "/maximin_tree.gzpckl", "wb")
		pickle.dump(full_maximin_decision_tree, dump_file, pickle.HIGHEST_PROTOCOL)
		dump_file.close()
		
		
def __build_and_store_dec_layouts(data_dir):
	both_raw_dec_layouts = { 
				"cross" : __build_field_layouts_dec(SIDES_NOMINALS["cross"]),
				"nought" : None
	}
	
	both_raw_dec_layouts["nought"] = deepcopy(both_raw_dec_layouts["cross"])
	
	# invert payouts for the other side
	for dec_layout in both_raw_dec_layouts["nought"].iterkeys():
		if ((both_raw_dec_layouts["nought"][dec_layout][0] != None) and
			(np.abs(both_raw_dec_layouts["nought"][dec_layout][0]) == 1.0)):
			
			both_raw_dec_layouts["nought"][dec_layout][0] = \
				-both_raw_dec_layouts["nought"][dec_layout][0]
	
	# store	
	dump_file = gzip.open(data_dir + "/raw_dec_layouts.gzpckl", "wb")
	pickle.dump(both_raw_dec_layouts, dump_file, pickle.HIGHEST_PROTOCOL)
	dump_file.close()
	
	return both_raw_dec_layouts
	
	
def init(side_name):
	"""
	Initialize AI by bulding whole decision tree
	
	side_name could either be:
	"nought" or "cross"
	"""
	
	global my_side, my_side_name
	
	my_side = SIDES_NOMINALS[side_name]
	my_side_name = side_name
	
	load_cached_maximin_tree("data")
	
	
	
def make_move(field, reinf = 0.0):
	"""
	returns altered (my move) field
	"""
	
	assert(full_maximin_decision_tree != None)
	assert(my_side_name != "")
	
	new_layout_dec = \
		full_maximin_decision_tree[my_side_name]\
			[__ndarray_to_dec_layout(field * 2)][3]
	
	field[:] = __dec_layout_to_ndarray(new_layout_dec) * 0.5
	

def rank_move(field_before, field_after, side_name):
	"""
	return relative score (worst == 0, best == 1) of move made by
	'side_name'
	
	'field_before' - field layout before move
	'field_after' - field layout after move
	"""
	
	field_before_dec = __ndarray_to_dec_layout(field_before * 2)
	
	### whether proper side is ranked...
	assert(len(full_maximin_decision_tree[side_name][field_before_dec]) >= 5)
	###
	
	move_id = full_maximin_decision_tree[side_name][field_before_dec][1].index(
				__ndarray_to_dec_layout(field_after * 2)		
	)
	return full_maximin_decision_tree[side_name][field_before_dec][4][move_id]
	
	

#================================================================================
# TEST CODE
#================================================================================

if (__name__ == "__main__"):
	init("nought")
	
	"""
	print my_side_name
	#for field, decision in full_maximin_decision_tree[my_side_name].iteritems():
	#	print field
	#	print decision
	#	print "\n"
	
	declayouts_f = gzip.open("data/raw_dec_layouts.gzpckl", "rb")
	both_raw_dec_layouts = pickle.load(declayouts_f)
	declayouts_f.close()
	
	#for field, decision in both_raw_dec_layouts[my_side_name].iteritems():
	#	print field
	#	print decision
	#	print "\n"
	
	#tt = {
	#"nought" : build_maximin_decision_tree(SIDES_NOMINALS["nought"], both_raw_dec_layouts["nought"]),
	#"cross" : build_maximin_decision_tree(SIDES_NOMINALS["cross"], both_raw_dec_layouts["cross"])
	#}
	
	tt = { 
				
				
		
				"nought" : build_maximin_decision_tree(
									SIDES_NOMINALS["nought"], 
									both_raw_dec_layouts["nought"]
				),
				"cross" : build_maximin_decision_tree(
									SIDES_NOMINALS["cross"], 
									both_raw_dec_layouts["cross"]
				)
	}
	
	
	for field, decision in both_raw_dec_layouts["cross"].iteritems():
		print field
		print decision
		print "\n"
		
	print "=====================================\n"
	
	tt1 = build_maximin_decision_tree(
									SIDES_NOMINALS["nought"], 
									both_raw_dec_layouts["nought"]
				)
	
	for field, decision in both_raw_dec_layouts["cross"].iteritems():
		print field
		print decision
		print "\n"
	
	tt2 = build_maximin_decision_tree(
									SIDES_NOMINALS["cross"], 
									both_raw_dec_layouts["cross"]
				)
	#print tt
	
	
	for field, decision in tt2.iteritems():
		print field
		print decision
		print "\n"
	"""