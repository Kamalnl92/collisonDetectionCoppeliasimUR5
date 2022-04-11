from robot import Robot
import numpy as np

import time
def go():

    stage = "grasp_only"
    obj_mesh_dir = "/home/kamal/Desktop/UR5/RobotUR5/objects/blocks" #blocks #novel_objects
    num_obj = 5
    workspace_limits = np.asarray([[-0.724, -0.276], [-0.224, 0.224], [-0.0001, 0.4]])
    is_testing = False
    test_preset_cases = False
    test_preset_file = None
    goal_conditioned = True
    grasp_goal_conditioned = False



    robot = Robot(stage, obj_mesh_dir, num_obj, workspace_limits,
                   is_testing, test_preset_cases, test_preset_file,
                   goal_conditioned, grasp_goal_conditioned)
    # chance to adjust the camera
    time.sleep(1)
    robot.add_objects()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    go()

