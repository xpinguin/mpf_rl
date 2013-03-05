"""
	Different kinds of Self-Organized Maps are implemented here:
	
	== "Spatial" ==
	1. Kohonen's SOM
	2. Parameterless SOM [Berglund and Sitte, 2006]
	
	== "Temporal" ==
	1. RSOM based on Kohonen's SOM
	2. RSOM based on PL-SOM
"""

from common import *
from sklearn.mixture import GMM

from noise import *


#================================================================================

class _Template_SOM:
	"""
	
	Template for deriving specific kinds of Self-Organizing Maps
	
	Temporal extension (RSOM) is enabled by passing 'rsom_ext = True' as
	argument to constructor
	
	Generative extension has been implemented using GMM in a following way:
	 1. SOM treated like a mixture of gaussians, where N = lattice width * lattice height
	 2. Each gaussian is multivariate distributions with mean = weight vector and
	 	covariance is calculated through distances between its direct neighbours
	 3. Inference is performed like in a derived actual SOM, so no EM here
	 4. Each mixture component has proportional coefficient equal to component's activation
		 from activation vector
	
	Non-GMM generative extension also added:
	 1. Neurons indicies are treated as categorical values
	 2. Discrete probability distribution is specified above that values
	 3. [noised] weight vectors of neurons which indicies are drawn from DPD
		 described by probability density function (given activation vector) are returned   

	"""
	
	def __init__(self, lattice_shape, input_dim, **kwargs):
		# SOM's lattice shape (width and height)
		self.lattice_shape = lattice_shape
		
		# SOM's neurons (weights) organized in 2d numpy array
		self.neurons = empty((lattice_shape[0]*lattice_shape[1], input_dim), 
								dtype = FLOAT_DTYPE)
		self.neurons[:] = random.uniform(0, 1, self.neurons.shape)
		
		# enable RSOM extension if requested
		# 'decay' is normal public parameter which could be tuned if needed
		if ("rsom_ext" in kwargs.keys()) and (kwargs["rsom_ext"]):
			self.decay = 0.7
			self.__calc_diff_m = self.__calc_diff_m_rsom
			
			self.__last_diff_m = zeros(self.neurons.shape)
		else:
			self.__calc_diff_m = self.__calc_diff_m_regular
		
		# Model approximation characteristic, i.e. how close was
		# the last BMU corresponding to the last input
		self.last_model_bias = None
		
		# Activation vector: each component represents likelihood
		# that particular neuron matches given input
		#
		# NOTE: this is preallocation, actually. But it is used outside, so
		#		it is not private 
		self.act_vec = zeros(self.neurons.shape[0])
		
		# Likelihood function which is used to calculate activation vector
		self._likelihood_func = None
		
		builtin_llf = {
					"gaussian": lambda d: exp(-d / 2.0),
					"uniform": lambda d: 1.0 - d / max(d)
		}
		
		if ("likelihood_func" in kwargs):
			if ((kwargs["likelihood_func"].__class__ == str) and
				(kwargs["likelihood_func"] in builtin_llf)):
					self._likelihood_func = builtin_llf[kwargs["likelihood_func"]]
			else:
				self._likelihood_func = lambda s, d: kwargs["likelihood_func"](d)
				
		# -- uniform likelihood by default
		if (self._likelihood_func == None):
			self._likelihood_func = builtin_llf["uniform"]
			
		# Default to dummy predictor's (markov chain) 
		# state transition probabilities update function
		self.__update_state_trans_probs = lambda bmu: None
				
		
		# Associated generative model (instance of GMM)
		self.gen_model = None
		
		# Whether covariance is full or not 
		# (see 'init_generative_model' for more details)
		self.gmm_full_cov = True
		
		# how to reduce vector from neighbours to neuron's weight in covariance calculation
		#
		# NOTE: arbitary value for now!
		self.covar_diff_scale = 0.3
		
		# define some private helper variables
		# (mostly - preallocations of arrays for speed optimization)
		
		# -- difference between input and weight vectors of every neuron
		self.__diff_m = zeros(self.neurons.shape)
		
		# -- precalculated neurons' coordinates (i, j) in lattice
		self._neurons_coords = zeros((self.neurons.shape[0], 2), dtype = uint32)
		self._neurons_coords[:, 0] = mod(arange(0, self.neurons.shape[0]), lattice_shape[0])
		self._neurons_coords[:, 1] = floor(arange(0, self.neurons.shape[0]) / lattice_shape[0])
		
		# -- gen_model's covariances update function
		# -- default is to dummy function, as long as we have no
		# -- generative model by default
		self.__update_covars = lambda: None
		
		# -- "Neurons roulette":
		# -- just [noised] weight vectors of neurons which indicies
		# -- are drawn from discrete distribution are returned
		self.generate = self.__generate_dpd
		
		# -- Noise function for "roulette"
		if ("noise" in kwargs):
			self._noise_func = kwargs["noise"]
			self._noise_func.shape = self.neurons.shape[1]
			
			# brings anything constructive only for GaussianNoise
			#self._noise_func.shape = self.neurons.shape[1]
		else:
			self._noise_func = lambda: 0.0 # no noise by default
			
		# Attributes to store in .MAT file
		self._stored_attr_names = [
								"lattice_shape", "last_model_bias", # "decay"
								"_Template_SOM__last_bmu_ind"
		]
		self._excluded_attr_names = [
									"_Template_SOM__diff_m",
									"_Template_SOM__last_diff_m",
									"_neurons_coords"
		]
			
	
	def init_generative_gmm(self, gmm_cov_type = 'full'):
		"""
		Initialize SOM's generative extension (GMM, currently)
		
		'gmm_cov_type' could be equal to:
		1. 'tied' (average covariance for each mixture component)
		2. 'full' (distinct covariance for each mixture component)
		"""
		
		# GMM could treat SOM as completely distinct gaussians ('full' covariance)
		# or as gaussians with some average covariance matrix ('tied' covariance)
		assert (gmm_cov_type == 'tied') or (gmm_cov_type == 'full')
		
		if (gmm_cov_type != 'full'): self.gmm_full_cov = False
		
		# initialize generative model as GMM
		self.gen_model = GMM(n_components = self.neurons.shape[0],
							 covariance_type = gmm_cov_type)
		
		self.gen_model.means_ = self.neurons[:] # make a view
		
		if (self.gmm_full_cov):
			self.gen_model.covars_ = zeros(
						(
							self.gen_model.n_components, 
							self.neurons.shape[1], self.neurons.shape[1]
						), 
						dtype = FLOAT_DTYPE
			)
			
			self.__update_covars = self.__update_covars_full
		else:
			self.gen_model.covars_ = zeros(
						(self.neurons.shape[1], self.neurons.shape[1]), 
						dtype = FLOAT_DTYPE
			)
			self._temp_neuron_cov = zeros(
						self.gen_model.covars_.shape, 
						dtype = FLOAT_DTYPE
			)
			
			self.__update_covars = self.__update_covars_tied
		
		# -- data samples (neighbour neurons - mean neuron) organized for vectorized
		# -- covariance calculation
		self._covar_calc_data = zeros((self.neurons.shape[0]*self.neurons.shape[1], 4), 
									dtype = FLOAT_DTYPE)
		
		# -- per neuron views to _covar_calc_data
		self._covar_calc_data_views = empty((self.neurons.shape[0],), dtype="object")
		
		for i in xrange(self.neurons.shape[0]):
			self._covar_calc_data_views[i] = self._covar_calc_data[
						i*self.neurons.shape[1]:(i+1)*self.neurons.shape[1],
						:
			]
		
		# -- normalization matrix against adjacent neurons num for each neuron
		# -- (duplicated for each weight vector compononent)
		self._neurons_adj_num_norm = zeros((self._covar_calc_data.shape[0], 1), dtype = FLOAT_DTYPE)
		
		# -- indicies of adjacent neurons and its weight vectors' components
		self._adj_neurons_inds = zeros(self._covar_calc_data.shape, dtype = uint32)
		self._adj_wv_comps_inds = zeros(self._covar_calc_data.shape, dtype = uint32)
		
		# -- populate all three arrays above with valid data:
		# --- adjacent neurons number
		# --- indicies of adjacent neurons
		# --- indicies of adjacent neurons' weight vectors' components
		#
		for i in xrange(self.neurons.shape[0]):
			i_x = i % self.lattice_shape[0]
			i_y = floor(i / self.lattice_shape[0])
			
			adj_inds = [
					(i_x-1, i_y), (i_x+1, i_y), 
					(i_x, i_y-1), (i_x, i_y+1)
			]
			adj_num = len(adj_inds)
			
			local_adj_id = 0
			
			for (adj_i_x, adj_i_y) in adj_inds:
				if ((adj_i_x < 0) or (adj_i_x >= self.lattice_shape[0]) or 
					(adj_i_y < 0) or (adj_i_y >= self.lattice_shape[1])):
					adj_num -= 1
					
					# refer to self instead of an absent adjacent neuron
					adj_i_x = i_x
					adj_i_y = i_y
				
				self._adj_neurons_inds[
					i * self.neurons.shape[1]:(i+1) * self.neurons.shape[1],
					local_adj_id
				] = adj_i_y * self.lattice_shape[0] + adj_i_x
				
				local_adj_id += 1
				
			self._neurons_adj_num_norm[
				i * self.neurons.shape[1]:(i+1) * self.neurons.shape[1],
				0
			] = 1.0 / sqrt(adj_num)
			
			self._adj_wv_comps_inds[
				i * self.neurons.shape[1]:(i+1) * self.neurons.shape[1],
				0:4
			] = arange(0, self.neurons.shape[1])[:, None]
		
		# -- view to the neurons data organized in a way
		# -- suitable for covariance calculation
		self._neurons_wv_comps_flat = self.neurons.reshape(
						(self.neurons.shape[0]*self.neurons.shape[1], 1))
		
		# -- GMM as generative method
		self.generate = self.__generate_gmm
		
	def init_predictor(self):
		"""
		First-Order Markov Model prediction extension is initialized by
		calling this function
		
		Prediction extension could be used to predict the next BMU, given
		current
		
		- each neuron is treated as a state of a markov chain
		- current active state corresponds to current BMU
		- transition event from previous (t-1) BMU [i] to current (t) BMU [j] is 
			recorded in frequencies matrix in [i, j]
		- frequencies matrix is then row-normalized in order to retrieve
			markov chain's state-transition matrix
			
		NOTE: Withour prior call to this function 'predict_next_act_vec'
				won't work 
		"""
		
		# -- frequencies of transitions from one state to another
		self.__mm_freqs = zeros((self.neurons.shape[0], self.neurons.shape[0]))
		
		# -- state transition matrix
		self.__mm_trans_probs = eye(self.neurons.shape[0])
		
		# -- previous BMU
		self.__last_bmu_ind = None
		
		# -- predicted activation vector pre-cache
		self.predicted_act_vec = zeros(self.act_vec.shape)
		
		# -- state-transition matrix update
		self.__update_state_trans_probs = self.__update_state_trans_probs_fomm
		
	def _to_matlab_mat(self):
		"""
		returns dictionary with all essential properties:
		1. Numpy arrays for now
		"""
		
		res_d = dict()
		
		for attr_name in dir(self):
			if (attr_name in self._excluded_attr_names): continue
			
			attr = getattr(self, attr_name)
			
			if (((hasattr(attr, "__class__")) and (attr.__class__ == ndarray)) or
				(attr_name in self._stored_attr_names)):
				
				res_d[attr_name.lstrip("_")] = attr
				
		if ((self._noise_func.__class__ == UniformNoise) or
			(self._noise_func.__class__ == GaussianNoise)):
			res_d["noise_magn"] = self._noise_func.magn
		
		return res_d
		
	def __calc_diff_m_regular(self, input_vec):
		"""
		Normal SOM's procedure of findind difference between input vector
		and neuron's weights
		"""
		
		self.__diff_m[:] = input_vec - self.neurons
		
	def __calc_diff_m_rsom(self, input_vec):
		"""
		RSOM extension to SOM: difference between input vector and neuron's
		weights is adjusted by previous such difference and both distributed using
		decay factor 'self.decay' which is controlling "memory" deepness
		"""
		
		self.__diff_m[:] = (1 - self.decay) * self.__last_diff_m + \
					self.decay * (input_vec - self.neurons)
					
		# store __diff_m as it could be modified
		# (in 'update_neurons' for in-place optimization purposes, for instance)			
		self.__last_diff_m[:] = self.__diff_m # copy\
		
	def __update_state_trans_probs_fomm(self, bmu_ind):
		"""
		Updates frequencies and state transition matrix of first-order markov
		model (markov chain) used as predictor
		
		TODO: find a way to optimize this crap and get rid of frequencies matrix!
		"""
		
		if (self.__last_bmu_ind != None):
			self.__mm_freqs[self.__last_bmu_ind, bmu_ind] += 1
			
			self.__mm_trans_probs[self.__last_bmu_ind, :] = \
				self.__mm_freqs[self.__last_bmu_ind, :] / \
				sum(self.__mm_freqs[self.__last_bmu_ind, :]) 
			
			
		self.__last_bmu_ind = bmu_ind
		
	def __update_covars_full(self):
		"""
		updates corresponding covariances in generative model
		assuming distinct covariances for each mixture component (neuron)
		"""
		
		self._covar_calc_data[:] = self.neurons[self._adj_neurons_inds, self._adj_wv_comps_inds]
		self._covar_calc_data -= self._neurons_wv_comps_flat
		self._covar_calc_data *= self._neurons_adj_num_norm * self.covar_diff_scale
		
		# NOTE: this is seems to be faster (and memory tolerant)
		# than the dot product of '_covar_calc_data' to '_covar_calc_data.T'
		for i in xrange(self.neurons.shape[0]):
			dot(self._covar_calc_data_views[i], 
					self._covar_calc_data_views[i].T, 
					self.gen_model.covars_[i])
			
	def __update_covars_tied(self):
		"""
		updates corresponding covariances in generative model
		assuming one average covariance for every mixture component (neuron)
		"""
		
		self._covar_calc_data[:] = self.neurons[self._adj_neurons_inds, self._adj_wv_comps_inds]
		self._covar_calc_data -= self._neurons_wv_comps_flat
		self._covar_calc_data *= self._neurons_adj_num_norm * self.covar_diff_scale
		
		# Simple mean average covariance matrix
		for i in xrange(self.neurons.shape[0]):
			dot(self._covar_calc_data_views[i], 
					self._covar_calc_data_views[i].T, 
					self._temp_neuron_cov)
			
			self.gen_model.covars_ += self._temp_neuron_cov
			
		self.gen_model.covars_ /= self.neurons.shape[0]
	
	
	def find_bmu(self, input_vec, diff_m = None, calc_act_vec = False):
		""" returns BMU position [i] in lattice and its weight vector """
		
		if (diff_m == None):
			self.__calc_diff_m(input_vec) 
			diff_m = self.__diff_m[:]
			
		# find BMU (using squared euclidian distance) 
		# and calculate activation vector (if needed)
		# TODO: precache 'norms' array
		norms = diag(dot(diff_m, diff_m.T))
		bmu_ind = argmin(norms)
		
		if (calc_act_vec):
			self.act_vec[:] = self._likelihood_func(norms)
		
		
		# %%%%%%%%% VARIATED %%%%%%%%%%%%%%%%%
			
		# calculate model bias (error)
		#
		# TODO: try just norm of diff_m?
		# TODO #2: Unify with 'model_error' in update_neurons in case of PL_SOM ???
		#
		
		input_norm = linalg.norm(input_vec)
		if (input_norm == 0.0): input_norm = EPS
		
		wv_norm = linalg.norm(self.neurons[bmu_ind])
		if (wv_norm == 0.0): wv_norm = EPS 
		
		self.last_model_bias = linalg.norm(
			input_vec / input_norm - 
			self.neurons[bmu_ind] / wv_norm
		)
		
		# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
		
		return (bmu_ind, self.neurons[bmu_ind])
	
	def _gauss_nh(self, bmu_ind, denom):
		"""
		Standard gaussian neighbourhood which depends on
		1. current BMU index
		2. squared shape parameter: 'denom'
		"""
		
		# TODO: pre-cache both arrays: 'ind_diff' and that under return statement
	
		ind_diff = array([bmu_ind % self.lattice_shape[0],
						  floor(bmu_ind / self.lattice_shape[0])]) - \
					self._neurons_coords
		
		return diag(exp(-dot(ind_diff, ind_diff.T) / 
					(denom)))[:, None]
	
	def _update_neurons_kernel(self, bmu_ind, diff_m):
		raise NotImplementedError
	
	def update_neurons(self, bmu_ind, input_vec, diff_m = None):
		"""
		updates neurons (weights) according to given BMU index [i]
		and input vector
		
		update covariance matrix(es) for GMM
		
		NOTE: actual update procedure MUST be implemented in children classes
				in '_update_neurons_kernel(self, bmu_ind, diff_m)' function
				'input_vec' is not needed for children update kernel
		"""
		
		if (diff_m == None):
			self.__calc_diff_m(input_vec) 
			diff_m = self.__diff_m[:]
		
		# -- update neuron's weights
		# -- update procedure is specific to particular kind of SOM
		# -- and is implemented in children classes
		self._update_neurons_kernel(bmu_ind, diff_m[:])
		
		# -- update corresponding covariances in generative model (if it exists!)
		self.__update_covars()
		
		# -- update markov model's state-transition probabilities (if enabled)
		self.__update_state_trans_probs(bmu_ind)

	def feed(self, input_vec):
		"""
		Helper function for performing whole PLSOM feed procedure
		
		returns BMU: index [i] and its weigth vector
		"""
		
		self.__calc_diff_m(input_vec) 
		
		# -- 'input' here is not actually used in find_bmu
		bmu_and_wv = self.find_bmu(input_vec, self.__diff_m[:], True)
		
		# -- update neurons
		self.update_neurons(bmu_and_wv[0], input_vec, self.__diff_m[:])
		
		return bmu_and_wv
	
	def predict_next_act_vec(self):
		"""
		Predicts activation vector (next BMU likelihood) at next time step
		given current activation vector and markov chain's state-transition
		matrix
		
		NOTE: 'init_predictor' MUST be called prior to usage of this function!
		"""
		
		dot(self.act_vec, self.__mm_trans_probs, self.predicted_act_vec)
		
		return self.predicted_act_vec[:]
	
	def __generate_gmm(self, act_vec, samples_num):
		"""
		Generate data (in input space) from GMM associated with SOM
		'act_vec' establishes the weights of each mixture component
		"""
		
		# act_vec /= max(act_vec) # Is such normaliztaion really needed?
		self.gen_model.weights_ = act_vec[:]
	
		return self.gen_model.sample(samples_num)
	
	def __generate_dpd(self, act_vec, samples_num):
		"""
		SOM's neurons are treated as categorical values with
		associated Probabilty Mass Function,
		specified by 'act_vec'
		
		Returns weight vectors of neurons sampled from Discrete PD
		
		NOTE: 'act_vec' could have any values, as long as 
				it is normalized in this function
		"""
		
		abs(act_vec, out = act_vec) # just in case
		
		# -- CDF
		bins = cumsum(act_vec)
		
		if (bins[-1] == 0.0):
			print act_vec
			raise ValueError
		
		bins /= bins[-1] # normalization
		
		return self.neurons[digitize(random.random_sample(samples_num), bins)] + \
			self._noise_func()

