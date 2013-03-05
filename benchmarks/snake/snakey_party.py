#!/usr/bin/env python
# A Snakey clone made with Pygame.
# Requires Pygame: http://pygame.org/download.shtml
# Includes various fruits with different effects in regards to score,
# snake size, and other in-game effects.
# Includes various Snake AIs and game modes (Arcade, Duel, Party).

import random, pygame, sys
from pygame.locals import *
from classes.const import *
from classes.methods import *
from classes.button import *
from classes.snake import *
from classes.fruit import *
from classes.gamedata import *

from numpy import random
			

_mpfbot = OpponentMPF(MPFBOT, getStartCoords(1), GREEN, BLUE, 10, 10, -15, [30, 5, 60, 30, 35, 100, 100])


def main():
	#global FPSCLOCK, DISPLAYSURF, DEBUG

	#pygame.init()
	#FPSCLOCK = pygame.time.Clock()
	#DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
	pygame.display.set_caption('Snakey Party')

	arcadebutton = Button('(a)rcade mode', WINDOWWIDTH / 2, WINDOWHEIGHT * 2/8)
	duelbutton = Button('(d)uel mode', WINDOWWIDTH / 2, WINDOWHEIGHT * 3/8)
	partybutton = Button('(p)arty mode', WINDOWWIDTH / 2, WINDOWHEIGHT * 4/8)
	tronybutton = Button('(t)ron-y mode', WINDOWWIDTH / 2, WINDOWHEIGHT * 5/8)
	sandboxbutton = Button('(s)andbox mode', WINDOWWIDTH / 2, WINDOWHEIGHT * 6/8)
	instructbutton = Button('(i)nstructions', WINDOWWIDTH / 2, WINDOWHEIGHT * 7/8)

	while True: ### need to update this

		DISPLAYSURF.fill(BACKGROUNDCLR)
		drawTitle('Snakey Party', WINDOWWIDTH / 2, WINDOWHEIGHT * 1/8, XLARGETITLE, GREEN, True)
		arcadebutton.display()
		duelbutton.display()
		partybutton.display()
		tronybutton.display()
		sandboxbutton.display()
		instructbutton.display()

		for event in pygame.event.get():
			if event.type == QUIT:
				terminate()
			elif event.type == MOUSEBUTTONDOWN:
				mouse = pygame.mouse.get_pos()
				if arcadebutton.pressed(mouse):
					pygame.event.get()
					game = GameData()
					runGame(game, [LINUS])
					showGameOverScreen()
				elif duelbutton.pressed(mouse):
					pygame.event.get()
					players = False
					players = showSelectPlayersScreen()
					if players != False:
						game = GameData(10, 10, 9, 2)
						runGame(game, players)
						showGameOverScreen()
				elif partybutton.pressed(mouse):
					pygame.event.get()
					game = GameData(25, 12, 0, 4)
					players = getPlayers()
					runGame(game, players)
					showGameOverScreen()
				elif tronybutton.pressed(mouse):
					pygame.event.get()
					game = GameData(25, 12, 0, 0)
					game.trailing = True
					runGame(game, [SNAKEY, LINUS, WIGGLES, GOOBER])
					showGameOverScreen()
				elif sandboxbutton.pressed(mouse):
					showSandboxScreen()
				elif instructbutton.pressed(mouse):
					showInstructScreen()
			elif event.type == KEYDOWN:
				if event.key == K_a:
					pygame.event.get()
					game = GameData()
					iter = 0
					
					while (iter <= 10000):
						pygame.display.set_caption("Iteration: %d" % (iter))
						
						runGame(game, [MPFBOT])
						
						iter += 1
						
					showGameOverScreen()
				elif event.key == K_d:
					pygame.event.get()
					players = False
					players = showSelectPlayersScreen()
					if players != False:
						game = GameData(10, 10, 9, 2)
						runGame(game, players)
						showGameOverScreen()
				elif event.key == K_p:
					pygame.event.get()
					game = GameData(25, 12, 0, 4)
					players = getPlayers()
					runGame(game, players)
					showGameOverScreen()
				elif event.key == K_t:
					pygame.event.get()
					game = GameData(25, 12, 0, 0)
					game.trailing = True
					runGame(game, [SNAKEY, LINUS, WIGGLES, GOOBER])
					showGameOverScreen()
				elif event.key == K_s:
					showSandboxScreen()
				elif event.key == K_i:
					showInstructScreen()
				elif event.key == K_ESCAPE or event.key == K_q:
					terminate()

		game = False
		pygame.display.update()
		FPSCLOCK.tick(FPS)
		

