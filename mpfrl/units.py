"""
	General Memory-Prediction Framework hierarchy unit "template"
	and several implementations:
		1. LoopSOM with RL extension (seems unreliable)
		2. SOM-RSOM pair with inner and global prediction loops
"""

from common import *
from noise import *

MPF_UT_SENSOR = 1
MPF_UT_ACTUATOR = 2
MPF_UT_INTERNAL = 3

class _Base_MPF_Unit:
	"""
	
	Base class for derving various MPF unit's implementation
	
	This class provides basic units hierarchy functions:
	1. input space distribution
	2. hierarchy "establishment"
	3. automated backward pass after forward pass
	
	NOTE: Quite straight-forward recursive approach is employed in here
	TODO: Rewrite it to something less resource demanding and beautiful
	
	Inherited classes MUST implement two function:
	1. '_forward_pass_kernel' which actually performs forward pass
	2. '_backward_pass_kernel' which actually performs backward pass
	
	"""
	
	def __init__(self, ss_class, ts_class, input_dim, ss_shape, ts_shape, 
					parent_unit, unit_type, unit_level = None, h = None):
		
		# Type of unit (used by containing hierarchy)
		self.unit_type = unit_type
		if (unit_type == MPF_UT_SENSOR) or (unit_type == MPF_UT_ACTUATOR):
			self.unit_level = 0
		else:
			self.unit_level = unit_level
		
		noise_magn_decrease = 0.0001
		if (self.unit_level != None):
			# let noise decrease depened exponentially on level id
			noise_magn_decrease *= 10**(-self.unit_level)
		
		# Spatial SOM (Spatial pooler)
		self.ss = ss_class(ss_shape, input_dim, 
						noise = UniformNoise(-0.5, 0.5, 1.0, noise_magn_decrease)
		)
		
		# Temporal SOM (Temporal pooler)
		# NOTE: If enabled!
		if ((ts_class == None) or (ts_class == None.__class__)):
			self.has_ts = False
			
			# just temporary compatiblity solution
			self.ts = self.ss
			
		else:
			self.has_ts = True
			
			self.ts = ts_class(ts_shape, ss_shape[0] * ss_shape[1], 
							rsom_ext = True,
							noise = UniformNoise(-0.5, 0.5, 1.0, noise_magn_decrease)
			)
		
		# Adjust tree of units
		self.children_units = []
		self.parent_unit = parent_unit
		
		if (self.parent_unit != None):
			self.parent_unit.add_child(self)
			
		# Link to containing hierarchy
		# (set by MPF_Hierarchy instance)
		self._hierarchy = h
		
		# - Input to SS accumulator when collecting children's outputs
		# - Output generated from SS in backward pass
		self._accu_ss_io_vec = zeros(self.ss.neurons.shape[1])
		
		# Attributes to store in matlab file
		self._stored_attr_names = ["unit_level"]
		
	def _to_matlab_mat(self):
		"""
		returns dictionary with interesting arrays and structures
		"""
		
		res_d = dict()
		
		for attr_name in dir(self):
			if ((getattr(self, attr_name).__class__ == ndarray) or
				(attr_name in self._stored_attr_names)):
				
				res_d[attr_name.lstrip("_")] = getattr(self, attr_name)
		
		# store spatial and temporal poolers
		res_d["ss"] = self.ss._to_matlab_mat()
		
		if (self.has_ts):
			res_d["ts"] = self.ts._to_matlab_mat()
				
		return res_d
			
	def add_child(self, child_unit):
		#assert(self.ss.neurons.shape[1] != child_unit.ts.neurons.shape[0])
		
		child_unit.parent_unit = self
		
		if (len(self.children_units) > 0):
			child_unit._pu_iv_range = [
								self.children_units[-1]._pu_iv_range[1], 
								self.children_units[-1]._pu_iv_range[1] + \
									child_unit.ts.neurons.shape[0]
			]
		else:
			child_unit._pu_iv_range = [0, child_unit.ts.neurons.shape[0]]
			
		self.children_units.append(child_unit)
		
		#print self.ss.neurons.shape
		#print child_unit._pu_iv_range
		#print "--------------------------\n\n"
		assert(self.ss.neurons.shape[1] >= child_unit._pu_iv_range[1])
		
		# accumulator's counter
		self._child_inputs_num = 0
		
	
	def forward_pass_from_child(self, child_unit):
		self._accu_ss_io_vec[
					child_unit._pu_iv_range[0]:child_unit._pu_iv_range[1]
		] =	child_unit.ts.act_vec
		
		self._child_inputs_num += 1
		
		if (self._child_inputs_num >= len(self.children_units)):
			self._child_inputs_num = 0
			self.forward_pass(self._accu_ss_io_vec)
			
	
	def _forward_pass_kernel(self, input_vec):
		raise NotImplementedError
	
	def forward_pass(self, input_vec):
		"""
		Performs forward pass of an input vector
		activating whole hierarchy from bottom to top
		"""
		
		# actually perform forward pass
		# 'ts.act_vec' should be properly initialized
		self._forward_pass_kernel(input_vec[:])
		
		# pass result to parent
		if (self.parent_unit != None):
			self.parent_unit.forward_pass_from_child(self)
			
		#else:
			# in top unit
			# -- perform backward pass to children
			
			#
			#self.backward_pass(self.ts.act_vec[:])
			#
			# OR
			#
			#self.backward_pass(random.uniform(0.0, 1.0, self.ts.act_vec.shape))
		
	def _backward_pass_kernel(self, ts_act_vec):
		raise NotImplementedError
	
	def backward_pass(self, ts_act_vec):
		"""
		Performs backward pass thus generating values in SS input domain
		(i.e. global prediction)
		
		Those values are passed from top to bottom (down the hierarchy)
		
		OBSOLETE: This function is initially invoked by 'forward_pass' and thus shouldn't
		be called distinctly  

		"""
		
		# after call to this function, self._accu_ss_io_vec should be 
		# properly initialized:
		# this vector represents output from current unit
		self._backward_pass_kernel(ts_act_vec[:])
		
		# distribute output through-out children
		for child_unit in self.children_units:
			child_unit.backward_pass(
						self._accu_ss_io_vec[
							child_unit._pu_iv_range[0]:
							child_unit._pu_iv_range[1]
						]
			)


