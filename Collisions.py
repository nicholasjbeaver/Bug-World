
'''
Collision API
	Collisions() - container for the list of objects.  There are two types: emitters and detectors.  Detectors only detect things in the emitters list.
	CollisionObject() - necessary parent class to participate in the API

	Usage:
		1) Create a Collisions object (CO)
		2) The CO is responsible for know what collisions it needs to register for
		3) The CO must have a pointer to its container.  This allows a recursive search to make sure it isn't "colliding" with itself
		4) The CO must have a callback method to call when they do collide with something
		5) The CO shouldn't asked to be removed from the lists when it is marked from deletion.

	Definitions:
		1) Hitbox is the object that gets detected.  Sometimes the hitbox is the object.  Other times, the hitbox is a child
		   off of the object because it is offset from the object
		2) Hitbox type will be used to use circles, bounding boxes etc.  Would like to do a cone for eyesight to get directionality
		3) Maybe do a 1-d ray trace?


'''

#Use transforms to represent absolute position, that way always know regardless of env


'''
	Class: CollisionObject
		- Is a base class

'''

class CollisionObject():

	class HitBoxType():
		HITBOX_CIRCLE = int(1)
		HITBOX_RECT	= int(2)

	def __init__( Self ):
		Self.set_hitbox_type( Self )
		#must be added too in sublass so that if an object inherits this, it MUST know to add itself to a Collisions list.

	def get_abs_x(Self):
		#must override
		pass

	def get_abs_y(Self):
		#must override
		pass

	def get_size(Self):
		#must override and return radius
		pass

	def get_hitbox_type( Self ):
		return Self.hitbox_type


	def set_hitbox_type( Self ):
		Self.hitbox_type = Self.HitBoxType.HITBOX_CIRCLE

	def is_this_me( Self, co ):
		#check to see if the object to compare is itself or recursively its owner
#TODO - add recursion for the container.  E.g., bug contains eyes.  Eyes contain a hitbox.
		if( Self == co ): return True
		else: return False

class Collisions():

	def __init__( Self, handler_method ):
		Self._emitters = []
		Self._detectors = []
		Self._enabled = False # can be used to ignore a certain type of collisions
		Self._cb = handler_method

	def __repr__( Self ):
		return( 'Emitters(' + str(len( Self._emitters )) + '): ' + ' '.join(map(str, Self._emitters )) + '\n' + 'Detectors: ' + ' '.join(map(str, Self._detectors))) 

	def enable_collsions( Self ):
		Self._enabled = True

	def disable_collisions( Self ):
		Self._enabled = False

	def add_emitter(Self, collision_object ):
		Self._emitters.append( collision_object )

	def add_detector(Self, collision_object ):
		Self._detectors.append( collision_object )

	def del_emitter(Self, collision_object ):
#TODO - since objects will be removed occasionally, can iterate through for each one.  Assume there isn't mass deletion because then it would be better to 
#		mark for deletion and then process whole list
		#find object in list and remove it
		#should be called in the destructor method so that it is removed from all lists
		#See article: https://stackoverflow.com/questions/1207406/how-to-remove-items-from-a-list-while-iterating
		#somelist[:] = [x for x in somelist if not determine(x)]
		Self._emitters[:] = [co for co in Self._emitters if not co==collision_object]


	def del_detector(Self, collision_object ):
		Self._detectors[:] = [co for co in Self._detectors if not co==collision_object]
		pass	

	def print_collision( OB1, OB2 ):
		print( OB1.name + ', ' + OB2.name  )
		pass

	def circle_collision( Self, CO1, CO2 ):	#takes two Circle Hitbox Objects in.
		dx = CO1.get_abs_x() - CO2.get_abs_x()
		dy = CO1.get_abs_y() - CO2.get_abs_y()

		dist_sqrd = ( dx * dx ) + ( dy * dy )
		#size is radius of objections circle hit box
		if (dist_sqrd < (CO1.get_size() + CO2.get_size())**2) : return True
		else: return False

	def detect_collisions( Self ):
		#loop through solid bodies
		#call collision handlers on each object
		for CO1 in Self._detectors:
			for CO2 in Self._emitters:
				if CO1.is_this_me( CO2 ): continue #make sure the object is not part of the bug that owns it
				elif Self.circle_collision(CO1, CO2): #replace with hitbox stuff
					print("Emitter " + CO1.name + " detected " + CO2.name )

					#call the callback handler
					Self._cb(CO1,CO2)



#--- Testing Code after this point -------------------------------------------------------------------------------------------------------------

'''
	For an object to participate in Collision Detection it must inherit from the Collisions.CollisionObject class
	and must override the methods needed during collision detection
'''

class CTOType():
	#use integers so it is faster for dict lookups
	OBJ = int(1)  #catch all for the base class.  Shouldn't ever show up
	BUG = int(2)  #handles any bug interaction
	HERB = int(3) # Herbivore
	OMN = int(4)  # Omnivore
	CARN = int(5) # Carnivore 
	OBST = int(6) # Obstacle
	MEAT = int(7) # Food for Carnivore and Omnivore
	PLANT = int(8)# Food for Herbivore and Omnivore
	EYE = int(9)  # An eye that used for visual detection	

