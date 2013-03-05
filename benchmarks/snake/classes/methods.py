from const import *
from fruit import *
from button import *

import numpy as np

# pre-cache
_nd_array_grid = np.zeros(
				(CELLWIDTH, CELLHEIGHT + (TOP_BUFFER / CELLSIZE)), 
				dtype = np.float32
)

def getPlayers(num=3):
	"""
	Returns list containing Snakey and a number (only argument) of random snakes.
	"""
	players = [SNAKEY]

	while num > 0:
		nextPlayer = ''
		randPlayer = random.randint(1,3)
		if randPlayer == 1:
			nextPlayer = LINUS
		elif randPlayer == 2:
			nextPlayer = WIGGLES
		elif randPlayer == 3:
			nextPlayer = GOOBER
		players.append(nextPlayer)
		num = num - 1
		
	return players


def showSelectPlayersScreen():
	"""
	Blits player/opponent select onto screen. Returns selection as list.
	"""
	playerbuttons = []
	playersnakeybutton = SelectButton('(s)nakey', WINDOWWIDTH / 3, WINDOWHEIGHT * 2/7, SNAKEY, True)
	playerbuttons.append(playersnakeybutton)
	playerlinusbutton = SelectButton('(l)inus', WINDOWWIDTH / 3, WINDOWHEIGHT * 3/7, LINUS)
	playerbuttons.append(playerlinusbutton)
	playerwigglesbutton = SelectButton('(w)iggles', WINDOWWIDTH / 3, WINDOWHEIGHT * 4/7, WIGGLES)
	playerbuttons.append(playerwigglesbutton)
	playergooberbutton = SelectButton('(g)oober', WINDOWWIDTH / 3, WINDOWHEIGHT * 5/7, GOOBER)
	playerbuttons.append(playergooberbutton)
	
	opponentbuttons = []
	opponentlinusbutton = SelectButton('(l)inus', WINDOWWIDTH / 3 * 2, WINDOWHEIGHT * 3/7, LINUS, True)
	opponentbuttons.append(opponentlinusbutton)
	opponentwigglesbutton = SelectButton('(w)iggles', WINDOWWIDTH / 3 * 2, WINDOWHEIGHT * 4/7, WIGGLES)
	opponentbuttons.append(opponentwigglesbutton)
	opponentgooberbutton = SelectButton('(g)oober', WINDOWWIDTH / 3 * 2, WINDOWHEIGHT * 5/7, GOOBER)
	opponentbuttons.append(opponentgooberbutton)
	
	cancelbutton = Button('(e)xit', WINDOWWIDTH / 3, WINDOWHEIGHT * 6/7)
	acceptbutton = Button('(d)uel!', WINDOWWIDTH / 3 * 2, WINDOWHEIGHT * 6/7)
	
	DISPLAYSURF.fill(BACKGROUNDCLR)

	while True:
		
		drawTitle('Choose Match-up:')
		drawTitle('Player 1:', WINDOWWIDTH / 3, WINDOWHEIGHT * 1/7, MEDIUMTITLE, GOLDENROD, True)
		drawTitle('Player 2:', WINDOWWIDTH / 3 * 2, WINDOWHEIGHT * 1/7, MEDIUMTITLE, GOLDENROD, True)

		# display all buttons
		for button in playerbuttons:
			button.display()
		for button in opponentbuttons:
			button.display()
		cancelbutton.display()
		acceptbutton.display()

		for event in pygame.event.get():
			if event.type == QUIT:
				terminate()
			elif event.type == MOUSEBUTTONDOWN:
				mouse = pygame.mouse.get_pos()
				# check each button for player
				for button in playerbuttons:
					if button.pressed(mouse):
						button.setActive(playerbuttons)
				# check each button for opponent
				for button in opponentbuttons:
					if button.pressed(mouse):
						button.setActive(opponentbuttons)
				# check cancel/accept buttons
				if cancelbutton.pressed(mouse):
					pygame.event.get()
					return False
				elif acceptbutton.pressed(mouse):
					pygame.event.get()
					final = []
					for button in playerbuttons:
						if button.getActive():
							final.append(button.getValue())
					for button in opponentbuttons:
						if button.getActive():
							final.append(button.getValue())
					return final

			elif event.type == KEYDOWN:
				if event.key == K_s:
					pygame.event.get()
					playersnakeybutton.setActive(playerbuttons)
				elif event.key == K_l:
					pygame.event.get()
					opponentlinusbutton.setActive(opponentbuttons)
				elif event.key == K_w:
					pygame.event.get()
					opponentwigglesbutton.setActive(opponentbuttons)
				elif event.key == K_g:
					pygame.event.get()
					opponentgooberbutton.setActive(opponentbuttons)
				elif event.key == K_d:
					pygame.event.get()
					final = []
					for button in playerbuttons:
						if button.getActive():
							final.append(button.getValue())
					for button in opponentbuttons:
						if button.getActive():
							final.append(button.getValue())
					return final
				elif event.key == K_e:
					pygame.event.get()
					return False
				elif event.key == K_ESCAPE or event.key == K_q:
					terminate()

		pygame.display.update()


