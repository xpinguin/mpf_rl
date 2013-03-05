"""
	Different "noises": just frozen random distributions with
	additional properties (scale decreasing, for instance)
	
	Such approach is sufficiently faster than scipy rv_continuous...
"""

from common import *

class UniformNoise:
	def __init__(self, lower = -1.0, upper = 1.0, magn = 1.0,
				magn_decrease = 0.0, min_magn = 0.001):
		self.shape = 1 # default value
		
		self.lower = lower
		self.upper = upper
		self.magn = magn + magn_decrease
		self.magn_decrease = magn_decrease
		self.min_magn = min_magn
		
	def __call__(self):
			self.magn -= self.magn_decrease
			if (self.magn < self.min_magn):
				self.magn_decrease = 0.0
				self.magn = self.min_magn
			
			return random.uniform(self.lower, self.upper, self.shape) * self.magn
		
class GaussianNoise:
	def __init__(self, mean = 0.0, magn = 1.0,
				magn_decrease = 0.0, min_magn = 0.001):
		self.shape = 1 # default value
		
		self.mean = mean
		self.magn = magn + magn_decrease
		self.magn_decrease = magn_decrease
		self.min_magn = min_magn
		
	def __call__(self):
			self.magn -= self.magn_decrease
			if (self.magn < self.min_magn):
				self.magn_decrease = 0.0
				self.magn = self.min_magn
			
			return random.normal(self.lower, self.magn, self.shape)