class CollisionTestObject( CollisionObject ):

	def __init__( Self, CollisionTestWorld, Owner, name, x, y, size ):
		Self.type = CTOType.OBJ #needs to be overwritten
		Self.name = name
		Self.x = x
		Self.y = y
		Self.size = size
		Self.World = CollisionTestWorld #handle back to container so can call instance methods on it.
		Self.Owner = Owner #for composite objects like eyes that are on the bug.  This would point to the bug

	def __repr__( Self ):
		return Self.name

	def get_abs_x( Self ):
		return Self.x

	def get_abs_y( Self ):
		return Self.y

	def get_size( Self ):
		return Self.size

	def is_this_me( Self, CO2 ):
		if 	( Self == CO2 ): True
		elif ( Self.Owner != None ):
			return ( Self.Owner.is_this_me( CO2 ))  #recursively call in case the comparision object is actually the owner.
		else:
			return False

	def kill( Self ): #must override this method so that it is removed from all of the event lists
		return

	def __del__( Self ):
		print("Destructor Called " + Self.name )


class CollisionTestBody( CollisionTestObject ):

	def __init__( Self, CTW, Owner, name, type, x, y, size ):
		super().__init__( CTW, Owner, name, x, y, size )
		Self.type = type 
		Self.World.register_collision_event( Self.World.CTWEventType.VISUAL_EMITTER, Self)
		Self.World.register_collision_event( Self.World.CTWEventType.PHYSICAL_DETECTOR, Self )
		Self.World.register_collision_event( Self.World.CTWEventType.PHYSICAL_EMITTER, Self )

	def kill( Self ):
#TODO
		#want to make sure it gets removed from all of the collision events
		#since the world creates in different lists, it should remove it from all of them
		#let's revisit though...probably should print a debug message here when something gets deleted at least
		Self.World.deregister_collision_event( Self.World.CTWEventType.VISUAL_EMITTER, Self)
		Self.World.deregister_collision_event( Self.World.CTWEventType.PHYSICAL_DETECTOR, Self )
		Self.World.deregister_collision_event( Self.World.CTWEventType.PHYSICAL_EMITTER, Self )
		print('About to die: ' + Self.name )





class CollisionTestEye( CollisionTestObject ):
	def __init__( Self, CTW, Owner, name, x, y, size ):
		super().__init__( CTW, Owner, name, x, y, size )
		Self.type = CTOType.EYE 
		Self.World.register_collision_event( Self.World.CTWEventType.VISUAL_DETECTOR, Self )

	def kill( Self ):
		Self.World.deregister_collision_event( Self.World.CTWEventType.VISUAL_DETECTOR, Self )
		print('About to die: ' + Self.name )


class CTWCollisionDict():

	def handle_collision( Self, detector, emitter ):
		Self.handle_dict( detector, emitter ) #the dector detected the emitter

	def handle_dict( Self, OB1, OB2 ):
		try:
			Self.CollisionDict[(OB1.type,OB2.type)]( OB1, OB2 ) #use types to lookup function to call and then call it
		except KeyError:
			print('No handler for: ' + OB1.name + ' T:' + str(OB1.type)	+ ", " + OB2.name + ' T:' + str(OB2.type))

	def print_collision( OB1, OB2 ):
		print( OB1.name + ' T:' + str(OB1.type)	+ ", " + OB2.name + ' T:' + str(OB2.type) )

	def herb_carn( herb, carn):
		CTWCollisionDict.print_collision( herb, carn )

	def carn_herb( carn, herb):
		CTWCollisionDict.print_collision( carn, herb )
	
	def herb_herb( herb1, herb2 ):
		CTWCollisionDict.print_collision( herb1, herb2 )
		#certain probability of mating?

	def carn_carn( carn1, carn2 ):
		CTWCollisionDict.print_collision( carn1, carn2 )
		#certain probability of mating?

	def bug_eye( bug, eye ):
		CTWCollisionDict.print_collision( bug, eye)
		#try using the superclass so can just detect color
		#could always replace with one hot vector classification for the brain so an eye detects a specific type of bug

	CollisionDict={ # look up which function to call when two objects of certain types collide
		( CTOType.HERB, CTOType.CARN ): herb_carn,
		( CTOType.HERB, CTOType.HERB): herb_herb,
		( CTOType.CARN, CTOType.CARN ): carn_carn,
		( CTOType.CARN, CTOType.CARN ): carn_herb,
		( CTOType.HERB, CTOType.EYE ): bug_eye,
		( CTOType.CARN, CTOType.EYE ): bug_eye
		}