def showSandboxScreen():
	"""
	Blits sandbox mode onto screen.
	"""
	
	buttons = []
	snakesbutton = InputButton(1, WINDOWWIDTH * 2/3, WINDOWHEIGHT * 2/8, 1, 4, True)
	buttons.append(snakesbutton)
	fpsbutton = InputButton(12, WINDOWWIDTH * 2/3, WINDOWHEIGHT * 3/8, 3, 60)
	buttons.append(fpsbutton)
	

	cancelbutton = Button('(e)xit', WINDOWWIDTH * 1/3, WINDOWHEIGHT * 7/8)
	acceptbutton = Button('(s)tart', WINDOWWIDTH * 2/3, WINDOWHEIGHT * 7/8)

	while True:
	
		DISPLAYSURF.fill(BACKGROUNDCLR)
		
		drawTitle('Sandbox Mode:')
		drawTitle('Snakes:', WINDOWWIDTH * 1/3, WINDOWHEIGHT * 2/8, MEDIUMTITLE, GOLDENROD, True)
		drawTitle('Starting FPS:', WINDOWWIDTH * 1/3, WINDOWHEIGHT * 3/8, MEDIUMTITLE, GOLDENROD, True)

		# display all buttons
		
		snakesbutton.display()
		fpsbutton.display()
		cancelbutton.display()
		acceptbutton.display()

		for event in pygame.event.get():
			if event.type == QUIT:
				terminate()
			elif event.type == MOUSEBUTTONDOWN:
				mouse = pygame.mouse.get_pos()
				# check buttons
				for button in buttons:
					button.pressed(mouse, buttons)
				# check cancel/accept buttons
				if cancelbutton.pressed(mouse):
					pygame.event.get()
					return False
				elif acceptbutton.pressed(mouse):
					pygame.event.get()
					return False

			elif event.type == KEYDOWN:
				if event.key == K_s:
					pygame.event.get()
					return False
				elif event.key == K_e:
					pygame.event.get()
					return False
				elif event.key == K_ESCAPE or event.key == K_q:
					terminate()

		pygame.display.update()