#================================================================================
# LoopSOM-inspired MPF unit implementation
# this impl. is quite useless actually and kept here for future revise and
# removal :)
#================================================================================

class MPF_Unit_LoopSOM(_Base_MPF_Unit):
	"""
	
	Memory-prediction framework hierarchy's unit implementation
	based on LoopSOM approach [Rafael C. Pinto and Paulo M. Engel, 2009]

	Also, original LoopSOM doesn't have backward pass
	(i.e. "GSOM" for both temporal and spatial SOMs)
	
	Reinforcement Learning extension is quite stupid in here :)
	
	"""
	
	def __init__(self, **kwargs):
		_Base_MPF_Unit.__init__(self, **kwargs)
		
		# SS activation predictions from TS-only and TS-from-hierarchy
		self.ss_act_local_pred = zeros(self.ss.neurons.shape[0])
		self.ss_act_global_pred = zeros(self.ss.neurons.shape[0])
	
	def _forward_pass_kernel(self, input_vec):
		"""
		very doubtful reward introduction in here ...
		"""
		
		
		if (self.ts.last_model_bias == None): # t = 0, special case
			# no inner prediction at all
			
			self.ss.feed(input_vec)
			self.ts.feed(self.ss.act_vec)
			
		else: # t > 0
			# inner prediction must flow ;)
			#
			# -- find SS's original activation vector, keeping SS unaltered
			# -- (i.e. activation vector not corrected by temporal pooler)
			self.ss.find_bmu(input_vec, None, True)
			
			# -- confidences
			# -- based on model biases
			#
			# NOTE: Global prediction confidence should be calculated from
			#		top node model_bias
			# TODO: Find other ways!
			#
			# TODO #2: Implement weights of predictions as parameters
			#
			# TODO #3: Find out how to incorporate reinforcement better!
			#
			# ---- spatial
			conf_s = 1.0 - 0.5 * self.ss.last_model_bias
			
			# ---- temporal (local prediction)
			conf_t_local = 1.0 - 0.5 * self.ts.last_model_bias + \
					0.4 * self._hierarchy.reinforcement_prime
			
			# ---- temporal (global prediction)
			# ---- reinforcement's prime (should be clamped to [0, 1]) is 
			# ---- also taken into account
			conf_t_global = 1.0 - \
					0.5 * self._hierarchy.top_unit.ts.last_model_bias + \
					0.4 * self._hierarchy.reinforcement_prime
			
			# -- calculate adjusted (by prediction) SS's activation vector
			# -- and find new BMU
			ss_adj_act_vec = \
					(conf_s * self.ss.act_vec + 
					 conf_t_local * self.ss_act_local_pred +
					 conf_t_global * self.ss_act_global_pred) / \
					(conf_s + conf_t_local + conf_t_global)
			
			ss_adj_bmu_ind = argmax(ss_adj_act_vec)
			
			# -- update Spatial SOM at last
			self.ss.update_neurons(ss_adj_bmu_ind, input_vec)
			
			# -- feed Temporal SOM (RSOM)
			self.ts.feed(ss_adj_act_vec)
			
			# -- local prediction (from RSOM's currect activation)
			# -- for next forward pass
			self.ss_act_local_pred[:] = self.ts.generate(self.ts.act_vec, 1)
	
	def _backward_pass_kernel(self, ts_act_vec):
		"""
		quite simple backward pass
		"""
		
		self.ss_act_global_pred[:] = self.ts.generate(ts_act_vec[:], 1)
		
		self._accu_ss_io_vec[:] = self.ss.generate(self.ss_act_global_pred[:], 1)
	
