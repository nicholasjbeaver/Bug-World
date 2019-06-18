
import logging
import neat

'''
This encapsulates the functionality of a bug brain

- A brain has inputs and outputs
- A brain structure is controlled by a gene
- needs to normalize inputs
- be able to display itself
- be able to store the gene so can start from there
- should have bias neurons
- can have periodic neurons to invoke time/dependent behavior


Inputs:
Phase 1
- right eye( color, type, distance)
- left eye(color, type, distance)
- health
- energy
- age ... maybe a component of score?
- score (add to the score when something good happens e.g., health goes up, energy goes up, movement)
	this can be used for the fitness function or for reinforcement learning

- wheel velocity from last step (or could let this evolve a recurrent connection)

*** energy usage is proportional to velocity


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


BugBrainInterface -- a bug must implement this interface to have a brain
	- has a genome
	- brain is created from genome
	- has inputs and outputs from the brain
	- must normalize its own inputs
	- must register with the correct population
	- must support an activation method so can take inputs and provide outputs

- Must be able to create a new bug from a genome.

'''