def showInstructScreen():
	"""
	Blits instructions onto screen. Returns when exit button clicked / key pressed.
	"""
	
	def drawFruit(x, y, color):
		"""
		Responsible for drawing demo fruit to screen
		"""
		fruitRect = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
		pygame.draw.rect(DISPLAYSURF, color, fruitRect)
	
	endbutton = Button('(e)xit', WINDOWWIDTH * 3/6, WINDOWHEIGHT * 15/16)
	nextbutton = Button('(n)ext (->)', WINDOWWIDTH * 5/6, WINDOWHEIGHT * 15/16)
	prevbutton = Button('(<-) (p)rev', WINDOWWIDTH * 1/6, WINDOWHEIGHT * 15/16)
	
	page = 1
	
	while True:
	
		DISPLAYSURF.fill(BACKGROUNDCLR)

		drawTitle('Snakey Party', WINDOWWIDTH / 2, WINDOWHEIGHT * 1/16, MEDIUMTITLE, GREEN, True)
		drawTitle('Instructions', WINDOWWIDTH / 2, WINDOWHEIGHT * 3/16, MEDIUMTITLE, GREEN, True)
		
		if page == 1:
			drawMessage('A variation on a classic game, Snakey Party is a', 5, WINDOWHEIGHT * 4/16, GOLDENROD)
			drawMessage('Snakey clone made with Pygame.', 5, WINDOWHEIGHT * 5/16, GOLDENROD)
			drawMessage('Navigating Snakey with the arrow keys, avoid', 5, WINDOWHEIGHT * 6/16, GOLDENROD)
			drawMessage('boundaries and other snakes while enjoying a', 5, WINDOWHEIGHT * 7/16, GOLDENROD)
			drawMessage('buffet of tasty fruits!', 5, WINDOWHEIGHT * 8/16, GOLDENROD)
		elif page == 2:
			drawMessage('Fruits when eaten have different effects.', 5, WINDOWHEIGHT * 4/16, GOLDENROD)
			drawFruit(5, WINDOWHEIGHT * 5/16, RED)
			drawMessage('Apple (10 points) When eaten will generate more', 55, WINDOWHEIGHT * 5/16, RED)
			drawMessage('apples. They may also generate other fruits to appear.', 5, WINDOWHEIGHT * 6/16, RED)
			drawFruit(5, WINDOWHEIGHT * 7/16, GREEN)
			drawMessage('Poison (-25 points) Causes Snakey to shrink.', 55, WINDOWHEIGHT * 7/16, GREEN)
			drawFruit(5, WINDOWHEIGHT * 8/16, ORANGE)
			drawMessage('Orange (50 points) Worth lots of points, and will', 55, WINDOWHEIGHT * 8/16, ORANGE)
			drawMessage('cause Snakey to grow!', 5, WINDOWHEIGHT * 9/16, ORANGE)
			drawFruit(5, WINDOWHEIGHT * 10/16, PURPLE)
			drawMessage('Raspberry  Will cause all fruit to be worth double', 55, WINDOWHEIGHT * 10/16, PURPLE)
			drawMessage('for a short period of time (time stacks).', 5, WINDOWHEIGHT * 11/16, PURPLE)
			drawFruit(5, WINDOWHEIGHT * 12/16, BLUE)
			drawMessage('Blueberry (100 points) Slows everything down for a', 55, WINDOWHEIGHT * 12/16, BLUE)
			drawMessage('short period of time (time stacks).', 5, WINDOWHEIGHT * 13/16, BLUE)
		elif page == 3:
			drawMessage('Modes.', 5, WINDOWHEIGHT * 4/16, GOLDENROD)
		elif page == 4:
			drawMessage('AIs.', 5, WINDOWHEIGHT * 4/16, GOLDENROD)

		endbutton.display()
		if page > 1:
			prevbutton.display()
		if page < 4:
			nextbutton.display()

		for event in pygame.event.get():
			if event.type == QUIT:
				terminate()
			elif event.type == MOUSEBUTTONDOWN:
				mouse = pygame.mouse.get_pos()
				if endbutton.pressed(mouse):
					pygame.event.get()
					return
				elif nextbutton.pressed(mouse):
					page = page + 1
				elif prevbutton.pressed(mouse):
					page = page - 1
			elif event.type == KEYDOWN:
				if event.key == K_e or event.key == K_i:
					pygame.event.get()
					return
				elif (event.key == K_LEFT or event.key == K_p) and page > 1:
					page = page - 1
				elif (event.key == K_RIGHT or event.key == K_n) and page < 4:
					page = page + 1
				elif event.key == K_ESCAPE or event.key == K_q:
					terminate()

		pygame.display.update()


def terminate():
	"""
	Clean exit from pygame.
	"""
	pygame.quit()
	sys.exit()
	

