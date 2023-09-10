import pygame as pg
import pygame_gui as gui
import main
import sys
from pygame.locals import *
from math import tan, floor , radians, pi, cos, atan, sin, degrees, ceil
from random import choice
from time import sleep
from copy import deepcopy
from packing import set_high_score

# TODO: get the actual screen size
SCREEN_WIDTH = 800         #x resolution
SCREEN_HEIGHT = 600       #y resolution
PAUSED = False           #Check if game is paused
GAME_OVER = False         #Check if game is over
SCORE = 0                #Score

ASPECT_RATIO = SCREEN_WIDTH/SCREEN_HEIGHT



PLAYER_SPRITE_RUNNING = [(158, 85,327,779),(806,121,348,764),(1436,165,358,767),
 (2093,186,359,778),(2744,169,364,765),(3412,126,341,748),(4051,82,342,755)]

# road properties to help with geometry
ROAD_PROPS = {"length":{"short":25, "medium":50, "long":100},
              "curve":{"none":0, "easy":1,"medium":2,"hard":3},
              "hill":{"none":0, "easy":20,"medium":40,"hard":60}}

# image load helper
def get_image(surf, x, y, width, height):  # gets sprite  x,y width, height,
    return pg.Surface.subsurface(surf, (x, y, width, height))

def getImages(surf, sprites_in_row, sprites_in_column,transformx=300, transformy=300, reverse_animation = False):  # returns with list of sprites
    sprites = []
    sprite_width = surf.get_width()//sprites_in_row
    sprite_height = floor(surf.get_height()/ sprites_in_column)
    for i in range (0,sprites_in_row):
        for j in range(0,sprites_in_column):
            sub = get_image(surf,i*sprite_width,j*sprite_height,sprite_width,sprite_height)
            sprites.append(pg.transform.scale(sub,(transformx,transformy)))
    return (list(reversed(sprites)) if reverse_animation else sprites)

# math S.O.S TODO: cos / sin functions will work much metter i rekon (hills are meh)
def easeIn(a,b,percent):
    return a+ (b-a)*pow(percent,2)

def easeOut(a,b,percent):
    return a + (b-a)*(1-pow(1-percent,2))

def easeInOut(a,b,percent):
    return a + (b-a)*((-cos(percent*pi)/2) + 0.5)

def rotate2DPoint(x,y, angle):
    """rotate 2d point in an angle"""
    #remember the angle is in radians !!!
    return cos(angle)*x-sin(angle)*y, sin(angle)*x+cos(angle)*y

def rotate3Dpoint(x,y,z,angleX=0,angleY=0, angleZ = 0):
    """rotate a 3D point in an angle this allows for rotation on every axis"""
    # to rotate a 3d point we need to rotate each of its 2d aspects
    y,z = rotate2DPoint(y,z,angleX)
    x,z = rotate2DPoint(x,z,angleY) 
    x,y = rotate2DPoint(x,y,angleZ)

    return x,y,z

def project(x,y,z, cameraX, cameraY,cameraZ, depth, angleX=0, angleY=0,angleZ=0):
    """project a 3D point to 2D screen
    returns screen x,y and the scale factor"""
    # Translate the points to be reletive to the camera
    x_distance = x - cameraX   #distance from the camera on x 
    y_distance = y - cameraY   #distance from the camera on y 
    z_distance = z - cameraZ   #distance from the camera on z 
    #rotation 
    x_distance, y_distance,z_distance  = rotate3Dpoint(x_distance,y_distance,z_distance,angleY = angleY, angleX=angleX, angleZ=angleZ)
    # get the projection factor, real distance reletive to screen distance
    factor = depth / (z_distance or 0.1)     #if the point is 0: it woudn't we shown but we will dvide in 0 so we avoid it
    x = int(SCREEN_WIDTH/2 + factor * x_distance )       #screen_width/2 - handle x fov (so camera depth is correct for x)
    y = int(SCREEN_HEIGHT/2 - factor * y_distance )     #screen_heigth/2 -this handle y fov (so depth is correct for y)
    
    return x,y, factor    

