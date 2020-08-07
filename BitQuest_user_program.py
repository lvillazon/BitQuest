'''
This problem was asked by Two Sigma.
Alice wants to join her school's Probability Student Club.
Membership dues are computed via one of two simple probabilistic games.
The first game: roll a die repeatedly. Stop rolling once you get a five
followed by a six. Your number of rolls is the amount you pay, in dollars.
The second game: same, except that the stopping condition is a five
followed by a five.
Which of the two games should Alice elect to play? Does it even matter?
Write a program to simulate the two games and calculate their expected value.
'''

import random

def die_roll():
    return random.randint(1, 6)

def play_game(a,b):
    roll = 0
    fee = 0
    while True:  # loop only quits when we return
        while roll != a:
            fee += 1
            roll = die_roll()
        if die_roll() == b:
            return fee +1
        else:
            fee += 1

games = 3

print("Game 1 - stops on a 5 + 6")
total = 0
for _ in range(games):
    total = total + play_game(5,6)
game1_ave = total / games
print("Average fee over", str(games), "games= $", str(game1_ave))

print("Game 2 - stops on a 5 + 5")
total = 0
for _ in range(games):
    total = total + play_game(5,5)
game2_ave = total / games
print("Average fee over", str(games), "games= $", str(game2_ave))
if game1_ave < game2_ave:
    print("game 1 is cheaper")
else:
    print("game 2 is cheaper")


