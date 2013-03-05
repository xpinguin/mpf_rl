#!/usr/bin/env python

import random, pygame, sys
from pygame.locals import *
from const import *
import methods as mth
import methods

import numpy as np

sys.path.append("../../")

from mpfrl.hierarchy import MPF_Hierarchy
from mpfrl.units import *
from mpfrl.SOM import Miller_SOM


class Snake:
	"""
	Snake class houses all information for a particular snake.
	player - if snake is the player.
	name - name of snake.
	alive - if snake is alive. Rather than delete, this allows snake to slowly shrink to the point of where it died.
	coords - a list of dictionaries containing coordinates 'x' and 'y'. A special global variable HEAD (0).
	direction - where snake moves for every game iteration ('left', 'up', etc).
	color - body of snake's color.
	colorBorder - outline of body.
	growth - when a snake is to grow, this is stored in this buffer so that every game iteration can add one growth, only.
	multiplier - all fruit eaten which cause points to be scored are multiplied by this.
	multipliertimer - number of game iterations multiplier stays in effect.
	score - the number of points snake has accumulated.
	place - used to determine death order.
	"""
	def __init__(self, n=SNAKEY, c=False, colorsnake=GREEN, colorborder=COBALTGREEN):
		self.name = n
		if self.name == SNAKEY:
			self.player = True
		else:
			self.player = False
		self.alive = True
		
		if c == False:
			self.coords = getStartCoords(1)
		else:
			self.coords = c
		
		# determine direction if length supports
		if len(self.coords) > 1:
			if self.coords[0]['x'] > self.coords[1]['x']:
				self.direction = RIGHT
			else:
				self.direction = LEFT
		# egg is just hatched-- for now goes left initially
		else:
			 self.direction = LEFT
		
		self.color = {'red': 0, 'green': 0, 'blue': 0}
		self.updateColor({'red': colorsnake[0], 'green': colorsnake[1], 'blue': colorsnake[2]})
		self.colorCurrent = self.color
		
		self.colorBorder = {'red': 0, 'green': 0, 'blue': 0}
		self.updateColorBorder({'red': colorborder[0], 'green': colorborder[1], 'blue': colorborder[2]})
		self.colorBorderCurrent = self.colorBorder
		
		self.growth = 0
		self.multiplier = 1
		self.multipliertimer = 0
		self.score = 0
		self.place = False
		self.scored = True
		self.fruitEaten = {'apple':0, 'poison':0, 'orange':0, 'raspberry':0,
						   'blueberry':0, 'lemon':0, 'egg':0}

	def updateScore(self, points_input):
		"""
		This updates score of snake, factoring multiplier.
		Argument (points_input) should be int.
		"""
		self.score = self.score + (points_input * self.multiplier)

	def updateGrowth(self, growth_input):
		"""
		This updates growth "owed" to snake, allowing amount to stack.
		Argument (growth_input) should be int.
		"""
		self.growth = self.growth + growth_input

	def updateMultiplier(self, multiplier_input, timer_input):
		"""
		This updates multiplier value and time (game iterations) multiplier is active. Only time stacks.
		"""
		# multiplier value does not stack, but time does
		self.multiplier = multiplier_input
		self.multipliertimer = self.multipliertimer + timer_input
		
	def updateColor(self, change):
		"""
		Adjusts color of snake.
		Argument (change) is dictionary.
		Factors in maximums and minimums.
		"""
		for color in change:
			if self.color.has_key(color):
				if change[color] > 0:
					if self.color[color] + change[color] > 255:
						self.color[color] = 255
					else:
						self.color[color] = self.color[color] + change[color]
				elif change[color] < 0:
					if self.color[color] + change[color] < 0:
						self.color[color] = 0
					else:
						self.color[color] = self.color[color] + change[color]
						
	def updateColorBorder(self, change):
		"""
		Adjusts border color of snake.
		Argument (change) is dictionary.
		Factors in maximums and minimums.
		"""
		for color in change:
			if self.colorBorder.has_key(color):
				if change[color] > 0:
					if self.colorBorder[color] + change[color] > 255:
						self.colorBorder[color] = 255
					else:
						self.colorBorder[color] = self.colorBorder[color] + change[color]
				elif change[color] < 0:
					if self.colorBorder[color] + change[color] < 0:
						self.colorBorder[color] = 0
					else:
						self.colorBorder[color] = self.colorBorder[color] + change[color]
		
	def setColorCurrent(self, color):
		"""
		Sets current color.
		Argument (color) is a tuple.
		"""
		self.colorCurrent = {'red': color[0], 'green': color[1], 'blue': color[2]}
		
	def setColorBorderCurrent(self, color):
		"""
		Sets current border color.
		Argument (color) is a tuple.
		"""
		self.colorBorderCurrent = {'red': color[0], 'green': color[1], 'blue': color[2]}
		
	def getColor(self):
		"""
		Returns tuple of snake color.
		"""
		return (self.color['red'], self.color['green'], self.color['blue'])
		
	def getColorCurrent(self):
		"""
		Returns tuple of snake color, currently.
		"""
		return (self.colorCurrent['red'], self.colorCurrent['green'], self.colorCurrent['blue'])
		
	def getColorBorder(self):
		"""
		Returns tuple of snake color, border.
		"""
		return (self.colorBorder['red'], self.colorBorder['green'], self.colorBorder['blue'])
		
	def getColorBorderCurrent(self):
		"""
		Returns tuple of snake color, current border.
		"""
		return (self.colorBorderCurrent['red'], self.colorBorderCurrent['green'], self.colorBorderCurrent['blue'])
		
	def resetColor(self):
		"""
		Sets current color to color.
		"""
		self.colorCurrent = self.color
		
	def resetColorBorder(self):
		"""
		Sets current border color to border color.
		"""
		self.colorBorderCurrent = self.colorBorder
		
	def getPlace(self, totaldead, totalscored):
		"""
		Returns a string containing the 'place' of a snake (longest lasting = 1st)
		If game aborted early, will grant all living snakes '1st (alive)'
		"""
		totalalive = totalscored - totaldead

		# snake not dead
		if self.place == False:
			return '1st*'
		# if not aborted early
		elif totalalive == 0:
			if self.place == totalscored:
				return '1st'
			elif self.place + 1 == totalscored:
				return '2nd'
			elif self.place + 2 == totalscored:
				return '3rd'
			else:
				return 'last'
		# aborted early; factor in living snakes
		elif self.place == totalscored - totalalive:
			return '2nd'
		elif self.place + 1 == totalscored - totalalive:
			return '3rd'
		else:
			return 'last'
			
	def checkCoords(self, x, y):
		"""
		Returns True if snake (head) matches (x,y) coordinates provided.
		Will always return False if coordinates < 1.
		"""
		if len(self.coords) > 0:
			if self.coords[HEAD]['x'] == x and self.coords[HEAD]['y'] == y:
				return True
		return False
		
	def getCoords(self, axis):
		"""
		Returns x or y (axis) coordinates of head of snake.
		Will always return False if coordinates < 1.
		"""
		if len(self.coords) > 0:
			return self.coords[HEAD][axis]

	def boundsCollision(self):
		"""
		This returns True if snake (head) is ever out of grid parameters.
		"""
		# check if out of bounds -- offset on on 'y' for buffer.
		if self.getCoords('x') == -1 or \
		   self.getCoords('x') == CELLWIDTH or \
		   self.getCoords('y') == -1 + (TOP_BUFFER / CELLSIZE) or \
		   self.getCoords('y') == CELLHEIGHT + (TOP_BUFFER / CELLSIZE):
			return True
		else:
			return False
			
	def snakeCollision(self, snake):
		"""
		This returns True if snake (head) collides with any part of a given snake (outside of own head if checking against self).
		Will always return False if coordinates of self or snake < 1.
		"""
		if len(self.coords) > 0 and len(snake.coords) > 0:
			if self is snake:
				# exclude head if checked against self
				for snakebody in snake.coords[1:]:
					if snakebody['x'] == self.coords[HEAD]['x'] and \
					   snakebody['y'] == self.coords[HEAD]['y']:
						return True	
			else:
				for snakebody in snake.coords:
					if snakebody['x'] == self.coords[HEAD]['x'] and \
					   snakebody['y'] == self.coords[HEAD]['y']:
						return True
		# no collision
		return False
		
	def fruitCollision(self, fruit):
		"""
		This returns True if snake (head) has collided with a given fruit.
		"""
		if self.getCoords('x') == fruit.coords['x'] and \
		   self.getCoords('y') == fruit.coords['y']:
			return True
		else:
			return False

	def move(self, trailing=False):
		"""
		This will update coords for snake, moving it one cell in given direction.
		It also factors in and updates growth if any growth is "owed" snake (one per game iteration).
		If snake is dead, will only remove the last segment of snake and ignore direction / not move snake.
		"""
		if self.alive:
			# delete last segment first.
			if self.growth < 0:
				self.growth = self.growth + 1
				if len(self.coords) > 3:
					# implement negative growth by removing last two segments
					del self.coords[-2:]
				else:
					# snake is too short -- remove last segment as normal
					del self.coords[-1]
			elif self.growth > 0:
				# implement positive growth by not deleting last segment
				self.growth = self.growth - 1
			elif trailing == False:
				# no growth factor, delete last segment if trailing is off
				del self.coords[-1]

			# determine new head coordinates by direction
			if self.direction == UP:
				newhead = {'x': self.getCoords('x'), 
						   'y': self.getCoords('y') - 1}
			elif self.direction == DOWN:
				newhead = {'x': self.getCoords('x'), 
						   'y': self.getCoords('y') + 1}
			elif self.direction == LEFT:
				newhead = {'x': self.getCoords('x') - 1, 
						   'y': self.getCoords('y')}
			elif self.direction == RIGHT:
				newhead = {'x': self.getCoords('x') + 1, 
						   'y': self.getCoords('y')}

			# insert new head segment
			self.coords.insert(HEAD, newhead)

		# dead snake -- remove last segment
		elif len(self.coords) > 0:
			del self.coords[-1]
			
	def drawSnake(self):
		"""
		Responsible for drawing snake image to screen.
		"""
		for coord in self.coords:
			x = coord['x'] * CELLSIZE
			y = coord['y'] * CELLSIZE
			snakeSegmentRect = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
			pygame.draw.rect(DISPLAYSURF, self.getColorBorderCurrent(), snakeSegmentRect)
			snakeInnerSegmentRect = pygame.Rect(x + 3, y + 3, CELLSIZE - 6, CELLSIZE - 6)
			pygame.draw.rect(DISPLAYSURF, self.getColorCurrent(), snakeInnerSegmentRect)
			
	def drawScore(self, position, allsnake):
		"""
		Responsible for drawing snake score to screen.
		Coordinates of where drawn so that 'y' depends on number of snakes being scored, 'x' at the top (where buffer is)
		"""
		# get number of snakes in allsnake that will be scored.
		totalscored = 0
		for snake in allsnake:
			if snake.scored == True:
				totalscored = totalscored + 1
		methods.drawMessage(self.name + ': ' + str(self.score), \
							methods.getPosition(position, allsnake, totalscored), \
							1, self.getColorCurrent())