class Camera():
    def __init__(self):
        self.height = 1500    # height of camera from the road (aka player..)
        self.x = SCREEN_WIDTH//2
        self.y = self.height
        self.z = 0
        self.top_fov = 90           #camera x field of view
        self.side_fov = 2*atan(tan(self.top_fov/2)* ASPECT_RATIO)   
        self.depth =((SCREEN_WIDTH/2)/tan(radians(self.top_fov/2)))   #camera distance from screen USING WIDTH TO CALCULATE, the height could be used too with the fov y...
        self.angleX = 0     
        self.angleY = 0      
        self.angleZ = 0     
        self.max_angle = 30

    def turn(self , angleX=0 , angleY = 0, angleZ = 0):
        """gets angle in degrees and 'turn' the camera at that angle
        left/down -angle right/up +angle """
        # useful for extra-effects, and debugging
        if angleX and -self.max_angle<=degrees(self.angleX)+angleX <=self.max_angle :
            angleX =radians(angleX)
            if angleX + self.angleX <-2*pi:
                self.angleX += angleX +2*pi
            elif angleX + self.angleX >2*pi:
                self.angleX += angleX -2*pi
            else:
                self.angleX += angleX 

        if angleY and  -self.max_angle<=degrees(self.angleY)+angleY<=self.max_angle:
            angleY =radians(angleY)
            if angleY + self.angleY <-2*pi:
                self.angleY += angleY +2*pi
            elif angleY + self.angleY >2*pi:
                self.angleY += angleY -2*pi
            else:
                self.angleY += angleY
                
        if angleZ and  -self.max_angle<=degrees(self.angleZ) + angleZ <=self.max_angle:
            angleZ =radians(angleZ)
            if angleZ + self.angleZ <-2*pi:
                self.angleZ += angleZ +2*pi
            elif angleZ + self.angleZ >2*pi:
                self.angleZ += angleZ -2*pi
            else:
                self.angleZ += angleZ

    def setY(self, y ):
        """keeps the camera above a point"""
        self.y = y + self.height

    def setZ(self,z):
        """move camera z"""
        self.z = z

