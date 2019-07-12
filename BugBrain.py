
import logging
import neat

'''
This encapsulates the functionality of a bug brain.  Everything is at the individual genome level

- A brain has inputs and outputs
- A brain structure is controlled by a gene
- needs to normalize inputs
- be able to display itself
- be able to store the gene so can start from there
- should have bias neurons
- can have periodic neurons to invoke time/dependent behavior

BugBrainInterface -- a bug must implement this interface to have a brain
	- has a genome
	- brain is created from genome
	- has inputs and outputs from the brain
	- must normalize its own inputs
	- must support an activation method so can take inputs and provide outputs

- Must be able to create a new bug from a genome.

- Must be able to save itself to a file and save the file name
- Must be able to load itself from a file to create
- Must hide what type of network is being used(e.g., FF, RNN, CTRNN)
'''

class BugBrainInterface:

	# assume that the inputs are set before activate
	# have local variables for holding the results of collision data
	#TODO: make sure reset collision data on the bug after activation call

	_right_eye_color = tuple() #
	_left_eye_color = tuple()

	def __init__(self, config, genome):
		if genome:
			#create a brain with a genome
			pass
		else:
			#use the config to create a genome
			#create a brain with a genome
			pass


	def create_brain(self, config, genome):
		# create a new brain
		# all comes from DefaultGenome section of the config file
		self.net = neat.nn.feed_forward.FeedForwardNetwork.create(genome, config)

	def activate(self, genome, config):
		# normalize inputs
		# activate the neural net
		# update state if outputs are to be used as inputs
		# return outputs

		# get the inputs to the net from the sensors
		inputs = self.get_scaled_state()
	
		#run the inputs the nets activation collect the outputs (i.e., action)
		action = self.net.activate(inputs)

		'''
		Outputs Phase 1
	
		- right_wheel_velocity
		- left_wheel_velocity
		'''
		return action


def update_brain_inputs(right_eye, left_eye, ):
	pass

def get_scaled_state(self):

	# must match num_inputs from config file

	''' Inputs:
	Phase 1
	- right eye( from collision data )
	- left eye(from collision data)
	- health
	- energy
	- age ... maybe a component of score?
	- score (add to the score when something good happens e.g., health goes up, energy goes up, movement)
		this can be used for the fitness function or for reinforcement learning

- wheel velocity from last step (or could let this evolve a recurrent connection)

- bias neuron to encourage movement

'''
	pass


'''
** energy usage is proportional to velocity

Phase 2
- direction in the eyes
- sound
- smell
- communication

Outputs
Phase 1
- right wheel velocity
- left wheel velocity

Phase 2
- body color
- emit sound
- emit odor
- communicate

'''