#================================================================================



#================================================================================
# Kohonen's SOM
# !!! IMPLEMENT !!!
#================================================================================

#class SOM(_Template_SOM):
#	"""
#	
#	Classic Kohonen's SOM with generative extensions by _Template_SOM
#	
#	TODO: Implement!
#	
#	"""
	
#	def __init__(self, lattice_shape, input_dim, **kwargs):
#		_Template_SOM.__init__(self, lattice_shape, input_dim, **kwargs)
#		
#	
#	def _update_neurons_kernel(self, bmu_ind, diff_m):	
#		
#		
#		# -- update neurons' weights
#		diff_m *= self._gauss_nh(bmu_ind, self.nh_constant * model_error)
#		self.neurons += diff_m * model_error
		
		
#================================================================================


#================================================================================
# MillerSOM (Kohonen-alike SOM with online learning feature)
#================================================================================

class Miller_SOM(_Template_SOM):
	"""
	
	Self-Ogranizing Map proposed by [Miller and Lommel, 2006] in paper
	considering HQSOM (MPF-like structure of SOM-RSOM pairs)
	
	The only difference from Kohonen's SOM is the ability of online learning
	as long as neighbourhood shape depends only on mean-squared error and not
	on time
	
	"""
	
	def __init__(self, lattice_shape, input_dim, **kwargs):
		_Template_SOM.__init__(self, lattice_shape, input_dim, **kwargs)
		
		# Neighbourhood constant used in neighbourhood shape calculation
		# Could be thought as a tunable parameter
		#
		# NOTE: completely arbitary value for now!
		self.nh_constant = 2.3
		
	
	def _update_neurons_kernel(self, bmu_ind, diff_m):	
		
		# Model error is estimated as squared euclidean distance from
		# input to BMU averaged by input vector's length
		#
		# NOTE: model error couldn't be 0 due to fact it is used as denominator
		model_error = dot(diff_m[bmu_ind], diff_m[bmu_ind]) / diff_m.shape[1]
		if (model_error < EPS): model_error = EPS 
		
		# -- update neurons' weights
		diff_m *= self._gauss_nh(bmu_ind, model_error*self.nh_constant*self.nh_constant)
		self.neurons += diff_m