class Opponent(Snake):
	"""
	Derived from Snake class, this adds functionality for determining direction.
	"""
	def __init__(self, n='bot', c=False, sc=COBALTGREEN, sb=GOLDENROD, r=20, p=10, a=-15, g=[50,-10,30,20,35,100,30]):
		Snake.__init__(self, n, c, sc, sb)
		self.avoidBoundaries = True
		self.depthPerception = 20
		self.randomness = r
		self.preferSameDirection = p
		self.avoidSnake = a
		self.goal = {'apple': g[0], 'poison': g[1], 'orange': g[2], 'raspberry': g[3], 'blueberry': g[4], 'lemon': g[5], 'egg': g[6]}

	def updateDirection(self, grid):
		"""
		Responsible for determining opponent's direction choice.
		Takes one argument - grid representation of playing board. Copied and marked as cells are 'explored'
		Neighboring 
		"""
		# copy grid to snake -- this will allow cells already searched to be marked 'visited'
		self.grid = grid
	
		# all directions have value adjusted -- reset
		self.nextDirection = {LEFT:0, RIGHT:0, UP:0, DOWN:0}
		
		# coords of own snake head
		x = self.getCoords('x')
		y = self.getCoords('y')

		# opposite direction kills snake
		if self.direction == LEFT:
			self.nextDirection[RIGHT] = self.nextDirection[RIGHT] - 1000
		elif self.direction == RIGHT:
			self.nextDirection[LEFT] = self.nextDirection[LEFT] - 1000
		elif self.direction == UP:
			self.nextDirection[DOWN] = self.nextDirection[DOWN] - 1000
		elif self.direction == DOWN:
			self.nextDirection[UP] = self.nextDirection[UP]- 1000

		# avoid boundaries
		if self.avoidBoundaries == True:
			if x == 0:
				self.nextDirection[LEFT] = self.nextDirection[LEFT] - 1000
			if x == CELLWIDTH - 1:
				self.nextDirection[RIGHT] = self.nextDirection[RIGHT] - 1000
			if y == (TOP_BUFFER / CELLSIZE):
				self.nextDirection[UP] = self.nextDirection[UP] - 1000
			if y == CELLHEIGHT + (TOP_BUFFER / CELLSIZE) - 1:
				self.nextDirection[DOWN] = self.nextDirection[DOWN] - 1000
				
		# prefer same direction
		self.nextDirection[self.direction] = self.nextDirection[self.direction] + self.preferSameDirection

		# avoid immediate snakes
		if grid.has_key((x-1,y)) and (grid[(x-1,y)] == 'snake'):
			self.nextDirection[LEFT] = self.nextDirection[LEFT] - 1000
		if grid.has_key((x+1,y)) and (grid[(x+1,y)] == 'snake'):
			self.nextDirection[RIGHT] = self.nextDirection[RIGHT] - 1000
		if grid.has_key((x,y-1)) and (grid[(x,y-1)] == 'snake'):
			self.nextDirection[UP] = self.nextDirection[UP] - 1000
		if grid.has_key((x,y+1)) and (grid[(x,y+1)] == 'snake'):
			self.nextDirection[DOWN] = self.nextDirection[DOWN] - 1000
			
		# 'look' to neighboring squares for possible snakes and fruits
		self.look(x, y, self.depthPerception)

		# factor in randomness
		for d in self.nextDirection:
			self.nextDirection[d] = self.nextDirection[d] + random.randint(0,self.randomness)
			
		# report if debugging
		if DEBUG == True:
			print self.name
			print self.nextDirection

		# update snake direction to direction with highest score
		self.direction = max(self.nextDirection, key=self.nextDirection.get)
		
	def look(self, x, y, depth):
		"""
		recursively looks in all directions unless depth is exhausted.
		visited coords are ignored.
		coords containing a snake are affected by avoidSnake variable
		"""
		if depth < 1:
			return
		elif self.grid.has_key((x,y)):
			if self.grid[(x,y)] == 'visited':
				return
			elif self.grid[(x,y)] == 'snake':
				if DEBUG == True:
					print '..snake:'
				self.influenceDirection(x, y, self.avoidSnake)
				self.grid[(x,y)] = 'visited'
				self.look(x-1, y, depth -1)
				self.look(x+1, y, depth -1)
				self.look(x, y+1, depth -1)
				self.look(x, y-1, depth -1)
			elif self.grid[(x,y)] != 0:  # implied fruit
				fruit = self.grid[(x,y)]
				if DEBUG == True:
					print '..fruit: %s' % (fruit)
				self.influenceDirection(x, y, self.goal[fruit])
				self.grid[(x,y)] = 'visited'
				self.look(x-1, y, depth -1)
				self.look(x+1, y, depth -1)
				self.look(x, y+1, depth -1)
				self.look(x, y-1, depth -1)
			else: #empty cell
				self.grid[(x,y)] = 'visited'
				self.look(x-1, y, depth -1)
				self.look(x+1, y, depth -1)
				self.look(x, y+1, depth -1)
				self.look(x, y-1, depth -1)
		else: #bound collision
			return

	def influenceDirection(self, x, y, base):
		"""
		Finds difference between (x,y) coord and point of origin.
		Direction is then altered by 'base' amount, decayed 1 per distance from.
		"""
		if DEBUG == True:
			print '....%s (%s, %s)-->' % (self.nextDirection, x, y)
		xdiff = self.getCoords('x') - x
		ydiff = self.getCoords('y') - y
		if xdiff > 0:  # positive = left
			if (base - xdiff > 0 and base > 0) or (base - xdiff < 0 and base < 0):
				self.nextDirection[LEFT] = self.nextDirection[LEFT] + base - xdiff
		elif xdiff < 0:  # negative = right
			if (base + xdiff > 0 and base > 0) or (base + xdiff < 0 and base < 0):
				self.nextDirection[RIGHT] = self.nextDirection[RIGHT] + base + xdiff
		if ydiff > 0:  # positive = up
			if (base - ydiff > 0 and base > 0) or (base - ydiff < 0 and base < 0):
				self.nextDirection[UP] = self.nextDirection[UP] + base - ydiff
		elif ydiff < 0:  # negative = down
			if (base + ydiff > 0 and base > 0) or (base + ydiff < 0 and base < 0):
				self.nextDirection[DOWN] = self.nextDirection[DOWN] + base + ydiff
		if DEBUG == True:
			print '....%s' % (self.nextDirection)

	def getPlace(self, totaldead, totalsnakes):
		return Snake.getPlace(self, totaldead, totalsnakes)
		
	def updateColor(self, change):
		Snake.updateColor(self, change)
		
	def updateColorBorder(self, change):
		Snake.updateColorBorder(self, change)

	def setColorCurrent(self, color):
		Snake.setColorCurrent(self, color)
		
	def setColorBorderCurrent(self, color):
		Snake.setColorBorderCurrent(self, color)
		
	def getColor(self):
		return Snake.getColor(self)
		
	def getColorCurrent(self):
		return Snake.getColorCurrent(self)
		
	def getColorBorder(self):
		return Snake.getColorBorder(self)
		
	def getColorBorderCurrent(self):
		return Snake.getColorBorderCurrent(self)
		
	def resetColor(self):
		Snake.resetColor(self)
	
	def resetColorBorder(self):
		Snake.resetColorBorder(self)

	def updateScore(self, points_input):
		Snake.updateScore(self, points_input)

	def updateGrowth(self, growth_input):
		Snake.updateGrowth(self, growth_input)

	def updateMultiplier(self, multiplier_input, timer_input):
		Snake.updateMultiplier(self, multiplier_input, timer_input)
		
	def checkCoords(self, x, y):
		return Snake.checkCoords(self, x, y)
		
	def getCoords(self, axis):
		return Snake.getCoords(self, axis)

	def boundsCollision(self):
		return Snake.boundsCollision(self)

	def snakeCollision(self, snake):
		return Snake.snakeCollision(self, snake)

	def fruitCollision(self, fruit):
		return Snake.fruitCollision(self, fruit)

	def move(self, trailing):
		Snake.move(self, trailing)

	def drawSnake(self):
		Snake.drawSnake(self)

	def drawScore(self, position, allsnake):
		Snake.drawScore(self, position, allsnake)		

