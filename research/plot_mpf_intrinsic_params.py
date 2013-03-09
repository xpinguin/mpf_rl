import os
import cPickle as pickle
import gzip

from numpy import *

import pylab as plt

def load_mpf(dump_path):
	files_list = os.listdir(dump_path)
	h_filenames = [
				filename 
				for filename in files_list
					if ((filename.find("h_") == 0) and
						(filename.find(".gzpckl") > 0)) 
	]
	
	assert(len(h_filenames) > 0)
	
	
	# try to load params from prebuilt cache (if cache is not obsolete)
	try:
		cache_f = gzip.open(dump_path + "/cached_params.gzpckl", "rb")
		
		# test date
		if (os.path.getmtime(dump_path + "/" + h_filenames[0]) > 
			os.path.getmtime(dump_path + "/cached_params.gzpckl")):
			
			cache_f.close()
			raise # regenerate cache file
		
		# load cached params at last
		params = pickle.load(cache_f)
		cache_f.close()
		
		return params
		
	except:
		pass
	# ---
	
	# dict with parameters
	# each parameter represented by array holding its evolution through time
	params = dict()
	
	#units_num = -1
	#levels_num = -1
	
	
	
	for h_filename in h_filenames:
		in_f = gzip.open(dump_path + "/" + h_filename, "rb")
		h_dict = pickle.load(in_f)
		in_f.close()
		
		h_dict_af = h_dict["after_forward"]
		#h_dict_ab = h_dict["after_backward"] 
		
		time_index = int(h_dict_af["t"] / h_dict_af["dump_period"])
		
		# total number of levels
		if (not "levels_num" in params):
			params["levels_num"] = len(h_dict_af["levels"])
		
		# actual time of slice
		if (not "time" in params):
			params["time"] = zeros(len(h_filenames))
			
		params["time"][time_index] = h_dict_af["t"]
		
		print "Processing time '%d'..." % (h_dict_af["t"])
		
		# hierarchy prediction error
		if (not "pred_error" in params):
			params["pred_error"] = {
				"angular" : zeros(len(h_filenames)),
				"distance" : zeros(len(h_filenames))
			}
		
		# -- angular error
		params["pred_error"]["angular"][time_index] = dot(
			h_dict_af["curr_input_vec"],
			h_dict_af["prev_output_vec"]
		) / (
			linalg.norm(h_dict_af["curr_input_vec"]) * \
			linalg.norm(h_dict_af["prev_output_vec"])
		)
		
		# -- distance error
		params["pred_error"]["distance"][time_index] = linalg.norm(
			h_dict_af["curr_input_vec"] - \
			h_dict_af["prev_output_vec"]
		)
		
		# store SS and TS evolving parameters per level & per unit
		for level_id in xrange(len(h_dict_af["levels"])):
			if (not level_id in params):
				params[level_id] = dict()
			
			for unit_id in xrange(len(h_dict_af["levels"][level_id])):
				if (not unit_id in params[level_id]):
					params[level_id][unit_id] = dict()
					
				# unit's parameters
				# -- continious prediction error: angular and distance
				if (not "pred_error" in params[level_id][unit_id]):
					params[level_id][unit_id]["pred_error"] = {
						"angular" : zeros(len(h_filenames)),
						"distance" : zeros(len(h_filenames))
					}
				
				# -- angular error
				params[level_id][unit_id]["pred_error"]["angular"][
						time_index
				] = dot(
					h_dict_af["levels"][level_id][unit_id]["curr_input_vec"],
					h_dict_af["levels"][level_id][unit_id]["prev_output_vec"]
				) / (
					linalg.norm(
						h_dict_af["levels"][level_id][unit_id]["curr_input_vec"]
					) * \
					linalg.norm(
						h_dict_af["levels"][level_id][unit_id]["prev_output_vec"]
					)
				)
				
				# -- distance error
				params[level_id][unit_id]["pred_error"]["distance"][
						time_index
				] = linalg.norm(
					h_dict_af["levels"][level_id][unit_id]["curr_input_vec"] - \
					h_dict_af["levels"][level_id][unit_id]["prev_output_vec"]
				)
				
				
				# spatial SOM parameters
				if ("ss" in h_dict_af["levels"][level_id][unit_id]):
					if (not "ss" in params[level_id][unit_id]):
						params[level_id][unit_id]["ss"] = {
							"bmu_ind" : zeros(len(h_filenames)),
							"ub_bmu_ind" : zeros(len(h_filenames)), # unbiased
							"model_error" : zeros(len(h_filenames))
						}
							
					params[level_id][unit_id]["ss"]["bmu_ind"][
							time_index
					] = argmax(
						h_dict_af["levels"][level_id][unit_id]["ss"]["act_vec"]
					)
					
					params[level_id][unit_id]["ss"]["ub_bmu_ind"][
								time_index
					] = argmax(
						h_dict_af["levels"][level_id][unit_id]["unbiased_ss_act_vec"]
					)
					
					params[level_id][unit_id]["ss"]["model_error"][
								time_index
					] = h_dict_af["levels"][level_id][unit_id]["ss"]["last_model_bias"]
				
				# temporal SOM parameters
				if ("ts" in h_dict_af["levels"][level_id][unit_id]):
					if (not "ts" in params[level_id][unit_id]):
						params[level_id][unit_id]["ts"] = {
							"bmu_ind" : zeros(len(h_filenames)),
							"model_error" : zeros(len(h_filenames))
						}
							
					params[level_id][unit_id]["ts"]["bmu_ind"][
							time_index
					] = argmax(
						h_dict_af["levels"][level_id][unit_id]["ts"]["act_vec"]
					)
					
					params[level_id][unit_id]["ts"]["model_error"][
								time_index
					] = h_dict_af["levels"][level_id][unit_id]["ts"]["last_model_bias"]
	
	# cache params
	cache_f = gzip.open(dump_path + "/cached_params.gzpckl", "wb")
	pickle.dump(params, cache_f, pickle.HIGHEST_PROTOCOL)
	cache_f.close()
	# ---
	
	return params


