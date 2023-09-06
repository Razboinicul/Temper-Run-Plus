from typing import Iterable
import pygame as pg
from pygame.locals import *
from math import tan, floor , radians, pi, cos, atan, sin, degrees
from random import choice

# ToDo: get the actual screen size
SCREEN_WIDTH = 800         #x resolution
SCREEN_HEIGHT = 600       #y resolution

ASPECT_RATIO = SCREEN_WIDTH/SCREEN_HEIGHT

WIDTH = 64      #thinking about it, the player's size soudn't be here....
HEIGHT = 64     #remove in the future  

DARK_GRAY=pg.color.THECOLORS['darkgray']
RED=pg.color.THECOLORS['red']
ROAD_PROPS = {"length":{"short":25, "medium":50, "long":100},
              "curve":{"none":0, "easy":1,"medium":2,"hard":3},
              "hill":{"none":0, "easy":20,"medium":40,"hard":60}}

# math S.O.S
def easeIn(a,b,percent):
    return a+ (b-a)*pow(percent,2)

def easeOut(a,b,percent):
    return a + (b-a)*(1-pow(1-percent,2))

def easeInOut(a,b,percent):
    return a + (b-a)*((-cos(percent*pi)/2) + 0.5)


def project(x,y,z, cameraX, cameraY,cameraZ, depth):
    """project a 3D point to 2D screen
    returns screen x,y and the scale factor"""
    # Translate the points to be reletive to the camera
    x_distance = x - cameraX   #distance from the camera on x 
    y_distance = y - cameraY   #distance from the camera on y 
    z_distance = z - cameraZ   #distance from the camera on z 
    # get the projection factor, real distance reletive to screen distance
    factor = depth / (z_distance or 0.1)     #if the point is 0: it woudn't we shown but we will dvide in 0 so we avoid it
    x = int(SCREEN_WIDTH/2 + factor * x_distance )       #screen_width/2 - handle x fov (so camera depth is correct for x)
    y = int(SCREEN_HEIGHT/2 - factor * y_distance )     #screen_heigth/2 -this handle y fov (so depth is correct for y)
    
    return x,y, factor    

class Camera():
    def __init__(self):
        self.height = 1000    # height of camera from the road (aka player..)
        self.x = SCREEN_WIDTH//2
        self.y = self.height
        self.z = 1
        self.top_fov = 90           #camera x field of view
        self.depth =((SCREEN_WIDTH/2)/tan(radians(self.top_fov/2)))   #camera distance from screen USING WIDTH TO CALCULATE, the height could be used too with the fov y...
        
    
