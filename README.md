# CollisonDetectionCoppeliasimUR5
This repository contains a simple version of UR5 robot arm in the scene. The goal is to implement collision detection. The collision detection script is in main script of the scene.
The robot arm color converts from green to red if a collision is detected. 
The python code is the client. Which is used to start the collision detection and span objects. These objects should also be detectable by the robot arm and considered a collision.
The connection to the server at the moment is made by both using ZeroMQ API and legacy API. In the future, it should be changed to ZeroMQ only.


# packages
- numpy
- os 

# running 
- Ubuntu20.4
- Run CoppeliaSim_Edu_V4_3_0 and load the scene
- Run the client-side 

python main.py


objects should start spawning in the scene

# problem 
the cuboid object is detectable 
the small spawned objects are not detectable