#================================================================================
# MPF unit implementation according to
# [David Rawlinson, Gideon Kowaldo - 
#	"Generating Adaptive Behaviour within a Memory-Prediction Framework", 2012]
#
# This seems to be the most adequate impl
#================================================================================

class MPF_Unit_RL(_Base_MPF_Unit):
	"""
	
	Memory-prediction framework hierarchy's unit implementation
	based on approach introduced by David Rawlinson and Gideon Kowaldo in
	their paper
	["Generating Adaptive Behaviour within a Memory-Prediction Framework", 2012]
	
	"""
	
	def __init__(self, **kwargs):
		_Base_MPF_Unit.__init__(self, **kwargs)
		
		# enable local predictor based on markov chain for Spatial SOM
		self.ss.init_predictor()
		
		# SS activation predictions from TS-only and TS-from-hierarchy
		self.ss_act_vec_local_pred = ones(self.ss.act_vec.shape[0])
		self.ss_act_vec_global_pred = ones(self.ss.act_vec.shape[0])
		
		self.ss_act_vec_total_pred = ones(self.ss.act_vec.shape[0])
		
		# reward correlator's learning-rate
		# TODO: add learning-rate decrease!
		self.rw_learning_rate = 1.0
		self.rw_learning_rate_decr = 0.001
		self.min_rw_learning_rate = 0.01
		
		# TS activation vector bias influence factor
		# TODO: also add decrease!
		self.rw_bias_influence = 1.0
		self.rw_bias_influence_decr = 0.001
		self.min_rw_bias_influence = 0.1
		
		# last temporal SOM's output (activation vector) scaled by 
		# rewards correlator's learning-rate
		self.__last_ts_act_vec = zeros(self.ts.act_vec.shape) 
		
		# backward pass temporal pooler activation vector bias
		# NOTE: could be used in forward pass, btw
		self.__ts_act_vec_bias = ones(self.ts.act_vec.shape)
		
		# correlation between reward and unit's output:
		# forward pass tempolar pooler activation vector
		self.__reward_corr = ones(self.ts.act_vec.shape)
		
		# -- adjusting function for reward correlation to be used
		# -- in activation vector bias calculation
		# NOTE: Sigmoid function is used, suggested in paper
		self._rcorr_adj_func = lambda rcorr: \
						1.0 / (1.0 + exp(-(((rcorr + 1.0) * 5.0) - 5.0))) - 0.5
						
		# attributes to store
		self._stored_attr_names.extend(["rw_learning_rate", "rw_bias_influence"])
		
		
	
	def _forward_pass_kernel(self, input_vec):
		"""
		TODO #1: Revise!
		TODO #2: Optimize!
		"""
		
		
		# find unbiased activation vector
		self.ss.find_bmu(input_vec, None, True)
		
		# bias it by local prediction and global predictions
		self.ss.act_vec *= self.ss_act_vec_total_pred
							
		# activation vector should be PMF (i.e. normalized likelihood)
		ss_act_vec_norm_factor = sum(self.ss.act_vec)
		if (ss_act_vec_norm_factor == 0.0): ss_act_vec_norm_factor = EPS
		
		self.ss.act_vec /= ss_act_vec_norm_factor
							
		# update neurons's weights
		# TODO: is it valid idea?
		ss_adj_bmu_ind = argmax(self.ss.act_vec)
		self.ss.update_neurons(ss_adj_bmu_ind, input_vec)
		
		# locally predict next SS's activation vector
		# TODO: Should it be BEFORE or AFTER neurons update?
		# QUESTION: May be better predict by orthogonal activation vector?
		#
		self.ss_act_vec_local_pred[:] = self.ss.predict_next_act_vec()
		
		### (IS THIS REALLY NEEDED, as long as activation vector is
		### already normalized?!)
		try:
			self.ss_act_vec_local_pred /= sum(self.ss_act_vec_local_pred)
		except:
			print self.ss_act_vec_local_pred 
		###
		
		# temporaly classify biased activation vector
		if (self.has_ts):
			# vector desired to be highly orthogonal in order to reduce 
			# uncertainty in RSOM
			self.ss.act_vec[:] = 0.0
			self.ss.act_vec[ss_adj_bmu_ind] = 1.0
			
			self.ts.feed(self.ss.act_vec[:])
		
			### The same as for SS: RSOM's activation vector must be normalized
			### likelihood - proper PMF! 
			self.ts.act_vec /= sum(self.ts.act_vec)
			###
		
		# prepare TS activation bias (from reinforcement) for 
		# backward pass
		# using previous (t-1) unit's output (TS activation vector)
		self.__reward_corr[:] = self.__last_ts_act_vec * \
								self._hierarchy.reinforcement_prime + \
								(1.0 - self.__last_ts_act_vec) * \
								self.__reward_corr
								
		self.__ts_act_vec_bias[:] = max([
						EPS, 
						max(min([
							1.0,
							min(self._rcorr_adj_func(self.__reward_corr[:]) * \
								self.rw_bias_influence + \
								1.0 / self.ts.act_vec.shape[0]) # uniform constant for fun :) 
						]))
		])
		
		# store unit's output for next forward pass
		# (i.e. Temporal SOM's activation vector)
		self.__last_ts_act_vec = self.ts.act_vec * self.rw_learning_rate
		
		# decreae learning rate and bias influence
		self.rw_learning_rate -= self.rw_learning_rate_decr
		if (self.rw_learning_rate < self.min_rw_learning_rate):
			self.rw_learning_rate = self.min_rw_learning_rate
			self.rw_learning_rate_decr = 0.0
			
		self.rw_bias_influence -= self.rw_bias_influence_decr
		if (self.rw_bias_influence < self.min_rw_bias_influence):
			self.rw_bias_influence = self.min_rw_bias_influence
			self.rw_bias_influence_decr = 0.0
	
	def _backward_pass_kernel(self, ts_act_vec):
		"""
		TODO: Watchout arrays-by-view passing! Carefully check
		
		TODO #2: Optimize - a lot of unneeded normalizations probably!
		"""
		
		# adjust unit's input in backward pass
		# (i.e. temporal pooler (Temporal SOM) activation vector)
		# by result of reward correlation
		
		###
		ts_act_vec /= sum(ts_act_vec)
		###
		
		ts_act_vec *= self.__ts_act_vec_bias
		ts_act_vec /= sum(ts_act_vec)
		
		
		
		# generated output will be used dually:
		# 1. For backward pass Spatial SOM's activation vector
		# 2. For next (t+1) forward pass Spatial SOM's output act_vec adjustment
		#	along with its own predictor
		#
		if (self.has_ts):
			self.ss_act_vec_global_pred[:] = \
								self.ts.generate(ts_act_vec[:], 1)[0, :]
								
			###
			self.ss_act_vec_global_pred /= sum(self.ss_act_vec_global_pred)
			###
		
		# 'ts_act_vec' is already a global prediction in case of lack of RSOM
		else:
			self.ss_act_vec_global_pred[:] = ts_act_vec
		
		
		# unite global and local predictions and add uniform probabilities for
		# "plasticity" as suggested in original paper
		self.ss_act_vec_total_pred[:] = self.ss_act_vec_global_pred * \
										self.ss_act_vec_local_pred + \
										1.0 / self.ss.act_vec.shape[0]
		self.ss_act_vec_total_pred /= sum(self.ss_act_vec_total_pred)
		
		# pass this "total" prediction to SOM
		self._accu_ss_io_vec[:] = \
					self.ss.generate(self.ss_act_vec_total_pred[:], 1)[0, :]
	