class Segment():
    """Part of the full , the points are the middle of the road, but 
    offsetting from them will resault in out of road -stuff too"""
    def __init__(self, index, segment_width):
        self.index = index  #segmet own list location to ease out calc
        self.point = {"1":{"x":SCREEN_WIDTH//2, "y":0,"z":0}, "2":{"x":SCREEN_WIDTH//2, "y":0,"z":0}}    #3D points
        self.screen_point = {"1":{"x":0,"y":0}, "2":{"x":0,"y":0}}          #2D points
        self.half_road_width = {"1":segment_width//2,"2":segment_width//2}  #hald the road with for each edge of seg
        self.road_width = segment_width
        self.scale = {"1":0,"2":0}  #the new segment width and height reletive to it's location
        self.sprites = pg.sprite.Group(Obsticale())
        self.curve = 0
        
    def project(self,camera, offsetX = 0)->None:
        """project the 3D points to 2D screen points"""
        
        #for point 1
        self.screen_point["1"]["x"] ,self.screen_point["1"]["y"] , self.scale["1"] = project(self.point["1"]["x"], self.point["1"]["y"], self.point["1"]["z"], camera.x - offsetX, camera.y,camera.z, camera.depth)
        self.half_road_width["1"] = int(self.scale["1"] * self.road_width/2 )
        #for point 2
        offsetX +=self.curve if offsetX else 0
        self.screen_point["2"]["x"] ,self.screen_point["2"]["y"] , self.scale["2"] = project(self.point["2"]["x"], self.point["2"]["y"], self.point["2"]["z"], camera.x - offsetX, camera.y,camera.z, camera.depth)
        self.half_road_width["2"] = int(self.scale["2"] * self.road_width/2)

    def draw(self, surface):
        """draw a polygon by the screen points, and the segments sprites"""
        polygon_points=[(self.screen_point["1"]["x"] - self.half_road_width["1"], self.screen_point["1"]["y"]),
         (self.screen_point["2"]["x"] - self.half_road_width["2"], self.screen_point["2"]["y"]), 
         (self.screen_point["2"]["x"] + self.half_road_width["2"], self.screen_point["2"]["y"]), 
         (self.screen_point["1"]["x"] + self.half_road_width["1"], self.screen_point["1"]["y"])]  
        
        if (self.index%6==0):
            color = RED
        else:
            color= DARK_GRAY 
        pg.draw.polygon(surface, color, polygon_points, 0)
        # self.sprites.update((self.screen_point["1"]["x"], self.screen_point["1"]["y"]), self.scale["1"]) #update sprite y and scale
        # self.sprites.draw(surface)
        

class Road():
    def __init__(self):
        self.segmentLength = 100   #how long is each segment 
        self.roadLength = 500       #arbitrary length... (the length in segments!)
        self.road_z_length = self.roadLength*self.segmentLength #the actual z road length
        self.road_width = 2000       #width of the road
        self.segments  = []         #segments that make up the road
        self.draw_distance = 300   #how much of the road is drawn each time

    def resetRoad(self):
        """creates the road and it's segments"""
        curve = choice(list(ROAD_PROPS["curve"].values())) * choice([1,-1])
        hill = choice(list(ROAD_PROPS["curve"].values())) * choice([1,-1])
        section = choice(list(ROAD_PROPS["length"].values()))  
        section_counter = 0
        out = False
        for n in range(0,self.roadLength):
            if out:
                self.addSegment(easeOut(0,curve, section_counter/section),easeOut(0,hill, section_counter/section))
            else:
                self.addSegment(easeIn(0,curve, section_counter/section),easeIn(0,hill, section_counter/section))
            section_counter+=1
            if section_counter == section:  #if the section is over...
                if out:
                    curve = choice(list(ROAD_PROPS["curve"].values())) * choice([1,-1])
                    hill = choice(list(ROAD_PROPS["curve"].values())) * choice([1,-1])
                    section = choice(list(ROAD_PROPS["length"].values()))
                    section_counter = 0
                else:
                    section_counter=0
                    out =True
       
    def curveRoadSegments(self, start, hold,leave ,n):
        """adds n length of segments from start and gives them curve/hill values"""
        pass
    

    def addSegment(self,curve=0,hill=0):
        seg = Segment(len(self.segments),self.road_width)
        seg.point["1"]["z"] = seg.index * self.segmentLength
        seg.point["2"]["z"] = (seg.index+1) * self.segmentLength
        seg.curve = curve   #the way of "cheating" the curves...
        seg.point["1"]["y"] = int(self.segments[seg.index-1].point["2"]["y"] if seg.index > 0 else  0)
        seg.point["2"]["y"] = int(seg.point["1"]["y"]+hill*25)
        self.segments.append(seg)
        


    def addStraightSegmet(self,start,n):
        """add straight segments to the road"""
        #first thing first we give seg a z value 
        #z location
        self.segments[n].point["1"]["z"] = n * self.segmentLength
        self.segments[n].point["2"]["z"] = (n+1) * self.segmentLength


    def draw(self,surface,camera):
        """Draw every segment of the road"""
        base_segment = self.findSegment(camera.z+camera.depth)    #first segment to apear on screen
        x = 0   # how much should the camera offset for this projection
        dx = 0  # how much it has been growing already
        camera.y = base_segment.point["1"]["y"] + camera.height
        for n in range(0,self.draw_distance):
            seg = self.segments[(base_segment.index + n)%self.roadLength]
            seg.project(camera,x)   #project point 1 and 2, give the camera offset to act as if its curving
            dx += seg.curve #the grouth rathe is now increased (segmet.project already adds the curve for point 2...)
            x += dx #the camera offset is now increased
            #to cheak if the segment is in draw distance, else don't draw it.
        for seg in reversed(self.segments):
            if seg.point["1"]["z"]>camera.z+camera.depth:  #to be seen segment needs to be after the screen
                #ToDo: clip segment whos point 2 is byond drawing distance (change it's screen y)
                #print("drawing")
                seg.draw(surface)
            

    def findSegment(self, z):
        """find segment with z location in a list of segments"""
        return self.segments[floor(z/self.segmentLength)%self.roadLength]

class GameSprite(pg.sprite.Sprite):
    """self animating sprite to inhearit animate()
    do not use this sprite, inherit from it. it is a time saver helping with shared functions of sprite"""
    def __init__(self) -> None:
        super().__init__()
        self.animation_frames = {"animationName":{"images":[],"cycleSpeed":30}}
        self.animationData = {"animation":"","frame":0,"sinceLast":0}

    def animate(self):
        if self.animationData["sinceLast"] == self.animation_frames[self.animationData["animation"]]["cycleSpeed"]: #if it's time to change animation
            self.animationData["frame"]+=1  #next frame
            if self.animationData["frame"] == len(self.animation_frames[self.animationData["animation"]]["images"]):
                self.animationData["frame"] = 0     #reset if this was the last frame
            self.animationData["sinceLast"]=0   #reset the count
            #change the image to the next 
            self.image = self.animation_frames[self.animationData["animation"]]["images"][self.animationData["frame"]]
        self.animationData["sinceLast"]+=1

    def draw(self, surface):     #ToDO: figure out why PlayerSprite cant inherit this function from Sprite
        surface.blit(self.image, self.rect)

class PlayerSprite(GameSprite):
    """player controlled charecter, provide a rect for movment"""
    def __init__(self):
        super().__init__()
        self.animation_frames = {
            "idle":{"images":[pg.transform.scale(pg.image.load(r"temp_1.png"),(WIDTH,HEIGHT)).convert_alpha()], "cycleSpeed":25},      #cycle speed means - how many updates untill next frame (diffrent for each animation)
            "running":{"images":
                [pg.transform.scale(pg.image.load(r"temp_1.png"),(WIDTH,HEIGHT)).convert_alpha(),
                pg.transform.scale(pg.image.load(r"temp_2.png"),(WIDTH,HEIGHT)).convert_alpha(),
                pg.transform.scale(pg.image.load(r"temp_3.png"),(WIDTH,HEIGHT)).convert_alpha()], "cycleSpeed":20},
            "jumping":[],
            "sliding":[]
        }
        self.animationData={"animation":"running", "frame":0,"sinceLast":0}    # animation= name of animation, frame= current frame displayed, sincelast=how many updates passed since last call
        self.image = self.animation_frames["idle"]["images"][0]
        self.rect = self.image.get_rect(topleft = (SCREEN_WIDTH/4,SCREEN_HEIGHT-HEIGHT-100))
        self.speed = 5
        

    def update(self):
        """moves the player and handles animaion"""
        pressed_keys = pg.key.get_pressed()
    
        if pressed_keys[K_LEFT]:
            self.rect.move_ip(-self.speed, 0)

        if pressed_keys[K_RIGHT]:
            self.rect.move_ip(self.speed, 0)
            
        super().animate()

class Obsticale(GameSprite):
    """obsticale needed to be dodged"""
    def __init__(self):
        super().__init__()
        self.width, self.height = 64,64
        self.animation_frames = {
            "idle":{"images":[
                pg.transform.scale(pg.image.load(r"temp_1.png"),(self.width, self.height)).convert_alpha(),
                pg.transform.scale(pg.image.load(r"temp_2.png"),(self.width, self.height)).convert_alpha(),
                pg.transform.scale(pg.image.load(r"temp_3.png"),(self.width, self.height)).convert_alpha()], "cycleSpeed":20}  
        }
        self.animationData={"animation":"idle", "frame":0,"sinceLast":0}    
        self.image = self.animation_frames["idle"]["images"][0]
        self.rect = self.image.get_rect(midbottom = (0,0))
        self.scale=0

    def update(self, midbottom , scale):
        """increase the size of self rect, image, each call.
        on max size Obsticale is killed"""
        self.scale=int(scale)
        reletive_size = (self.width*self.scale,self.height*self.scale)  #size reletive to og
        self.rect.update(midbottom,reletive_size)        #update th rect location and size
        self.image = pg.transform.scale(self.image,reletive_size)       #update image size

        #super().animate()

class Game():
    def __init__():
        pass

    def update():
        """a frame of the game"""
        pass