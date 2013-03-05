"""
	Memory-Prediction Framework hierarchy implementation with 
	reinforcement learning extension (i.e. with reinforcement's derivative calculation)1
	
	Conviniet wrapper for actual structure held by MPF_Unit instances
	
	Contains helper functions for automated hierarchy building
"""

from common import *
from SOM import *
from units import *

from scipy.io import savemat

class MPF_Hierarchy:
	"""
	
	Container for 'MPF_Unit' instances
	manages reinforcement and acts like conviniet interface
	between bunch of bottom-level (L0) units and user
	
	Also automatically build hierarchy, given only L0 units
	(i.e. "sensomotor" units in the bottom of hierarchy) and desired
	number of levels 
	
	"""
	
	def __init__(self, l0_units, levels_num, dump_period = 0, dump_path = "", 
					ss_class = None, ts_class = None):
		# Output vector after hierarchy evaluation
		# this vector is a prediction of next input
		self.output_vec = zeros(
				reduce(
					lambda a, u: a + u.ss.neurons.shape[1],
					l0_units,
					0
				)
		)
		
		# store classes for constructing hierarchy
		# -- unit class
		self.__mpf_unit_class = l0_units[0].__class__
		
		# -- spatial SOM class
		if (ss_class == None):
			self.__spatial_som_class = l0_units[0].ss.__class__
		else:
			self.__spatial_som_class = ss_class
		
		# -- RSOM (temporal SOM) class	
		if (ts_class == None):
			self.__temporal_som_class = l0_units[0].ts.__class__
		else:
			self.__temporal_som_class = ts_class
		
		# parts of input (and output!) vector associated to units
		self.l0_iv_ranges = []
		
		cur_iv_pos = 0
		for unit in l0_units:
			self.l0_iv_ranges.append(
						[cur_iv_pos, cur_iv_pos + unit.ss.neurons.shape[1]]
			)
			
			cur_iv_pos += unit.ss.neurons.shape[1]
		
		# Approx. first derivative of reinforcement
		self.reinforcement_prime = 0.0
		self.max_abs_reinforcement_prime = 0.0
		
		self._prev_reinforcement_prime = 0.0
		self._prev_reinforcement = 0.0
		#self._max_reinforcement_delta = 2.0
		self._reinforcement_prime_decay = 0.7
		
		# Build hierarchy
		self.l0_units = l0_units # for convinience
		
		for unit in self.l0_units:
			unit._hierarchy = self
		
		self.units = []
		#self.units.extend(self.l0_units)
		
		# time passed from hierarchy creation
		# each iteration (i.e. t = t + 1) occurs after
		# forward and subsequent passes
		self.t = 0
		
		# attributes to store
		self._stored_attr_names = [
						"t",
						"reinforcement_prime",
						"max_abs_reinforcement_prime"
		]
		
		# storing parameters
		self.dump_period = dump_period
		self.dump_path = dump_path
		
		# -- prepare dictionary for dumping
		self._dump_dict = dict()
		
		# try to automatically construct hierarchy
		self.__construct_hierarchy(l0_units, levels_num)
		
	def _check_should_dump(self):
		"""
		returns True if hierarchy should be stored in .MAT file
		False otherwise
		"""
		
		if ((self.dump_period > 0) and (self.t % self.dump_period == 0)):
			return True
		
		return False
			
	def _to_matlab_mat(self, dump_subname):
		"""
		prepares hierarchy for storing in .MAT-file
		"""
		
		if (not self._check_should_dump()): return
		
		res_d = dict()
		
		for attr_name in dir(self):
			attr = getattr(self, attr_name)
			
			if (((hasattr(attr, "__class__")) and (attr.__class__ == ndarray)) or
				(attr_name in self._stored_attr_names)):
				res_d[attr_name] = attr
		
		# dump units
		unit_counter = 0
		
		for unit in self.l0_units + self.units:
			res_d["unit_L%d__%.3d" % (unit.unit_level, unit_counter)] = \
				unit._to_matlab_mat()
				
			unit_counter += 1
			
		# place resulting dump in specific place
		self._dump_dict[dump_subname] = res_d
		
	def _dump_hierarchy(self):
		"""
		stores prepared hierarchy to matlab file
		"""
		
		if (not self._check_should_dump()): return
		
		# store at last
		savemat(
				self.dump_path + "/h_%d.mat" % (self.t), 
				self._dump_dict,
				oned_as = "column",
				do_compression = True
		)
		
	def __construct_hierarchy(self, l0_units, levels_num):
		"""
		Constructs hierarchy give only L0 ("sensomotor") units and
		desired number of levels
		"""
		
		assert(levels_num >= 2)
		
		def _add_unit(children, ss_ts_shapes, level_id):
			new_unit = self.__mpf_unit_class(
				ss_class = self.__spatial_som_class,
				ts_class = self.__temporal_som_class,
											
				input_dim = reduce(
					lambda a, u: a + u.ts.neurons.shape[0],
					children,
					0
				),
									
				# arbitary values for SS and TS shapes
				ss_shape = ss_ts_shapes[0], 
				ts_shape = ss_ts_shapes[1],
				
				parent_unit = None,
				unit_type = MPF_UT_INTERNAL,
				unit_level = level_id,
				h = self
			)
			
			for child_unit in children:
				new_unit.add_child(child_unit)
				
			self.units.append(new_unit)
			
			return new_unit
		
		
		# construct hierarchy by following rules:
		# - exactly one top node
		# - each subsequent top level has half of units than previous
		#
		# TODO: Find out some formula(s) for SS and TS shapes depending on
		#		level. Genetic algorithms or Random search?? 
		#
		lk_units = l0_units
			
		for level_id in xrange(levels_num - 2):
			new_units = []
			new_units_num = int(floor(len(lk_units) / 2))
			
			for i in xrange(new_units_num):
				first_child_id = i * 2
				last_child_id = (i+1) * 2
				
				if (i == (new_units_num - 1)) and (last_child_id < len(lk_units)):
					last_child_id = len(lk_units)
				
				new_units.append(
								_add_unit(
									lk_units[first_child_id:last_child_id],
									((3, 3), (4, 4)),
									level_id + 1
								)
				)
			
			lk_units = new_units
			
		# add top node at last
		self.top_unit = _add_unit(lk_units, ((20, 20), (10, 10)), levels_num - 1)
	
	def evaluate(self, input_vec, reinforcement):
		"""
		Evaluate the hierarchy once (forward and backward pass)
		
		NOTE: 'reinforcement' should be in [-1, 1]!
		"""
		
		"""
		# update reinforcement's first derivative
		if (self.max_abs_reinforcement_prime == 0.0):
			self.reinforcement_prime = (reinforcement - self._prev_reinforcement)
		else:
			self.reinforcement_prime = (reinforcement - self._prev_reinforcement) / \
										self.max_abs_reinforcement_prime
										
		if (abs(self.reinforcement_prime) > self.max_abs_reinforcement_prime):
			self.max_abs_reinforcement_prime = abs(self.reinforcement_prime)
		
		self._prev_reinforcement = reinforcement
		
		# -- don't forget about derivative at time t-1
		self.reinforcement_prime = \
			self._reinforcement_prime_decay * self.reinforcement_prime + \
			(1 - self._reinforcement_prime_decay) * self._prev_reinforcement_prime
			
		self._prev_reinforcement_prime = self.reinforcement_prime 
		"""
		
		# Try out
		self.reinforcement_prime = reinforcement

		
		# -- pass input_vec to L0 units
		# -- i.e. perform forward pass
		for i in xrange(len(self.l0_units)):
			self.l0_units[i].forward_pass(
						input_vec[self.l0_iv_ranges[i][0]:self.l0_iv_ranges[i][1]]
			)
			
		### dump hierarchy after FORWARD PASS
		self._to_matlab_mat("after_forward")
		###
		
		# -- perform backward pass
		# -- NOTE: now for convinience it should be performed explicitly!
		self.top_unit.backward_pass(random.uniform(0.0, 1.0, self.top_unit.ts.act_vec.shape))
		#
		# OR
		#
		#self.top_unit.backward_pass(self.ts.act_vec[:])
	
		# merge results of backward pass into output vector
		for i in xrange(len(self.l0_units)):
			self.output_vec[self.l0_iv_ranges[i][0]:self.l0_iv_ranges[i][1]] = \
				self.l0_units[i]._accu_ss_io_vec
				
		### dump hierarchy after BACKWARD PASS
		### and actually save dump
		self._to_matlab_mat("after_backward")
		
		self._dump_hierarchy()
		###
		
		# increase passed time
		self.t += 1
		
		# just temporary for single actuator in last unit
		return self.output_vec[-self.l0_units[-1].ss.neurons.shape[1]:]
