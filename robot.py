import os
import numpy as np
from simulation import vrep
import time
from zmqRemoteApi import RemoteAPIClient


class Robot(object):
    def __init__(self, stage, obj_mesh_dir, num_obj, workspace_limits,
                 is_testing, test_preset_cases, test_preset_file,
                 goal_conditioned, grasp_goal_conditioned):

        self.workspace_limits = workspace_limits
        self.num_obj = num_obj
        self.stage = stage
        self.goal_conditioned = goal_conditioned
        self.grasp_goal_conditioned = grasp_goal_conditioned
        self.flag = 1
        # Define colors for object meshes (Tableau palette)
        self.color_space = np.asarray([[78.0, 121.0, 167.0], # blue
                                        [156, 117, 95], # brown
                                        [242, 142, 43], # orange
                                        [237.0, 201.0, 72.0], # yellow
                                        [186, 176, 172], # gray
                                        [255.0, 87.0, 89.0], # red
                                        [176, 122, 161], # purpl
                                        [118, 183, 178], # cyan
                                        [255, 157, 167], # pink
                                        [58.0, 100.0, 140.0], # blue2
                                        [140, 107, 70], # brown2
                                        [220, 122, 23], # orange2
                                        [207.0, 160, 52], # yellow2
                                        [166, 156, 160] ])/255.0 # gray2
        # inserting the goal object colour green
        goal_bject = 3
        green_color = [89.0/255.0, 161.0/255.0, 79.0/255.0]
        self.color_space = np.insert(self.color_space, goal_bject, green_color, axis=0)
        # Read files in object mesh directory
        self.obj_mesh_dir = obj_mesh_dir
        self.mesh_list = os.listdir(self.obj_mesh_dir)

        for item in range(len(self.mesh_list)):
            self.obj_mesh_ind = item

        self.obj_mesh_color = self.color_space[np.asarray(range(self.num_obj)), :]

        # Connect to simulator
        vrep.simxFinish(-1) # Just in case, close all opened connections   # reason for only one vrep opening?????
        self.sim_client = vrep.simxStart('127.0.0.1', 19997, True, True, 5000, 5) # Connect to V-REP on port 19997
        if self.sim_client == -1:
            print('Failed to connect to simulation (V-REP remote API server). Exiting.')
            exit()
        else:
            print('Connected to simulation.')
            self.restart_sim()

        #zeroMQ
        print('Program started')
        client = RemoteAPIClient()
        self.sim = client.getObject('sim')
        print('simulation connected')


        # When simulation is not running, ZMQ message handling could be a bit
        # slow, since the idle loop runs at 8 Hz by default. So let's make
        # sure that the idle loop runs at full speed for this program:
        defaultIdleFps = self.sim.getInt32Param(self.sim.intparam_idle_fps)
        self.sim.setInt32Param(self.sim.intparam_idle_fps, 0)
        self.is_testing = is_testing
        self.test_preset_cases = test_preset_cases
        self.test_preset_file = test_preset_file

        # If testing, read object meshes and poses from test case file
        if self.is_testing and self.test_preset_cases:
            file = open(self.test_preset_file, 'r')
            file_content = file.readlines()
            self.test_obj_mesh_files = []
            self.test_obj_mesh_colors = []
            self.test_obj_positions = []
            self.test_obj_orientations = []
            for object_idx in range(self.num_obj):
                file_content_curr_object = file_content[object_idx].split()
                self.test_obj_mesh_files.append(os.path.join(self.obj_mesh_dir,file_content_curr_object[0]))
                self.test_obj_mesh_colors.append([float(file_content_curr_object[1]),float(file_content_curr_object[2]),float(file_content_curr_object[3])])
                self.test_obj_positions.append([float(file_content_curr_object[4]),float(file_content_curr_object[5]),float(file_content_curr_object[6])])
                self.test_obj_orientations.append([float(file_content_curr_object[7]),float(file_content_curr_object[8]),float(file_content_curr_object[9])])
            file.close()
            self.obj_mesh_color = np.asarray(self.test_obj_mesh_colors)

        # Add objects to simulation environment
        self.add_objects()

    def add_objects(self):

        # Add each object to robot workspace at x,y location and orientation (random or pre-loaded)
        self.object_handles = []
        sim_obj_handles = []

        if self.stage == 'grasp_only':
            obj_number = 3
            self.obj_mesh_ind = np.random.randint(0, len(self.mesh_list), size=self.num_obj)
            if self.goal_conditioned or self.grasp_goal_conditioned:
                obj_number = len(self.obj_mesh_ind)
        else:
            obj_number = len(self.obj_mesh_ind)
            print(obj_number)
        resx = []
        resy = []
        for object_idx in range(obj_number):
            print("object_idx", object_idx)
            curr_mesh_file = os.path.join(self.obj_mesh_dir, self.mesh_list[self.obj_mesh_ind[object_idx]])
            if self.is_testing and self.test_preset_cases:
                curr_mesh_file = self.test_obj_mesh_files[object_idx]
            curr_shape_name = 'shape_%02d' % object_idx
            drop_x = (self.workspace_limits[0][1] - self.workspace_limits[0][0] - 0.2) * np.random.random_sample() + self.workspace_limits[0][0] + 0.1
            drop_y = (self.workspace_limits[1][1] - self.workspace_limits[1][0] - 0.2) * np.random.random_sample() + self.workspace_limits[1][0] + 0.1  # + 0.1

            resx.append(drop_x)
            resy.append(drop_y)
            #for ind in range(len(resx)):
            if drop_x in resx and drop_y in resy:
                resx.pop()
                resy.pop()
                drop_x = (self.workspace_limits[0][1] - self.workspace_limits[0][0] - 0.2) * np.random.random_sample() + self.workspace_limits[0][0] + 0.1
                drop_y = (self.workspace_limits[1][1] - self.workspace_limits[1][0] - 0.2) * np.random.random_sample() + self.workspace_limits[1][0] + 0.1
                resx.append(drop_x)
                resy.append(drop_y)

            object_position = [drop_x, drop_y, 0.05]
            object_orientation = [0.0, 0.0, 4.33]
            print("orian")
            print(object_orientation)
            if self.is_testing and self.test_preset_cases:
                object_position = [self.test_obj_positions[object_idx][0], self.test_obj_positions[object_idx][1] + 0.1, self.test_obj_positions[object_idx][2]]
                object_orientation = [self.test_obj_orientations[object_idx][0], self.test_obj_orientations[object_idx][1], self.test_obj_orientations[object_idx][2]]
            object_color = [self.obj_mesh_color[object_idx][0], self.obj_mesh_color[object_idx][1], self.obj_mesh_color[object_idx][2]]
            ret_resp, ret_ints,ret_floats,ret_strings,ret_buffer = vrep.simxCallScriptFunction(self.sim_client, 'remoteApiCommandServer',vrep.sim_scripttype_childscript,'importShape',[0,0,255,0], object_position + object_orientation + object_color, [curr_mesh_file, curr_shape_name], bytearray(), vrep.simx_opmode_blocking)
            time.sleep(0.5)
            print(ret_resp)
            if ret_resp == 8:
                print('Failed to add new objects to simulation. Please restart.')
                exit()

            if len(ret_ints) <= 0:
                print("Len(ret_ints)", len(ret_ints))
                print("Restarting simulation and objects spawns")
                self.restart_sim()
                self.add_objects()
                break

            curr_shape_handle = ret_ints[0]
            self.object_handles.append(curr_shape_handle)
            if not (self.is_testing and self.test_preset_cases):
                time.sleep(0.5)
        self.prev_obj_positions = []
        self.obj_positions = []

        self.check_collision()
        # for testing the collisin Coppeliasim Forum
        while True:
            run = True


    def restart_sim(self):

        sim_ret, self.UR5_target_handle = vrep.simxGetObjectHandle(self.sim_client,'UR5_target',vrep.simx_opmode_blocking)
        vrep.simxSetObjectPosition(self.sim_client, self.UR5_target_handle, -1, (-0.5,0,0.3), vrep.simx_opmode_blocking)
        vrep.simxStopSimulation(self.sim_client, vrep.simx_opmode_blocking)
        vrep.simxStartSimulation(self.sim_client, vrep.simx_opmode_blocking)
        time.sleep(1)
        sim_ret, self.RG2_tip_handle = vrep.simxGetObjectHandle(self.sim_client, 'UR5_tip', vrep.simx_opmode_blocking)
        sim_ret, gripper_position = vrep.simxGetObjectPosition(self.sim_client, self.RG2_tip_handle, -1, vrep.simx_opmode_blocking)
        while gripper_position[2] > 0.4: # V-REP bug requiring multiple starts and stops to restart
            vrep.simxStopSimulation(self.sim_client, vrep.simx_opmode_blocking)
            vrep.simxStartSimulation(self.sim_client, vrep.simx_opmode_blocking)
            time.sleep(1)
            sim_ret, gripper_position = vrep.simxGetObjectPosition(self.sim_client, self.RG2_tip_handle, -1, vrep.simx_opmode_blocking)

    def check_collision(self):
        listAll = ['/Shape[0]', '/Shape[1]', '/Shape[2]', '/Shape[3]', '/Shape[4]', '/Shape[5]', '/Shape[6]', '/Shape[7]', '/Shape[8]', '/Shape[9]',
         '/Shape[10]', '/Shape[11]', '/Shape[12]', '/Shape[13]', '/Shape[14]', '/Shape[15]', '/Shape[16]', '/Shape[17]', '/Shape[18]',
         '/Shape[19]', '/Shape[20]']
        listSpawned = listAll.copy()
        listSpawned = listSpawned[0:self.num_obj]
        self.sim.callScriptFunction('check_Collision', self.sim.scripttype_mainscript, listSpawned)

    def stop_check_collision(self):
        self.sim.callScriptFunction('noCheckCollision', self.sim.scripttype_mainscript)