class CollisionTestWorld():

	CTWDict = CTWCollisionDict()
	Bodies = []
	Eyes = []

	class CTWEventType():
		PHYSICAL_EMITTER = int(1)
		PHYSICAL_DETECTOR = int(2)
		VISUAL_EMITTER = int(3)
		VISUAL_DETECTOR = int(4)

	def handle_collision( Self, OB1, OB2 ):
		Self.CTWDict.handle_collision( OB1, OB2 )

	def __init__(Self):
		#Set up two different collision lists
		Self.PhysicalCollisions = Collisions( Self.handle_collision )
		Self.VisualCollisions = Collisions( Self.handle_collision )

	def register_collision_event( Self, collision_event_type, collision_object ):
		#this abstracts the collision lists from the objects.  They just register for an event.  The world handles where it goes
		if ( collision_event_type == Self.CTWEventType.PHYSICAL_EMITTER ):
#			print("Adding Physical Emitter: " + str(collision_object) )
			Self.PhysicalCollisions.add_emitter( collision_object )

		elif( collision_event_type == Self.CTWEventType.PHYSICAL_DETECTOR):
#			print("Adding Physical Detector: " + str(collision_object) )
			Self.PhysicalCollisions.add_detector( collision_object)

		elif( collision_event_type == Self.CTWEventType.VISUAL_EMITTER ):
#			print("Adding Visual Emitter: " + str(collision_object) )
			Self.VisualCollisions.add_emitter( collision_object )

		elif( collision_event_type == Self.CTWEventType.VISUAL_DETECTOR ):
#			print("Adding Visual Detector: " + str(collision_object) )
			Self.VisualCollisions.add_detector( collision_object )
		else:
			print( "Unsupported Event Type: " + collision_event_type )

	def deregister_collision_event( Self, collision_event_type, collision_object ):
		#this abstracts the collision lists from the objects.  They just register for an event.  The world handles where it goes
		if ( collision_event_type == Self.CTWEventType.PHYSICAL_EMITTER ):
			print("Deleting Physical Emitter: " + str(collision_object) )
			Self.PhysicalCollisions.del_emitter( collision_object )

		elif( collision_event_type == Self.CTWEventType.PHYSICAL_DETECTOR):
			print("Deleting Physical Detector: " + str(collision_object) )
			Self.PhysicalCollisions.del_detector( collision_object)

		elif( collision_event_type == Self.CTWEventType.VISUAL_EMITTER ):
			print("Deleting Visual Emitter: " + str(collision_object) )
			Self.VisualCollisions.del_emitter( collision_object )

		elif( collision_event_type == Self.CTWEventType.VISUAL_DETECTOR ):
			print("Deleting Visual Detector: " + str(collision_object) )
			Self.VisualCollisions.del_detector( collision_object )
		else:
			print( "Unsupported Event Type: " + collision_event_type )

	def check_for_collisions( Self ):
		Self.PhysicalCollisions.detect_collisions()
		Self.VisualCollisions.detect_collisions()
		

	def add_bodies( Self ):
		#x, y, size 
		locs = [(CTOType.HERB,0,0,5), (CTOType.HERB, 7,0,5), (CTOType.CARN, 9,5,3), (CTOType.HERB,6,3,2)]
		ctr = 0

		for pos in locs:
			ctr += 1
			name = "body" + str(ctr)
			Self.Bodies.append( CollisionTestBody( Self, None, name, pos[0], pos[1], pos[2], pos[3] ) )

	def add_eyes( Self ):
		#x, y, size 
		locs = [(-2,0,2), (5,0,2), (0,-20, 2)]
		ctr = 0

		for pos in locs:
			ctr += 1
			name = "Eye" + str(ctr)
			Self.Eyes.append( CollisionTestEye( Self, None, name, pos[0], pos[1], pos[2] ) )

	def del_body( Self ):
#TODO - not sure this is correct way of handling...really 
		#delete first object in list to see if destructors are called
		to_kill = Self.Bodies[0]
		to_kill.kill()
		Self.Bodies[:] = Self.Bodies[2:]
		del to_kill

	def test_all( Self ):
		#add the elements to the World

		print( "--- before any adds ---")
		print( "Physical Collisions:" )
		print( Self.PhysicalCollisions )
		print( "Visual Collisions:" )
		print( Self.VisualCollisions )
		print()

		Self.add_bodies()
		print( "--- after add bodies ---")
		print( "Physical Collisions:" )
		print( Self.PhysicalCollisions )
		print( "Visual Collisions:" )
		print( Self.VisualCollisions )
		print()

		Self.add_eyes()
		print( "--- after add eyes ---")
		print( "Physical Collisions:" )
		print( Self.PhysicalCollisions )
		print( "Visual Collisions:" )
		print( Self.VisualCollisions )
		print()

		Self.check_for_collisions()
		print("After Collision Check")
		print()

		Self.del_body()
		print("After delete body")

		#Test cases

		#See if they were added properly

		#See if there are collisions

		#Delete an item ... make sure it isn't something iterating over

		#See if it was removed from the collision list

		#See if there collisions

		#Add another item
		#handle two subclasses colliding....eg carn,herb


	#test recursive isThisMe

	#test adding handler methods

	#test hitbox type checking

	#test bad cases: empty lists, wrong types, no handler, no bounding box type

	#test logging/printing

	#for eyes, sound etc, register only the closest one if multiple collisions

	

if __name__ == "__main__":
        g = CollisionTestWorld()
        g.test_all()



	