class OpponentMPF(Opponent):
	def __init__(self, n='bot', c=False, sc=COBALTGREEN, sb=GOLDENROD, r=20, p=10, a=-15, g=[50,-10,30,20,35,100,30]):
		Snake.__init__(self, n, c, sc, sb)
		
		self._dirs_names = [LEFT, UP, RIGHT, DOWN]
		self._dirs_ids = {LEFT: 0, UP: 1, RIGHT: 2, DOWN: 3}
		
		self._input_vec = np.zeros(methods._nd_array_grid.shape[0]*methods._nd_array_grid.shape[1] + 4)
		
		self.reinforcement = 0.0
		
		self._iterations_num = 0
		
		
		# init MPF hierarchy
		self.UNIT_VF = (4, 4)
		UNIT_INP_DIM = self.UNIT_VF[0]*self.UNIT_VF[1]
		
		self._l0_units = []
		self._grid_map = []
		
		for i in xrange(mth._nd_array_grid.shape[0] / self.UNIT_VF[0]):
			for j in xrange(mth._nd_array_grid.shape[1] / self.UNIT_VF[1]):
				self._l0_units.append(MPF_Unit_RL(
									ss_class = Miller_SOM,
									ts_class = Miller_SOM,
									input_dim = UNIT_INP_DIM,
									ss_shape = (10, 10),
									ts_shape = (8, 8),
									parent_unit = None,
									unit_type = MPF_UT_SENSOR
								)
				)
				
				for x in xrange(i*self.UNIT_VF[0], (i+1)*self.UNIT_VF[0]):
					for y in xrange(j*self.UNIT_VF[1], (j+1)*self.UNIT_VF[1]):
						self._grid_map.append(x*mth._nd_array_grid.shape[1] + y)
						
		#print self._grid_map
		
		
		self._l0_units.append(MPF_Unit_RL(
			ss_class = Miller_SOM,
			ts_class = Miller_SOM,
			input_dim = 4,
			ss_shape = (1, 4),
			ts_shape = (1, 10),
			parent_unit = None,
			unit_type = MPF_UT_ACTUATOR)
		)
		
		#self._l0_units[-1].ss.neurons += 1.0
		#self._l0_units[-1].ss.neurons *= 4.0
		#self._l0_units[-1].ss.neurons[:] = linspace(0.0, 4.0, 
		#					self._l0_units[-1].ss.neurons.shape[0])[:, None]#array([0.5, 1.5, 2.5, 2.5])[:, None]
		
		#self._l0_units[-1].ss.init_generative_gmm('full')
		
		#for unit in self._l0_units:
			#unit.ts.init_generative_gmm('tied')

		self._mpf_h = MPF_Hierarchy(self._l0_units, 4, 20, "K:/__temp/mpf_rl_dumps")
		
		#self._mpf_h.top_unit.ss.init_generative_gmm('full')
		#self._mpf_h.top_unit.ts.init_generative_gmm('full')
		
		#for unit in self._mpf_h.top_unit.children_units:
			#unit.ss.init_generative_gmm('full')
			
			
		# initial direction
		self.direction = self._dirs_names[1]
	
	def ressurect(self):
		if (not self.alive):
			self.alive = True
			self.coords = mth.getStartCoords(1)
			self.direction = self._dirs_names[1]
			
			#self.coords = mth.getStartCoords(random.randint(1, 4))
			#self.direction = self._dirs_names[random.randint(1, 4)]
			
			self.reinforcement -= 1.0
			
			self._iterations_num = 0
			
	def __sample_from_pmf(self, pmf, nominals):
		# normalize PMF to make it "proper"
		abs(pmf, out = pmf)
		
		# -- CDF
		bins = cumsum(pmf)
		
		if (bins[-1] == 0.0):
			print pmf
			raise ValueError
		
		bins /= bins[-1] # normalization
		
		return nominals[digitize(random.random_sample(1), bins)]
	
	def updateDirection(self, grid):
		# map grid to linear input vector
		self._input_vec[:-4] = grid.flatten()[self._grid_map]
		
		# actuator value from _really_ taken action
		self._input_vec[-4:] = 0.0
		self._input_vec[-4 + self._dirs_ids[self.direction]] = 1.0
		
		# evaluate hierarchy
		res_dir_distr = self._mpf_h.evaluate(self._input_vec, self.reinforcement)
		
		if (self._iterations_num / 20 > 0) and (self._iterations_num % 20 == 0):
			print "\n !!! Stil alive for %d !!!\n" % (self._iterations_num)
		
			self.reinforcement += 0.1
			if (self.reinforcement > 1.0): self.reinforcement = 1.0
		
		# decode actuator's value
		self.direction = self._dirs_names[self.__sample_from_pmf(res_dir_distr, self._dirs_ids.values())]
		print res_dir_distr, self.direction, self._mpf_h.reinforcement_prime
		
		self._iterations_num += 1
		
	def apply_reinforcement(self, grid, reinforcement):
		"""
		print "\n========== PUNISHMENT ============="
		#for i in xrange(15):
			#self.reinforcement -= 0.9 / 15.0
			#if (self.reinforcement < -1.0): self.reinforcement = -1.0
		
		# map grid to linear input vector
		self._input_vec[:-4] = grid.flatten()[self._grid_map]
		
		# actuator value from _really_ taken action
		self._input_vec[-4:] = 0.0
		self._input_vec[-4 + self._dirs_ids[self.direction]] = 1.0
		
		# evaluate hierarchy
		self.reinforcement = reinforcement
		res_dir_distr = self._mpf_h.evaluate(self._input_vec, reinforcement)
		print res_dir_distr, self.direction, self._mpf_h.reinforcement_prime
			
		print "========== END OF PUNISHMENT =============\n" 
		"""
		
		pass