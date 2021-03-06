import numpy as np
from functools import partial


import ai as maximin_ai
import mpfrl_ai as ai
import montecarlo_ai as mc_ai

MAX_GAMES_NUM = 10000

EMPTY = 0.0
NOUGHT = 0.5
CROSS = 1.0

GF_VISUAL = {EMPTY: '| |', NOUGHT: '|O|', CROSS: '|X|'}

game_field = np.zeros((3, 3))

player_side = None
ai_side_name = None

last_winner = None

def show_game_field():
	for i in xrange(game_field.shape[0]):
		print " _ " * 3
		print "".join([GF_VISUAL[game_field[i, j]] for j in xrange(game_field.shape[1])])
		print " - " * 3
	
	print "\n"
	
def check_win():
	global last_winner
	
	prod_hvd = []
	
	# diagonals
	prod_hvd.append(np.prod(np.diag(game_field)))
	prod_hvd.append(np.prod(np.diag(game_field[::-1])))
	
	# verticals and horizontals
	for i in xrange(game_field.shape[0]):
		prod_hvd.append(np.prod(game_field[i, :]))
		prod_hvd.append(np.prod(game_field[:, i]))
	
	for _prod in prod_hvd:
		if (_prod == (player_side)**3):
			last_winner = 1
			return "Player won!"
		elif (_prod == (ai.my_side)**3):
			last_winner = 2
			return "AI won!"
	
	if (game_field[game_field == EMPTY].shape[0] == 0):
		last_winner = 0
		return "Draw!"
		
	return None

def play_game():
	global player_side
	global ai_side_name
	global game_field
	global last_winner
	
	def __player_move(reinf = 0.0):
		#show_game_field()
		
		move_ok = False
		
		while(not move_ok):
			move = raw_input("Move (row,column) --> ").split(",")
			
			if (len(move) < 2): continue
			
			try:
				m_x = int(move[0])
				m_y = int(move[1])
			except:
				continue
			
			if ((m_x < 0) or (m_x >= game_field.shape[0]) or
				(m_y < 0) or (m_y >= game_field.shape[1])): continue
				
			if (game_field[m_x, m_y] != EMPTY): continue
			
			# make move if everything OK
			game_field[m_x, m_y] = player_side
			move_ok = True
		
		#show_game_field()
		
	def __print_avg_ranks(moves_ranks, moves_num):
		moves_ranks = moves_ranks / moves_num
			
		print "\n" + "="*60 + "\nAvg move RANK: %f vs %f\n" % \
									(moves_ranks[0], moves_ranks[1])
		print "="*60 + "\n"
		
	
	stop_game = False
	
	# choose side
	while (player_side == None):
		side = raw_input("Choose your side [O/X] --> ").lower()
		
		if (side == "o"):
			player_side = NOUGHT
			player_side_name = "nought"
			
			ai_side_name = "cross"
			
		elif (side == "x"):
			player_side = CROSS
			player_side_name = "cross"
			
			ai_side_name = "nought"
			
	
	ai.init(ai_side_name)
	mc_ai.init(ai_side_name)
	
	maximin_ai.init(player_side_name)
	#maximin_ai.init(ai_side_name)

	
	print "----------------------\n\n"
	
	# opponents in sequential order
	opponents_move_funcs = [None, None]
	side_names = [None, None]
	
	#opponents_move_funcs[int(player_side < ai.my_side)] = __player_move
	
	
	opponents_move_funcs[int(player_side < ai.my_side)] = \
		partial(maximin_ai.make_move, game_field[:])
	
	opponents_move_funcs[int(player_side > ai.my_side)] = \
		partial(ai.make_move, game_field[:])
	
	side_names[int(player_side < ai.my_side)] = player_side_name
	side_names[int(player_side > ai.my_side)] = ai_side_name
	
	game_no = 0
	reinforcement = 0.0
	score = np.zeros(2)
	draws = 0 # counts draws
	
	moves_ranks = np.zeros(2)
	moves_num = np.zeros(2)
	
	while (game_no < MAX_GAMES_NUM):
		print "\n ================= GAME #%d =================\n" % (game_no)
		
		game_field[:] = np.zeros((3, 3))
		
		# main loop
		turn_iter = 0
		
		while (not stop_game):
			show_game_field()
			
			res = check_win()
			if (res != None):
				if (last_winner == 2):
					reinforcement = 1.0
					score[1] += 1
					
				elif (last_winner == 1):
					reinforcement = -1.0
					score[0] += 1
					
				else:
					reinforcement = 1.0 # 0.5
					#score += 1
					
					draws += 1
				
				last_winner = None
				
				
				print res
				
				break
			
			prev_game_field = game_field.copy()
			
			opponents_move_funcs[turn_iter % 2](reinforcement)
			
			move_rank = maximin_ai.rank_move(
						prev_game_field[:],
						game_field[:],
						side_names[turn_iter % 2]
			)
			moves_ranks[turn_iter % 2] += move_rank
			moves_num[turn_iter % 2] += 1
			
			#print "\n--\tMOVE RANK: %f\n--" % (move_rank)
			
			if (reinforcement != 0.0):
				reinforcement -= np.sign(reinforcement) * 0.5
				
			if ((ai.SIDES_NOMINALS[side_names[turn_iter % 2]] == ai.my_side) and
				(move_rank > 0)):
				
				reinforcement += 1.0
				
			
			turn_iter += 1
		
		
		print "\n ================= END OF GAME =================\n"
		print "\t\tSCORE: %d VS %d\n\t\tDRAWS: %d\n" % (score[0], score[1], draws)
		
		__print_avg_ranks(moves_ranks, moves_num)
		
		game_no += 1
		
		#time.sleep(2)
	
		
play_game()
		