def runGame(game, players=[]):

	# in game variables
	allsnake = []
	allfruit = []
	nextEvent = 0

	# create snakes based on name. 'player' is set to false initially to handle input
	player = False
	pos = 1
	for snake in players:
		if snake == SNAKEY:
			player = Snake(SNAKEY, getStartCoords(pos))
			allsnake.append(player)
			pos = pos + 1
		elif snake == LINUS:
			linus = Opponent(LINUS, getStartCoords(pos), IVORY, DARKGRAY, 5, 20, -10)
			allsnake.append(linus)
			pos = pos + 1
		elif snake == WIGGLES:
			wiggles = Opponent(WIGGLES, getStartCoords(pos), SLATEBLUE, COBALTGREEN, 15, 5, -5, [60, -10, 40, 10, 25, 100, 5])
			allsnake.append(wiggles)
			pos = pos + 1
		elif snake == GOOBER:
			goober = Opponent(GOOBER, getStartCoords(pos), PINK, RED, 10, 10, -15, [30, 5, 60, 30, 35, 100, 100])
			allsnake.append(goober)
			pos = pos + 1
		elif snake == MPFBOT:
			_mpfbot.ressurect()
			
			allsnake.append(_mpfbot)
			pos = pos + 1

	# create initial apple(s)
	appleCounter = game.apples
	while appleCounter > 0:
		a = Apple(allfruit, allsnake, game)
		allfruit.append(a)
		appleCounter = appleCounter - 1
	
	# main game loop
	while True:
	
		# get grid representation for AIs
		grid = getGrid(allsnake, allfruit)
		nd_array_grid = get_grid_nd_array(allsnake, allfruit)
		
		# event handling loop -- get player's direction choice
		stop = False
		
		# get events in queue. This updates players direction and other key instructions (quit, debug...)
		# if the next event after direction update suggests sharp direction change, following direction is stored.
		for event in pygame.event.get():
			if event.type == QUIT:
				terminate()
			elif nextEvent != 0 and player != False:
				player.direction = nextEvent
				nextEvent = 0
				stop = True
			# check for exit/quit/debug keys
			if event.type == KEYDOWN and \
			   (event.key == K_ESCAPE or event.key == K_q):
				terminate()
			elif event.type == KEYDOWN and event.key == K_e:
				showGameStats(allsnake)
				return 1
			elif event.type == KEYDOWN and event.key == K_g and DEBUG == True:
				stop = True
				debugPrintGrid(grid)
			# if player is dead / does not exist - check for speed controls
			elif event.type == KEYDOWN and event.key == K_f and \
				 (player == False or player.alive == False):
				game.updateBaseSpeed(10)
				game.updateCurrentSpeed(False, True)
			elif event.type == KEYDOWN and event.key == K_s and \
				 (player == False or player.alive == False):
				game.updateBaseSpeed(-10)
				game.updateCurrentSpeed(False, True)

			# if player exists - check for direction input
			if event.type == KEYDOWN and \
			   player != False and stop == False:
				if event.key == K_LEFT and player.direction != RIGHT:
					player.direction = LEFT
					stop = True
				elif event.key == K_RIGHT and player.direction != LEFT:
					player.direction = RIGHT
					stop = True
				elif event.key == K_UP and player.direction != DOWN:
					player.direction = UP
					stop = True
				elif event.key == K_DOWN and player.direction != UP:
					player.direction = DOWN
					
			# peak into very next event. If key suggests sharp direction change, store in nextEvent
			elif event.type == KEYDOWN and player != False and nextEvent == 0:
				if event.key == K_LEFT and player.direction != RIGHT:
					nextEvent = LEFT
				elif event.key == K_RIGHT and player.direction != LEFT:
					nextEvent = RIGHT
				elif event.key == K_UP and player.direction != DOWN:
					nextEvent = UP
				elif event.key == K_DOWN and player.direction != UP:
					nextEvent = DOWN
				elif event.key == K_ESCAPE or event.key == K_q:
					terminate()
				elif event.key == K_g and DEBUG == True:
					debugPrintGrid(grid)
					
		if DEBUG == True:
			debugPause()
		
		# update all other snake's direction choice
		for snake in allsnake:
			if snake.alive and snake.player == False:
				if (snake.__class__ == OpponentMPF):
					snake.updateDirection(nd_array_grid)
				else:
					snake.updateDirection(grid)

		# collision detection
		for snake in allsnake:
			# check if the snake has hit boundary
			if snake.alive and snake.boundsCollision():
				snake.alive = False
				if (snake.__class__ == OpponentMPF):
					snake.apply_reinforcement(nd_array_grid, -0.1)
				
			# check if snake has hit another snake
			for othersnake in allsnake:
				if snake.alive and snake.snakeCollision(othersnake):
					snake.alive = False
					if (snake.__class__ == OpponentMPF):
						snake.apply_reinforcement(nd_array_grid, -0.1)

		# check if fruit has been eaten by a snake
		for snake in allsnake:
			for fruit in allfruit:
				if snake.alive and snake.fruitCollision(fruit):
					snake.reinforcement = 1.0
					
					fruit.isEaten(snake, game)
					# apples have special adding properties
					if fruit.__class__ == Apple:
						# check for speed increase
						if game.checkSpeedTrigger():
							game.updateBaseSpeed(1)
						# check for fruit bonus drop
						if game.checkBonusTrigger():
							game.runBonusFruit(allfruit, allsnake)
						# run usual fruid drop
						game.runDrop(allfruit, allsnake)
					# blueberries have special speed adjusting properties
					elif fruit.__class__ == Blueberry:
						# update game frames to be 'slow' by 7 seconds
						game.slowtimer = game.slowtimer + game.currentspeed * 7
					# remove fruit
					allfruit.remove(fruit)

		# check for snake death, update place and end game if no more snakes are alive
		if game.checkSnakeDeath(allsnake):
			#showGameStats(allsnake)
			return 1

		# check for size changes / move snake
		for snake in allsnake:
			snake.move(game.trailing)

		# check multiplier and adjust color and multiplier as needed
		for snake in allsnake:
			if snake.multipliertimer > 0:
				snake.multipliertimer = snake.multipliertimer - 1
				snake.setColorBorderCurrent(PURPLE)
			else:
				# make sure multiplier is 1, color is normal
				snake.multiplier = 1
				snake.resetColorBorder()

		# update timers on fruits, remove if necessary
		for fruit in allfruit:
			if fruit.__class__ != Apple:
				if fruit.updateTimer() == False:
					# if timer on Egg expires, hatch new snake
					if fruit.__class__ == Egg:
						fruit.isHatched(allsnake)
					allfruit.remove(fruit)
					
		# draw everything to screen
		game.drawScreen(allfruit, allsnake, player)


if __name__ == '__main__':
	main()