def showGameStats(allsnake):
	"""
	Displays game stats for all snakes (scored) at end of game.
	Returns when any key pressed.
	"""
	totaldead = 0
	totalscored = 0
	for snake in allsnake:
		if snake.scored == True:
			totalscored = totalscored + 1
			if snake.alive == False:
				totaldead = totaldead + 1
	
	position = 1
	for snake in allsnake:
		if snake.scored == True:
			pos_x = getPosition(position, allsnake, totalscored)
			pos_y = WINDOWHEIGHT / 20
			drawMessage(snake.name, pos_x, WINDOWHEIGHT / 20 * 3, snake.getColor())
			if totalscored != 1:
				drawMessage('place: ' + str(snake.getPlace(totaldead, totalscored)), pos_x, pos_y * 5, snake.getColor())
			drawMessage('score: ' + str(snake.score), pos_x, pos_y * 6, snake.getColor())
			drawMessage('apples: ' + str(snake.fruitEaten['apple']), pos_x, pos_y * 7, RED)
			drawMessage('poison: ' + str(snake.fruitEaten['poison']), pos_x, pos_y * 8, GREEN)
			drawMessage('oranges: ' + str(snake.fruitEaten['orange']), pos_x, pos_y * 9, ORANGE)
			drawMessage('raspberries: ' + str(snake.fruitEaten['raspberry']), pos_x, pos_y * 10, PURPLE)
			drawMessage('blueberries: ' + str(snake.fruitEaten['blueberry']), pos_x, pos_y * 11, BLUE)
			drawMessage('eggs: ' + str(snake.fruitEaten['egg']), pos_x, pos_y * 12, WHITE)
			position = position + 1

	drawMessage('Press any key.', WINDOWWIDTH / 2, pos_y * 19, GOLDENROD)
	pygame.display.update()
	pygame.time.wait(300)
	pygame.event.get() # clear event queue
	showGameOverScreen()
	waitForInput()


def showGameOverScreen():
	"""
	Displays 'Game Over' message.
	Returns when any key pressed.
	"""
	drawTitle('Game Over', WINDOWWIDTH / 2, WINDOWHEIGHT * 3/4, LARGETITLE, WHITE, True)
	pygame.display.update()


def getGrid(allsnake, allfruit):
	"""
	Returns dictionary representation of all snakes and fruits on screen.
	Coordinates are entered as tuple (x,y).
	Used by AI when choosing best path.
	"""
	# refresh grid, dictionary representation of playing board used by AI
	grid = {(x,y):0 for x in range(CELLWIDTH) for y in range(CELLHEIGHT + (TOP_BUFFER / CELLSIZE))}
	
	# add snakes to grid
	for snake in allsnake:
		for snakebody in snake.coords:
			grid[(snakebody['x'], snakebody['y'])] = 'snake'
			   
	 # add fruits to grid
	for fruit in allfruit:
		if fruit.__class__ == Apple:
			grid[(fruit.coords['x'], fruit.coords['y'])] = 'apple'
		elif fruit.__class__ == Poison:
			grid[(fruit.coords['x'], fruit.coords['y'])] = 'poison'
		elif fruit.__class__ == Orange:
			grid[(fruit.coords['x'], fruit.coords['y'])] = 'orange'
		elif fruit.__class__ == Raspberry:
			grid[(fruit.coords['x'], fruit.coords['y'])] = 'raspberry'
		elif fruit.__class__ == Blueberry:
			grid[(fruit.coords['x'], fruit.coords['y'])] = 'blueberry'
		elif fruit.__class__ == Lemon:
			grid[(fruit.coords['x'], fruit.coords['y'])] = 'lemon'
		elif fruit.__class__ == Egg:
			grid[(fruit.coords['x'], fruit.coords['y'])] = 'egg'
	
	return grid

def get_grid_nd_array(allsnake, allfruit):
	"""
	returns grid as 2d numpy array
	"""
	
	_nd_array_grid[:] = 0
	
	# add snakes to grid
	for snake in allsnake:
		for snakebody in snake.coords:
			if ((snakebody['x'] < _nd_array_grid.shape[0]) or 
				(snakebody['x'] >= _nd_array_grid.shape[0]) or
				(snakebody['y'] < _nd_array_grid.shape[1]) or 
				(snakebody['y'] >= _nd_array_grid.shape[1])):
				
				continue
			
			_nd_array_grid[snakebody['x'], snakebody['y']] = 0.2
			   
	 # add fruits to _nd_array_grid
	for fruit in allfruit:
		if fruit.__class__ == Apple:
			_nd_array_grid[fruit.coords['x'], fruit.coords['y']] = 0.4
		elif fruit.__class__ == Poison:
			_nd_array_grid[fruit.coords['x'], fruit.coords['y']] = 0.5
		elif fruit.__class__ == Orange:
			_nd_array_grid[fruit.coords['x'], fruit.coords['y']] = 0.6
		elif fruit.__class__ == Raspberry:
			_nd_array_grid[fruit.coords['x'], fruit.coords['y']] = 0.7
		elif fruit.__class__ == Blueberry:
			_nd_array_grid[fruit.coords['x'], fruit.coords['y']] = 0.8
		elif fruit.__class__ == Lemon:
			_nd_array_grid[fruit.coords['x'], fruit.coords['y']] = 0.9
		elif fruit.__class__ == Egg:
			_nd_array_grid[fruit.coords['x'], fruit.coords['y']] = 1.0
	
	return _nd_array_grid
   
	
