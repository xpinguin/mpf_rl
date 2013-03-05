import numpy as np
import pickle

FIELD_SIZE = 9
SIDES_NOMINALS = {"cross" : 1.0, "nought" : 0.5}

#my_side = SIDES_NOMINALS["nought"]
my_side = None

__b3_b10 = np.array([3**i for i in xrange(FIELD_SIZE)])

# prebuilt layouts tree
__field_dec_layouts = None

# prebuilt Wald's maximin tree
__maximin_decision_tree = None

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
			
		return 0.0
			
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
		
		res_layouts[cur_layout_dec] = [__layout_payout(cur_layout), []]
		if (res_layouts[cur_layout_dec][0] != 0.0): continue
		
		
		for i in xrange(9):
			child_layout = __evolve_layout(cur_layout.copy(), i)
			if (child_layout == None): break
			
			res_layouts[cur_layout_dec][1].append(
										__ndarray_to_dec_layout(child_layout)
			)
			
			layouts_queue.insert(0, child_layout)
			
		# handle drawn game (nobody wins)
		if (len(res_layouts[cur_layout_dec][1]) == 0):
			res_layouts[cur_layout_dec][0] = 0.5
			
	return res_layouts
		
	
def __build_maximin_decision_tree():
	"""
	builds Wald's maximin decision tree from prebuilt layouts
	"""
	
	global __maximin_decision_tree
	global __field_dec_layouts
	
	if (__field_dec_layouts == None): return False
	
	# update branches payouts for further usage with Wald's maximin model
	# i.e.
	# branch payout = min(children payouts) 
	layouts_queue = [
					dec_layout for (dec_layout, props) in \
						 __field_dec_layouts.iteritems() if props[0] == 0.0
	]
	
	for l in layouts_queue:
		__field_dec_layouts[l][0] = None
	
	while (len(layouts_queue) > 0):
		cur_layout_dec = layouts_queue.pop()
		
		"""
		min_payout = 1e+20
		
		for child_layout_dec in __field_dec_layouts[cur_layout_dec][1]:
			if (__field_dec_layouts[child_layout_dec][0] == None):
				layouts_queue.insert(0, cur_layout_dec)
				min_payout = None
				
				break
			
			if (__field_dec_layouts[child_layout_dec][0] < min_payout):
				min_payout = __field_dec_layouts[child_layout_dec][0]
				
		if (min_payout != None):
			__field_dec_layouts[cur_layout_dec][0] = min_payout
		"""	
		
		avg_payout = 0.0
		
		for child_layout_dec in __field_dec_layouts[cur_layout_dec][1]:
			if (__field_dec_layouts[child_layout_dec][0] == None):
				layouts_queue.insert(0, cur_layout_dec)
				avg_payout = None
				
				break
			
			avg_payout += __field_dec_layouts[child_layout_dec][0]
				
		if (avg_payout != None):
			__field_dec_layouts[cur_layout_dec][0] = avg_payout / \
							len(__field_dec_layouts[cur_layout_dec][1])
			
	#for props in __field_dec_layouts.itervalues():
	#	print props[0]
			
	# create decision tree that maximizes payout
	__maximin_decision_tree = dict()
	
	for (dec_layout, props) in __field_dec_layouts.iteritems():
		max_payout = -1e+99
		max_payout_children = None
		
		for child_dec_layout in props[1]:
			if (__field_dec_layouts[child_dec_layout][0] > max_payout):
				max_payout = __field_dec_layouts[child_dec_layout][0]
				max_payout_children = child_dec_layout
		
		__maximin_decision_tree[dec_layout] = max_payout_children
		
	# that's all
	return True
		
		
def build_and_store_dec_layouts():
	global __field_dec_layouts
	
	field_dec_layouts = __build_field_layouts_dec(SIDES_NOMINALS["nought"])
	
	dump_file = open("dec_layouts_nought.pickle", "wb")
	pickle.dump(field_dec_layouts, dump_file)
	dump_file.close()
	
	if (my_side == SIDES_NOMINALS["nought"]):
		__field_dec_layouts = field_dec_layouts.copy()
	
	# invert payouts for the other side
	for dec_layout in field_dec_layouts.iterkeys():
		if (np.abs(field_dec_layouts[dec_layout][0]) == 1.0):
			field_dec_layouts[dec_layout][0] = -field_dec_layouts[dec_layout][0]
	
	dump_file = open("dec_layouts_cross.pickle", "wb")
	pickle.dump(field_dec_layouts, dump_file)
	dump_file.close()
	
	if (my_side == SIDES_NOMINALS["cross"]):
		__field_dec_layouts = field_dec_layouts.copy()
	
	
	
def init(side_name):
	"""
	Initialize AI by bulding whole decision tree
	
	side_name could either be:
	"nought" or "cross"
	"""
	
	global __field_dec_layouts
	global __maximin_decision_tree
	
	global my_side
	
	my_side = SIDES_NOMINALS[side_name]
	
	try:
		dtree_f = open("maximin_tree_" + side_name + ".pickle", "rb")
		__maximin_decision_tree = pickle.load(dtree_f)
		dtree_f.close()
		
	except:
		try:
			declayouts_f = open("dec_layouts_" + side_name + ".pickle", "rb")
			__field_dec_layouts = pickle.load(declayouts_f)
			declayouts_f.close()
			
		except:
			build_and_store_dec_layouts()
			
		
		# build and store maximin decision tree	
		res = __build_maximin_decision_tree()
		assert(res == True)
		
		dump_file = open("maximin_tree_" + side_name + ".pickle", "wb")
		pickle.dump(__maximin_decision_tree, dump_file)
		dump_file.close()
	
	
	
def make_move(field, reinf = 0.0):
	"""
	returns altered (my move) field
	"""
	
	assert(__maximin_decision_tree != None)
	
	new_layout_dec = __maximin_decision_tree[__ndarray_to_dec_layout(field * 2)]
	
	field[:] = __dec_layout_to_ndarray(new_layout_dec) * 0.5
	


#================================================================================
# TEST CODE
#================================================================================

if (__name__ == "__main__"):
	init("nought")
	#print __dec_layout_to_ndarray(5)
	