def plot_activations_graph(mpf_params):
	levels_num = mpf_params["levels_num"]
	#max_units_per_level = len(mpf_params[0])
	
	for level_id in xrange(levels_num):
		fig = plt.figure()
		units_num = len(mpf_params[level_id])
		
		for unit_id, unit in mpf_params[level_id].iteritems():
			# SOM
			ax = fig.add_subplot(2, units_num, unit_id + units_num + 1)
			
			ax.set_title(
				"SOM, Level %d, Unit %d" % (level_id, unit_id)
			)
			ax.plot(
				mpf_params["time"],
				unit["ss"]["bmu_ind"],
				"gx"
			)
			
			ax.set_xlabel("t")
			ax.set_ylabel("BMU")
			
			# RSOM
			if (not "ts" in unit): continue
			
			ax = fig.add_subplot(2, units_num, unit_id + 1)
			
			ax.set_title(
				"RSOM, Level %d, Unit %d" % (level_id, unit_id)
			)
			ax.plot(
				mpf_params["time"],
				unit["ts"]["bmu_ind"],
				"bx"
			)
			
			ax.set_xlabel("t")
			ax.set_ylabel("BMU")
	
	plt.show()
	
def plot_pred_error_graph(mpf_params):
	# hierarchy prediction error
	fig = plt.figure()
	fig.suptitle("Hierarchy prediction error")
	
	# -- angular
	ax = fig.add_subplot(2, 1, 1)
	ax.set_title("Angular")
	ax.plot(mpf_params["time"], mpf_params["pred_error"]["angular"], 'r-')
	
	ax.set_xlabel("time")
	ax.set_ylabel("angle")
	
	# -- distance
	ax = fig.add_subplot(2, 1, 2)
	ax.set_title("Euclidean distance")
	ax.plot(mpf_params["time"], mpf_params["pred_error"]["distance"], 'b-')
	
	ax.set_xlabel("time")
	ax.set_ylabel("dist")
	
	
	# per-level per unit prediction error
	def __pl_pu_pred_error(fig, err_key, style):
		levels_num = mpf_params["levels_num"]
		
		for level_id in xrange(levels_num):
			units_in_level = len(mpf_params[level_id])
			
			for unit_id, unit in mpf_params[level_id].iteritems():
				# -- distance
				
				ax = fig.add_subplot(
							levels_num,
							units_in_level,
							unit_id + (levels_num - level_id - 1) * units_in_level + 1
				)
				ax.set_title("Level %d, Unit %d" % (level_id, unit_id))
				ax.plot(mpf_params["time"], unit["pred_error"][err_key], style)
				
				ax.set_xlabel("time")
				ax.set_ylabel("dist")
	
	# -- distance
	fig = plt.figure()
	fig.suptitle("Per-unit per-level DISTANCE prediction error")		
	__pl_pu_pred_error(fig, "distance", "b-")
	
	# -- angular
	fig = plt.figure()
	fig.suptitle("Per-unit per-level ANGULAR prediction error")		
	__pl_pu_pred_error(fig, "angular", "r-")
	
	plt.show()
	
def plot_som_and_rsom_model_errors(mpf_params):
	levels_num = mpf_params["levels_num"]
	#max_units_per_level = len(mpf_params[0])
	
	for level_id in xrange(levels_num):
		fig = plt.figure()
		units_num = len(mpf_params[level_id])
		
		for unit_id, unit in mpf_params[level_id].iteritems():
			# SOM
			ax = fig.add_subplot(2, units_num, unit_id + units_num + 1)
			
			ax.set_title(
				"SOM, Level %d, Unit %d" % (level_id, unit_id)
			)
			ax.plot(
				mpf_params["time"],
				unit["ss"]["model_error"],
				"r-"
			)
			
			ax.set_xlabel("time")
			ax.set_ylabel("error")
			
			# RSOM
			if (not "ts" in unit): continue
			
			ax = fig.add_subplot(2, units_num, unit_id + 1)
			
			ax.set_title(
				"RSOM, Level %d, Unit %d" % (level_id, unit_id)
			)
			ax.plot(
				mpf_params["time"],
				unit["ts"]["model_error"],
				"b-"
			)
			
			ax.set_xlabel("time")
			ax.set_ylabel("error")
	
	plt.show()
	
	
	

#================================================================================
# MAIN CODE
#================================================================================
mpf_params = load_mpf(
		"K:\\__temp\\mpf_rl_dumps\\tictactoe_no_rules_no_l0-rsom_3levels_6units_1"
)

#plot_activations_graph(mpf_params)
#plot_pred_error_graph(mpf_params)
plot_som_and_rsom_model_errors(mpf_params)



#================================================================================
# TEST CODE
#================================================================================
#print mpf_params[1][1]["ss"]["model_error"][5:10]
