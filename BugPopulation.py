
import logging

'''
This is to encapsulate the population interface.

A population will be used to control a group of bugs for mating, fitness evaluation.  
A population will evolve separately from other populations (e.g., herbivore, carnivore, omnivore will all evolve sep)

Reqs:
- Population will contain a pointer to all bugs in it
- Population will be able to trigger a new bug creation (maybe only creates the gene)
- Population will be able to remove a bug from the world (by setting health to zero)
- Has the concept of a generation
- Loop through a population and control mating and thinning
- Episodic control on the length of a generation
- could control population based on generation/fitness or strongest survive
- Need to rebuild the population if it starts to die off (maybe use the logistic function for this?)

- Need to be able to create a bug from a gene
- Need to store a gene so can start a sim from there


BugPopulations -- holds all of the populations that have brains

BugPopulation -- a single population that has all the same type of bug in it. e.g., OMN

BugPopulationInterface -- a bug must implement this interface to participate in a population



'''