class Segment():
    """Part of the full we project and draw a polygon from it"""
    def __init__(self, index, segment_width):
        self.index = index  # segmet own list location to ease out calc
        self.point = {"1":{"x":SCREEN_WIDTH//2, "y":0,"z":0}, "2":{"x":SCREEN_WIDTH//2, "y":0,"z":0}}    #3D points
        self.screen_point = {"1":{"x":0,"y":0}, "2":{"x":0,"y":0}}          #2D points
        self.half_road_width = {"1":segment_width//2,"2":segment_width//2}  #half the road with for each edge of seg
        self.road_width = segment_width
        self.scale = {"1":0,"2":0}  #the new segment width and height reletive to it's location
        self.sprites = []
        self.curve = 0
        # This is the z location we actually project, stated by the caller to fit the camera
        self.projected_z = {"1":0,"2":0}
        self.surf =  pg.color.THECOLORS["azure3"]
        


    def project(self,camera,  offsetX2 = 0)->None:
        """project the 3D points to 2D screen points"""
        # since im using a virtual camera when i project, only dx is needed
        #for point 1
        self.screen_point["1"]["x"] ,self.screen_point["1"]["y"] , self.scale["1"] = project(self.point["1"]["x"], self.point["1"]["y"], self.projected_z["1"],
         camera.x , camera.y,camera.z, camera.depth , angleY = camera.angleY, angleX=camera.angleX, angleZ=camera.angleZ)
        self.half_road_width["1"] = int(self.scale["1"] * self.road_width/2 )
        #for point 2

        self.screen_point["2"]["x"] ,self.screen_point["2"]["y"] , self.scale["2"] = project(self.point["2"]["x"], self.point["2"]["y"], self.projected_z["2"], 
         camera.x - offsetX2, camera.y,camera.z, camera.depth , angleY = camera.angleY, angleX=camera.angleX, angleZ=camera.angleZ)
        self.half_road_width["2"] = int(self.scale["2"] * self.road_width/2)
        
    def draw(self, surface):
        """draw a polygon by the screen points, and the segments sprites"""
        polygon_points=[(self.screen_point["1"]["x"] - self.half_road_width["1"], self.screen_point["1"]["y"]),
         (self.screen_point["2"]["x"] - self.half_road_width["2"], self.screen_point["2"]["y"]), 
         (self.screen_point["2"]["x"] + self.half_road_width["2"], self.screen_point["2"]["y"]), 
         (self.screen_point["1"]["x"] + self.half_road_width["1"], self.screen_point["1"]["y"])]  
        
        
       
        
        # see if the polygon apear on screen else dont bother drawing it 
        draw = False 
         #update sprite y and scale
        for point in polygon_points:
            if 0<point[0]< SCREEN_WIDTH and 0< point[1]< SCREEN_HEIGHT:
                draw =True
                break
        
        if draw:
            pg.draw.polygon(surface, self.surf, polygon_points, 0)
            for sprite in self.sprites:
                sprite.update()
                sprite.draw(surface,(self.screen_point["1"]["x"], self.screen_point["1"]["y"]), self.scale["1"])

class Road():
    def __init__(self, what_is_closure = 200):
        self.segmentLength = 100   #how long is each segment 
        self.roadLength = 500       #arbitrary length... (the length in segments!)
        self.road_z_length = self.roadLength*self.segmentLength #the actual z road length
        self.road_width = 2000       #width of the road
        self.segments  = []         #segments that make up the road
        self.draw_distance = 300   #how much of the road is drawn each time (in segments)
        self.obs_offsets = [-int(self.road_width*0.25),0,int(self.road_width*0.25)]
        self.closure = int(what_is_closure/self.segmentLength) # 500 is the number of pixels from a segment, a sprite is considered close

        # road builder helpers: #
        self.curve = choice(list(ROAD_PROPS["curve"].values())) * choice([1,-1])
        self.hill = choice(list(ROAD_PROPS["curve"].values())) * choice([1,-1])
        self.section = choice(list(ROAD_PROPS["length"].values()))  
        self.section_counter = 0
        self.out = False
        # for fun
        self.rumbleLength = 6 # how many segments make up a part 
        self.colorIndex = pg.color.THECOLORS['azure3']
        self.rumbleCounter = 0
        #to help with updating the passed segments:
        self.last_base_index = 0
        self.resetRoad() # Time to make a road!

    def incRoadProps(self):
        """call this function after update or addition of the last road segment"""
        self.section_counter+=1
        if self.section_counter == self.section:  #if the section is over...
            if self.out:
                self.curve = choice(list(ROAD_PROPS["curve"].values())) * choice([1,-1])
                self.hill = choice(list(ROAD_PROPS["curve"].values())) * choice([1,-1])
                self.section = choice(list(ROAD_PROPS["length"].values()))
                self.section_counter = 0
            else:
                self.section_counter=0
                self.out =True

    def resetRoad(self):
        """creates the road and it's segments"""
        self.segments = []
        for n in range(0,self.roadLength):
            if self.out:
                self.addSegment(easeIn(0,self.curve, self.section_counter/self.section),easeIn(0,self.hill, self.section_counter/self.section))
            else:
                self.addSegment(easeIn(0,self.curve, self.section_counter/self.section),easeOut(self.hill,0, self.section_counter/self.section))
            #always call this after using a road prop
            self.incRoadProps()

    def generateSprites(self,seg):
        seg.sprites = []
        if seg.index%70 == 0:
            # TODO: add actual randomizer to the sprites generator
            # TODO: add collectables!
            obs = Obsticale()
            obs.road_offset = choice(self.obs_offsets)
            seg.sprites.append(obs)

    def updateSegment(self,seg):
        """change the segment's curve and hilll values"""
        if self.out:
            seg.curve = easeOut(0,self.curve, self.section_counter/self.section)
            seg.point["1"]["y"] = int(self.segments[(seg.index-1)% len(self.segments)].point["2"]["y"])
            seg.point["2"]["y"] = int(seg.point["1"]["y"]+easeOut(0,self.hill, self.section_counter/self.section)*20)  #20 is arbitarty modifier
        else:
            seg.curve = easeIn(0,self.curve, self.section_counter/self.section)
            seg.point["1"]["y"] = int(self.segments[(seg.index-1)% len(self.segments)].point["2"]["y"])
            seg.point["2"]["y"] = int(seg.point["1"]["y"]+easeIn(self.hill,0, self.section_counter/self.section)*20)  #20 is arbitarty modifier
        #always call this after using a road prop
        self.generateSprites(seg)
        self.incRoadProps()
        
    
    def addSegment(self,curve=0,hill=0):
        seg = Segment(len(self.segments),self.road_width)
        seg.point["1"]["z"] = seg.index * self.segmentLength
        seg.point["2"]["z"] = (seg.index+1) * self.segmentLength
        seg.curve = curve    # faking curves, x position of segment is the same...
        seg.point["1"]["y"] = int(self.segments[seg.index-1].point["2"]["y"] if seg.index > 0 else  0)
        seg.point["2"]["y"] = int(seg.point["1"]["y"]+hill*20)  #20 is arbitarty modifier TODO: get an actual modifier
        
        color = self.colorIndex
        
        self.rumbleCounter+=1
        if self.rumbleCounter == self.rumbleLength:
            self.rumbleCounter = 1
            self.colorIndex = choice([pg.color.THECOLORS['azure3'],pg.color.THECOLORS['coral'],pg.color.THECOLORS['deeppink2']
,pg.color.THECOLORS['royalblue3'], pg.color.THECOLORS["yellow1"], pg.color.THECOLORS["red1"],pg.color.THECOLORS["aquamarine"]])
        seg.surf = color
        self.generateSprites(seg)
        self.segments.append(seg)

    def update(self,camera, player_seg = None):
        """Update every segment of the road, returns sprites that are close to the player 
        (both obstacles and collectables) and the segment with the screen y cordinates """
        base_segment = self.findSegment(camera.z)    #first segment to apear on screen
        virtual_camera = deepcopy(camera)
        virtual_camera.z = 0
        #x = 0   # how much should the camera offset for this projection
        dx = base_segment.curve  # how much it has been growing already
        # TODO: It is possible to rid of dx if the segmnet curve value is already accumulated...
        close_sprites = []
        for n in range(0,len(self.segments)):
            seg = self.segments[(base_segment.index + n)%len(self.segments)]    #run on 300 close sefments
            
            seg.projected_z["1"]  = n*self.segmentLength
            seg.projected_z["2"]  = (n+1)*self.segmentLength
            seg.project(virtual_camera, offsetX2 = dx)   #project point 1 and 2, give the camera offset to act as if its curving
            
            dx += seg.curve #the grouth rathe is now increased (segmet.project already adds the curve for point 2...)
            virtual_camera.x -= dx #the camera offset is now increased
            
            if player_seg and seg.index < player_seg.index + self.closure:   #if the segment is close...
                close_sprites += seg.sprites
            
            # i believe this conditioning is lacking... but it works for now
            if  base_segment.index >= self.last_base_index and base_segment.index>seg.index>=self.last_base_index:
                # We update all the segmets the camera traveled 
                self.updateSegment(seg)
            elif base_segment.index < self.last_base_index and len(self.segments)>seg.index>=self.last_base_index:
                self.updateSegment(seg)
                
                
        self.last_base_index = base_segment.index
        return close_sprites  #,(playerSeg if playerSeg else base_segment)

    def draw(self, surface , camera):
        """Draw the road from draw distance to base segment"""
        base_segment = self.findSegment(camera.z+camera.depth)    #first segment to apear on screen
        for n in range(self.draw_distance,0,-1): #painter's....
            # TODO: fix the sprites that apear floating and blinking...
            # TODO: clip segments whos point 2 is byond drawing distance (change it's screen y)
            seg = self.segments[(base_segment.index + n)%len(self.segments)]
            seg.draw(surface)
        
    def findSegment(self, z):
        """find segment with z location in a list of segments"""
        return self.segments[floor(z/self.segmentLength)%self.roadLength] 

class GameSprite(pg.sprite.Sprite):
    """self animating sprite to inhearit animate()
    do not use this sprite, inherit from it. it is a time saver helping with shared functions of sprite"""
    def __init__(self) -> None:
        super().__init__()
        self.animation_frames = {"animationName":{"images":[],"cycleSpeed":30}} # provided by child...
        self.animationData = {"animation":"","frame":0,"sinceLast":0} # provided by child...
        self.current_image = None   # provided by child...
        

    def animate(self):
        """update the animation dict, the caller needs to set his image to current_image"""
        if self.animationData["sinceLast"] == self.animation_frames[self.animationData["animation"]]["cycleSpeed"]: #if it's time to change animation
            self.animationData["frame"]+=1  #next frame
            if self.animationData["frame"] == len(self.animation_frames[self.animationData["animation"]]["images"]):
                self.animationData["frame"] = 0     #reset if this was the last frame
            self.animationData["sinceLast"]=0   #reset the count
            #change the image to the next 
            self.current_image = self.animation_frames[self.animationData["animation"]]["images"][self.animationData["frame"]]
        self.animationData["sinceLast"]+=1
        # remember the animate set a "current" image and noth the real image (the caller needs to change the image) 

    def draw(self, surface):     # TODO: figure out why PlayerSprite cant inherit this function from Sprite
        surface.blit(self.image, self.rect)
    
class PlayerSprite(GameSprite):
    """player controlled charecter, provide a rect for movment"""
    def __init__(self):
        super().__init__()
        self.width = 100
        self.height = 100

        self.animation_frames = {
            "idle":{"images":[], "cycleSpeed":25},      #cycle speed means - how many updates untill next frame (diffrent for each animation)
            "running":{"images": getImages(pg.image.load(r"character_run.png"),12,1,transformx=100,transformy=200,reverse_animation=True), "cycleSpeed":2},
            "jumping":[],
            "sliding":[]
        }
        self.animationData={"animation":"running", "frame":0,"sinceLast":0}    # animation= name of animation, frame= current frame displayed, sincelast=how many updates passed since last call
        self.image =  self.current_image = self.animation_frames["running"]["images"][0]  #the image we blit
        self.rect = self.image.get_bounding_rect()
        self.rect.topleft = (SCREEN_WIDTH/2,SCREEN_HEIGHT-self.height-10)
        self.Xspeed = 25
        self.Zspeed = 100   # !IMPORTANT: speed above 100 
        self.position = 0 # distance from the camera
        self.z = 0 
        self.offsetX = 0        # if between (-1) right to 1 left the player is in the segment's polygon
        self.max_offsetX = 0.9  # to avoid being too close to the edge
      
    def detectColision(self, obstacles):
        """cheak if any sprite collided with the player, returns False on no colision"""
        # Simple colission for now... (works since I defined "closure, only close sprites will be cheaked.")
        # TODO: colliosion is obs bot line is under 80% of the player rect
        # TODO: handle collision with the sprites
        collision = {}
        for obstacle in obstacles:
            collision[obstacle] = self.rect.colliderect(obstacle.rect)
        return collision

    def update(self,seg):
        """handles animaion, and set rect x and y to fit the new segment"""
        # no need to cheak max offset since the center x is based on the segment %..
        self.rect.centerx = seg.screen_point["1"]["x"] - int(seg.half_road_width["1"]*self.offsetX)
        self.setZ(seg.point["1"]["z"])
        self.setY(seg.screen_point["1"]["y"])
        
        super().animate()
        self.image = self.current_image
    

    def moveX(self, seg, direction = 1):   
        """move sprite left and right with right being +1 and left (-1)"""
        # TODO: move her equally on the eft and right
        new_offsetX = (seg.screen_point["1"]["x"]-(self.rect.centerx + (self.Xspeed * direction)))/seg.half_road_width["1"]
        # TODO: add centrifugal force
        if self.max_offsetX>new_offsetX>-self.max_offsetX:
            self.rect.x += self.Xspeed * direction 
            self.offsetX = new_offsetX
        else:
            self.offsetX = self.max_offsetX *-1 if self.offsetX<0 else self.max_offsetX # the (-1) is not intended and dosen't make sense
    
    def moveZ(self, direction = 1): #back or foward..?
        self.z += self.Zspeed * direction

    def setY(self,y):
        self.rect.bottom = y
    
    def setZ(self,z):
         self.z = z      

    def getCameraZ(self):
        return self.z-self.position

    def draw(self,surface):
        super().draw(surface)

class Obsticale(GameSprite):
    """obsticale needed to be dodged"""
    def __init__(self):
        super().__init__()
        self.height = 500
        self.width = 500
        self.animation_frames = {
            "idle":{"images":[
                pg.transform.scale(pg.image.load(r"spikes_1.png"),(self.width, self.height)).convert_alpha(),
                pg.transform.scale(pg.image.load(r"spikes_2.png"),(self.width, self.height)).convert_alpha()], "cycleSpeed":35}  
        }
        self.animationData={"animation":"idle", "frame":0,"sinceLast":0}    
        self.image  = self.current_image = self.animation_frames["idle"]["images"][0]
        self.rect = self.image.get_rect(midbottom = (0,0))
        self.road_offset = 0    # x location reletive to segment 
 
    def draw(self, surface , midbottom , scale):
        self.rect.midbottom = (midbottom[0]+int(self.road_offset*scale), midbottom[1])  #need to scale the offset too!
        self.rect.width = int(scale *self.width)
        self.rect.height = int(scale *self.height)
        # we scale the ORIGINAL image of the animation and put it in the image,not a rescale!
        self.image = pg.transform.scale(self.current_image, 
         (self.rect.width, self.rect.height))
        super().draw(surface)

    def update(self):
        """increase the size of self rect, image, each call.
        on max size Obsticale is killed"""
        super().animate()

class ParallaxBackground(GameSprite):
    def __init__(self):
        self.animation_frames = {
            "idle":{"images":[
                pg.transform.scale(pg.image.load(r"space.png"),(SCREEN_WIDTH*5//4, SCREEN_HEIGHT*5//4)).convert_alpha()], "cycleSpeed":35}  
        }
        self.animationData={"animation":"idle", "frame":0,"sinceLast":0}    
        self.image  = self.current_image = self.animation_frames["idle"]["images"][0]
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.speed = 1.5
       # TODO: add backround sprits that moove and disapear when getting too far from screen

    def update(self, playerSeg ):
        super().animate()
        self.image = self.current_image
        dx =  int(playerSeg.curve*self.speed)
        dy = 1 if playerSeg.point["2"]["y"]-playerSeg.point["1"]["y"] >0  else -1
        
        # repeat the image:
        width, height = self.image.get_size()
        copySurf = self.image.copy()
        if dx < 0:
            self.image.blit(copySurf, (width + dx, 0), (0, 0, -dx, height))
        else:
            self.image.blit(copySurf, (0, 0), (width - dx, 0,dx, height))

        if dy < 0:
            self.image.blit(copySurf, (0, height + dy), (0, 0, width, -dy))
        else:
            self.image.blit(copySurf, (0, 0), (0, height - dy, width, dy))

        self.image.blit(copySurf, (dx, dy))
        

class Game():
    def __init__(self):
        global SCORE
        SCORE = 0
        self.camera = Camera()
        self.road = Road(what_is_closure=400/8)  # Road is reset At it's init..(closure is what we define)
        self.road.update(self.camera)
        self.player = PlayerSprite()
        self.background =  ParallaxBackground()
        self.score = 0
        self.game_over = False        
        self.player.position =  2500    # this has to divide by the length of each segment
        self.player.z = self.camera.z + self.player.position #position..
       

    def update(self, window):
        """a frame of the game"""
        global GAME_OVER, SCORE
        # the player has y,z, and % x of the segment his y is on, 
        # and the camera folows player z, and y 
        # TODO: when the camera auto scroll, player z will be set by the players seg...
        # PLAYER SPEED ALWAYS ABOVE SEGMENT LENGTH!, since I cant be asked to deal with percentages.
        # also means NO SLOWING DOWNN WHOOOO
        GAME_OVER = False
        keys = pg.key.get_pressed()
        # Camera Move
        self.player.moveZ()
        #if keys[K_UP]:
        #     self.player.moveZ()
        #if keys[K_DOWN]:
        #     self.player.moveZ(direction = -1)

        # after giving the player a new z position, we want to get the segment he is on
        player_seg = self.road.findSegment(self.player.z)
        # We need that segment to prevent the player from leaving the road...
        if keys[K_LEFT]:
            self.player.moveX(player_seg, -1)
        if keys[K_RIGHT]:
            self.player.moveX(player_seg)

        # x is my text key!

        if keys[K_x]:   
            print(player_seg.index)
            

        # Camera Turn
        if keys[K_d]:
            self.camera.turn(angleY = 5)
        if keys[K_a]:
            self.camera.turn(angleY = -5)
        if keys[K_w]:
            self.camera.turn(angleX = 5)
        if keys[K_s]:
            self.camera.turn(angleX = -5)
        if keys[K_ESCAPE] or keys[K_p]:
            paused()

        self.camera.setY(player_seg.point["1"]["y"])
        self.camera.setZ(self.player.getCameraZ()) # set camera to follow the player...

        # we want to update everything with the new camera position!
        closeSprits = self.road.update(self.camera, player_seg) # TODO:
        self.player.update(player_seg)
        # TODO: add paralax scroll

        # nothing should come between the updates and the draw...
        
        self.background.update(player_seg)
        self.background.draw(window)
        self.road.draw(window, self.camera)
        self.player.draw(window)

        # TODO: handle collectables collision
        # TODO: make the close sprites overlap with out sprite ... by drawing the player between the segments
        # Cheak if the game ended this frame....#
        collision = self.player.detectColision(closeSprits)
        for i in collision.keys():
            if type(i) == Obsticale and collision[i]:
                SCORE = int(self.score/30)
                self.game_over = True
                game_over()
            else:
                self.score+=1
                SCORE = int(self.score/30)

        return SCORE # returns if game ended and the results

def paused():
    is_running = True
    """This is the Game's main function"""
    pg.init()
    pg.display.set_caption('Temper Run')
    window_surface = pg.display.set_mode((800, 600))
    
    window_surface.fill(pg.Color('#87CEEB'))
    manager = gui.UIManager((800, 600))
    clock = pg.time.Clock()
    
    bg = pg.image.load("bg.png").convert_alpha()
    pg.font.init() # you have to call this at the start, 
                   # if you want to use this module.
    TitleFont = pg.font.SysFont('Arial', 80)
    TitleText = TitleFont.render('Pause', False, (255, 255, 255))
    
    resume_button = gui.elements.UIButton(relative_rect=pg.Rect((290, 160), (250, 50)),
                                             text='Resume',
                                             manager=manager)

    main_menu_button = gui.elements.UIButton(relative_rect=pg.Rect((290, 230), (250, 50)),
                                             text='Go to Main Menu',
                                             manager=manager)
    
    exit_button = gui.elements.UIButton(relative_rect=pg.Rect((290, 300), (250, 50)),
                                             text='Exit',
                                             manager=manager)
    while is_running:
        time_delta = clock.tick(30)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                is_running = False
            if event.type == pg.USEREVENT:
                if event.user_type == gui.UI_BUTTON_PRESSED:
                    if event.ui_element == resume_button:
                        print('OK')
                        return
                if event.user_type == gui.UI_BUTTON_PRESSED:
                    if event.ui_element == main_menu_button:
                        print('OK')
                        main.main().game.game_over = True
                        return
                if event.user_type == gui.UI_BUTTON_PRESSED:
                    if event.ui_element == exit_button:
                        is_running = False
                        sys.exit()
                window_surface.blit(bg, (0, 0))

            manager.process_events(event)
        manager.update(time_delta)
        
        manager.draw_ui(window_surface)
        window_surface.blit(TitleText,(325, 25))
        pg.display.update()
    
    sys.exit()

def about():
    is_running = True
    """This is the Game's main function"""
    pg.init()
    pg.display.set_caption('Temper Run')
    window_surface = pg.display.set_mode((800, 600))
    
    window_surface.fill(pg.Color('#87CEEB'))
    manager = gui.UIManager((800, 600))
    clock = pg.time.Clock()
    
    bg = pg.image.load("bg.png").convert_alpha()
    pg.font.init() # you have to call this at the start, 
                   # if you want to use this module.
    TitleFont = pg.font.SysFont('Arial', 80)
    TitleText = TitleFont.render('About', False, (255, 255, 255))
    TextFont = pg.font.SysFont('Arial', 25)
    AboutText = TextFont.render('Lorem ipsum dolor sit amet, consectetur adipiscing elit. \nPellentesque a sem odio. Donec nec accumsan erat.  \nSed in rhoncus mauris. Proin eleifend velit at ex pulvinar pulvinar. \nNunc sit amet elit sodales, hendrerit nunc ac, maximus nisl. Donec ac sodales nibh. \nNunc viverra enim eget est blandit tincidunt. Donec semper.', False, (255, 255, 255))

    main_menu_button = gui.elements.UIButton(relative_rect=pg.Rect((290, 500), (250, 50)),
                                             text='Back',
                                             manager=manager)
    while is_running:
        time_delta = clock.tick(30)
        window_surface.blit(bg, (0, 0))
        for event in pg.event.get():
            if event.type == pg.QUIT:
                is_running = False
            if event.type == pg.USEREVENT:
                if event.user_type == gui.UI_BUTTON_PRESSED:
                    if event.ui_element == main_menu_button:
                        print('OK')
                        return

            manager.process_events(event)
        manager.update(time_delta)
        
        manager.draw_ui(window_surface)
        window_surface.blit(TitleText,(325, 25))
        window_surface.blit(AboutText,(10, 125))
        pg.display.update()
    
    sys.exit()

def game_over():
    """This is the Game's main function"""
    global PAUSED, SCORE
    is_running = True
    pg.font.init() # you have to call this at the start, 
                   # if you want to use this module.
    TitleFont = pg.font.SysFont('Arial', 80)
    TitleText = TitleFont.render('Game Over', False, (255, 255, 255))
    ScoreFont = pg.font.SysFont('Arial', 35)
    ScoreText = ScoreFont.render(f'Score: {SCORE}', False, (255, 255, 255))
    VerFont = pg.font.SysFont('Calibri', 40)
    if SCORE > main.high_score:
        new_high_score = True
        main.high_score = SCORE
        set_high_score(SCORE)
        HighScoreText = ScoreFont.render(f'New High Score: {main.high_score}', False, (255, 0, 0))
    else:
        new_high_score = False
        HighScoreText = ScoreFont.render(f'High Score: {main.high_score}', False, (255, 255, 255))
    pg.init()
    pg.display.set_caption('Temper Run')
    window_surface = pg.display.set_mode((800, 600))
    
    window_surface.fill(pg.Color('#87CEEB'))
    manager = gui.UIManager((800, 600))
    clock = pg.time.Clock()
    
    bg = pg.image.load("bg.png").convert_alpha()
    
    play_button = gui.elements.UIButton(relative_rect=pg.Rect((290, 160+50), (250, 50)),
                                             text='Play Again',
                                             manager=manager)

    main_menu_button = gui.elements.UIButton(relative_rect=pg.Rect((290, 230+50), (250, 50)),
                                             text='Go to Main Menu',
                                             manager=manager)
    
    exit_button = gui.elements.UIButton(relative_rect=pg.Rect((290, 300+50), (250, 50)),
                                             text='Exit',
                                             manager=manager)
    
    # only 1 game object is needed!
    game = Game()
    
    #stopping this game just set this to false
    game_active = False
    paused = False
    while is_running:
        time_delta = clock.tick(30)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                is_running = False
            if event.type == pg.USEREVENT:
                if event.user_type == gui.UI_BUTTON_PRESSED:
                    if event.ui_element == play_button:
                        game_active = True
                        SCORE = 0
                if event.user_type == gui.UI_BUTTON_PRESSED:
                    if event.ui_element == main_menu_button:
                        print('OK')
                        main.main().game.game_over = True
                        return
                if event.user_type == gui.UI_BUTTON_PRESSED:
                    if event.ui_element == exit_button:
                        is_running = False 
                
            manager.process_events(event)
        manager.update(time_delta)
        
        if game_active:
            #if game ongoing update it
            if PAUSED:
                paused()
                PAUSED = False
            #resume_button.hide()
            #resume_button.disable()
            play_button.disable()
            exit_button.disable()
            main_menu_button.disable()
            main_menu_button.hide()
            play_button.hide()
            exit_button.hide()
            ScoreText = VerFont.render(f'Score: {SCORE}', False, (255, 255, 255))
            game.update(window_surface)
            window_surface.blit(ScoreText,(0, 0))
        else:
            window_surface.blit(bg, (0, 0))
            window_surface.blit(TitleText,(250, 25))
            window_surface.blit(ScoreText,(365, 115))
            if new_high_score:
                window_surface.blit(HighScoreText,(295, 155))
            else:
                window_surface.blit(HighScoreText,(330, 155))
        
        manager.draw_ui(window_surface)
        pg.display.update()
    
    sys.exit()
        


if __name__ == "__main__":
    game_over()