def drawMessage(text, x=1, y=1, color=MESSAGECLR, center=False):
	"""
	Draws message to screen.
	Size scales depending on window width / height
	Set so that 640x480 -> 18 pts.
		800x600 -> 28 pts.
	"""
	size = int (WINDOWWIDTH * WINDOWHEIGHT / 17000)
	font = pygame.font.Font('freesansbold.ttf', size)
	messageSurf = font.render(text, True, color, BACKGROUNDCLR)
	messageRect = messageSurf.get_rect()
	if center == False:
		messageRect.topleft = (x, y)
	else:
		messageRect.center = (x, y)
		
	DISPLAYSURF.blit(messageSurf, messageRect)
	
	
def drawTitle(text, x=1, y=1, size=MEDIUMTITLE, color=GREEN, center=False):
	titleFont = pygame.font.Font('freesansbold.ttf', size)
	titleSurf = titleFont.render(text, True, color, BACKGROUNDCLR)
	titleRect = titleSurf.get_rect()
	if center == False:
		titleRect.topleft = (x, y)
	else:
		titleRect.center = (x, y)

	DISPLAYSURF.blit(titleSurf, titleRect)


def debugPause():
	while True:
		if checkForKeyPress():
			return
			
			
def debugPrintGrid(grid):
	x = 0
	y = 0
	line = ""
	while grid.has_key((0,y)):
		if grid.has_key((x,y)):
			line = line + str(grid[(x,y)])[0]
			x = x + 1
		else:
			print line
			line = ""
			y = y + 1
			x = 0


def getPosition(position, allsnake, totalscored):
	return (WINDOWWIDTH - (float(position) / float(totalscored) * WINDOWWIDTH))
	

def getStartCoords(pos=1):
	if pos == 1:
		return [{'x':5, 'y':5},{'x':4, 'y':5},{'x':3, 'y':5}]
	elif pos == 2:
		return [{'x':CELLWIDTH-5, 'y':CELLHEIGHT-5},{'x':CELLWIDTH-4, 'y':CELLHEIGHT-5},{'x':CELLWIDTH-3, 'y':CELLHEIGHT-5}]
	elif pos == 3:
		return [{'x':CELLWIDTH-5, 'y':5},{'x':CELLWIDTH-4, 'y':5},{'x':CELLWIDTH-3, 'y':5}]
	elif pos == 4:
		return [{'x':5, 'y':CELLHEIGHT-5},{'x':4, 'y':CELLHEIGHT-5},{'x':3, 'y':CELLHEIGHT-5}]


def checkForKeyPress():
	"""
	Returns key pressed (unless quitting)
	"""
	if len(pygame.event.get(QUIT)) > 0:
		terminate()

	keyUpEvents = pygame.event.get(KEYUP)
	if len(keyUpEvents) == 0:
		return None
	if keyUpEvents[0].key == K_ESCAPE or keyUpEvents[0].key == K_q:
		terminate()
	return keyUpEvents[0].key
	
	
def waitForInput():
	"""
	Returns when key pressed or mouse clicked.
	Escapes/Quits as normal.
	"""
	while True:
		for event in pygame.event.get():
			if event.type == QUIT:
				terminate()
			elif event.type == KEYDOWN:
				if event.key == K_ESCAPE or event.key == K_q:
					terminate()
				else:
					return
			elif event.type == MOUSEBUTTONDOWN:
				if pygame.mouse.get_pressed() != None:
					return
