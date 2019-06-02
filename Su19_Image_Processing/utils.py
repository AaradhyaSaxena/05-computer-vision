import numpy as np
from matplotlib import pyplot as plt
import cv2
import glob

import math
from scipy import linalg
from numpy.linalg import inv
from sklearn import linear_model, datasets
from numpy import linalg as LA


# output = 3x3 projection_matrix, input image shape=(num_points,2); obj shape=(num_points,3)
def projection_matrix_direct(imgp1, objp):
    
    obj = objp.T
    ab = np.matmul(obj,obj.T)
    abinv = inv(ab)
    abc = np.matmul(obj.T,abinv)
    camera_matrix = np.matmul(imgp1,abc)
    
    return camera_matrix

# output = 3x3 projection_matrix, input image shape=(num_points,2); obj shape=(num_points,3) 
def projection_matrix3(img_p, obj_p):
    
    C = []

    for i in range(315):
        C.append(np.array([obj_p[i,0], obj_p[i,1],1,0,0,0, (-1)*obj_p[i,0]*img_p[i,0], 
                           (-1)*obj_p[i,1]*img_p[i,0], (-1)*img_p[i,0]]))
        C.append(np.array([0,0,0, obj_p[i,0], obj_p[i,1],1, 
                           (-1)*obj_p[i,0]*img_p[i,1], (-1)*obj_p[i,1]*img_p[i,1],(-1)*img_p[i,1]]))
    
    c = np.array(C)
    ctc = np.matmul(c.T,c)
    u, s, vh = np.linalg.svd(ctc, full_matrices=True)
    L = vh[-1]
    H = L.reshape(3, 3)
    H = H/H[-1,-1]
    
    return H

# output = 3x4 projection_matrix, input image shape=(num_points,2); obj shape=(num_points,3) 
def projection_matrix4(img_p, obj_p):
    
    C = []

    for i in range(obj_p.shape[0]):
        C.append(np.array([obj_p[i,0], obj_p[i,1], obj_p[i,2],1,0,0,0,0,(-1)*obj_p[i,0]*img_p[i,0], 
                           (-1)*obj_p[i,1]*img_p[i,0],(-1)*obj_p[i,2]*img_p[i,0], (-1)*img_p[i,0]]))
        
        C.append(np.array([0,0,0,0, obj_p[i,0], obj_p[i,1], obj_p[i,2],1,(-1)*obj_p[i,0]*img_p[i,1], 
                           (-1)*obj_p[i,1]*img_p[i,1], (-1)*obj_p[i,2]*img_p[i,1],(-1)*img_p[i,1]]))
    
    c = np.array(C)
    ctc = np.matmul(c.T,c)
    u, s, vh = np.linalg.svd(ctc, full_matrices=True)
    L = vh[-2]
    H = L.reshape(3, 4)

#     H = H/H[-1,-1]
    
    return H

def return_pcv(img_path, corners_, obj_p):
    objpoints = [] 
    imgpoints = []
    imgpoints.append(corners_)
    objpoints.append(obj_p)
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)
    rx = [[1,0,0],[0,math.cos(rvecs[0][0]),math.sin(rvecs[0][0])],[0,(-1)*math.sin(rvecs[0][0]),math.cos(rvecs[0][0])]]
    ry = [[math.cos(rvecs[0][1]),0,math.sin(rvecs[0][1])],[0,1,0],[(-1)*math.sin(rvecs[0][1]),0,math.cos(rvecs[0][1])]]
    rz = [[math.cos(rvecs[0][2]),math.sin(rvecs[0][2]),0],[(-1)*math.sin(rvecs[0][2]),math.cos(rvecs[0][2]),0],[0,0,1]]
    R1 = np.matmul(rx,ry)
    R = np.matmul(R1,rz)
    m = np.ones((3,4))
    m[:,:3] = R
    m[:,[3]]= np.array(tvecs)
    cv_homography = np.matmul(mtx,m)
    pcv = cv_homography/cv_homography[-1,-1]

    return pcv


# returns k,r1,r2 ; takes input of projection_matrix(3,4)
def RQ_decomposition(projection_matrix4):
    
    p1 = projection_matrix4[:,:3]
    p2 = projection_matrix4[:,3]
    
    k, r1 = linalg.rq(p1)
    #np.allclose(p1, k @ r1)
    k = k/k[-1,-1]
    
    r2 = np.matmul(inv(k),p2)
    
    return k,r1,r2

#returns (num_corners,2)
def return_imagepoints(image_path,grid):
    grid_x,grid_y=grid
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    
    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, (grid_x,grid_y),None)
    if(ret==False):
        print("image/corner doesnt exist")
    else:
        # termination criteria
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
        imgpt = np.ones((grid_x*grid_y,2))
        imgpt[:,0] = corners[:,0,0]
        imgpt[:,1] = corners[:,0,1]
        
        return imgpt, corners

    #returns (num_corners,2)
def return_imgGraypoints(gray,grid):
    grid_x,grid_y=grid
    # gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    
    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, (grid_x,grid_y),None)
    if(ret==False):
        print("image/corner doesnt exist")
        return ret,None, None

    else:
        # termination criteria
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
        imgpt = np.ones((grid_x*grid_y,2))
        imgpt[:,0] = corners[:,0,0]
        imgpt[:,1] = corners[:,0,1]
        
        return ret,imgpt, corners

# returns projection of a point in image plane, arg: p(3,4) and obj list len=3;
def img_projection(projection_matrix, obj_p):
    
    length = obj_p.shape[0]
    new_var = np.ones((length,4))
    new_var[:,:3] = obj_p
    
    img_p = np.matmul(projection_matrix, new_var.T)
#     img_p = img_p/img_p[-1]
    
    return img_p


#returns (num_obj,3)
def return_objpoints(grid):
    grid_x,grid_y=grid
    objp = np.zeros((grid_x*grid_y,3), np.float32)
    objp[:,:2] = np.mgrid[0:grid_x,0:grid_y].T.reshape(-1,2)

    return objp



def homo_img(img_p):
    img_homo = np.ones((3,315))
    img_homo[0,:] = img_p[:,0]
    img_homo[1,:] = img_p[:,1]
    
    return img_homo

def homo_obj3(obj_p):
    obj_homo3 = np.ones((3,315))
    obj_homo3[0,:] = obj_p[:,0]
    obj_homo3[1,:] = obj_p[:,1]
    
    return obj_homo3

def homo_obj4(obj_p):
    obj_homo4 = np.ones((4,315))
    obj_homo4[0,:] = obj_p[:,0]
    obj_homo4[1,:] = obj_p[:,1]
    obj_homo4[2,:] = obj_p[:,2]
    
    return obj_homo4    

"""
img_p=return_imagepoints()
obj_p=return_objpoints()
P=projection_matrix3(img_p,obj_p)

print(P)
"""