#================================================================================
		


#================================================================================
# Parameterless SOM (PL-SOM) 
#================================================================================

class PL_SOM(_Template_SOM):
	"""
	
	Parameterless SOM (PLSOM) implementation according to
	[Berglund and Sitte, 2006]
	
	"""
	
	def __init__(self, lattice_shape, input_dim, **kwargs):
		_Template_SOM.__init__(self, lattice_shape, input_dim, **kwargs)
		
		# Neighbourhood constant used in neighbourhood shape calculation
		# Could be thought as a parameter of parameterless SOM, how ironic :-)
		#
		# NOTE: almost arbitary value for now!
		self.nh_constant = 2.3
		
		# -- used in error estimation: previous denominator
		# -- (i.e. normalization factor) of model_error estimation formula
		#
		# -- NOTE: assume (t-1) by word "previous"
		self.__last_me_denom = EPS
		
	
	def _update_neurons_kernel(self, bmu_ind, diff_m):	
		
		# -- adaptive error estimation using 2-norm for distance from BMU
		# -- [according to Berglund and Sitte, 2006]
		#
		# NOTE: Seems like 'sqrt()' does not affect performance!
		#
		# TODO: Unify with 'self.last_model_bias' ???
		#
		input_bmu_dist = sqrt(dot(diff_m[bmu_ind], diff_m[bmu_ind]))
		
		self.__last_me_denom = max(input_bmu_dist, self.__last_me_denom)
		model_error = input_bmu_dist / self.__last_me_denom
		
		if (model_error > 0.0):
			# 1.0 is sigma_min
			sigma = self.nh_constant * model_error
			if (sigma < 1.0): sigma = 1.0
			
			
			# OR
			#
			# (suggested sigma_min = 1.0)
			#sigma = (self.nh_constant - sigma_min) * model_error + sigma_min
			#
			# OR
			#
			# (suggested sigma_min = 0.0)
			#sigma = (self.nh_constant - sigma_min) * log(1 + model_error*(exp(1) - 1)) + sigma_min
			
			
			# -- update neurons' weights
			diff_m *= self._gauss_nh(bmu_ind, sigma*sigma)
			self.neurons += diff_m * model_error
		
#================================================================================

		
# ============================================================================
