from pygame import event
from pygame.constants import K_DOWN, K_F1, K_LEFT, K_RIGHT, K_UP
from Engine.BaseState import BaseState
from Engine.LevelMap import LevelMap
from Engine.DebugLog import Debug
from Engine.ResourceManager import ResourceManager
from Engine.Vector2 import Vector2
import Engine.Utilities
import pygame
import os

class Camera:
    def __init__(self, size : Vector2):
        self.position = Vector2()
        self.size = size
        self.bufferSize = 64
        self.boundary = (Vector2(), Vector2())
    
    def isWithinView(self, pos):
        buffer = Vector2(self.bufferSize, self.bufferSize)
        return Engine.Utilities.PointAABB(pos, self.position - buffer, self.position + self.size + buffer)

    def clampToBoundary(self):
        if self.position.x < self.boundary[0].x: self.position.x = self.boundary[0].x
        elif self.position.x > self.boundary[1].x: self.position.x = self.boundary[1].x
        if self.position.y < self.boundary[0].y: self.position.y = self.boundary[0].y
        if self.position.y > self.boundary[1].y: self.position.y = self.boundary[1].y

class Player:
    def __init__(self):
        self.position = Vector2(0,0)
        self.velocity = Vector2(0,0)
        self.radius = 28
        self.lives = 3
    
    def isDead(self):
        return self.lives <= 0

    def colliderData(self):
        return (self.position + Vector2(32,32), self.radius)

class State_Level(BaseState):
    statename = "Level 1"

    def __init__(self, resourcemanager : ResourceManager, window : pygame.Surface):
        super().__init__(resourcemanager, window, State_Level.statename)
        self.backgroundColor = (137, 207, 240)
        self.gravity = 9.8

        self.showDebug = False
        self.camera = Camera(Vector2.fromTuple(window.get_size()))
        
        self.player = Player()
        self.isOnGround = False

        self.levelMap = LevelMap(64) # GridSize = 64x64
        self.level = 1
            
    def __drawMap(self):
        Tiles = LevelMap.Tiles
        dimension = self.levelMap.mapDim
        map = self.levelMap.map
        for x in range(dimension[0]):
            for y in range(dimension[1]):
                value = map[y * dimension[0] + x]
                if value != 0:
                    position = Vector2(x * 64, y * 64)
                    if self.camera.isWithinView(position):
                        self.AddDrawCall(Tiles[value], position - self.camera.position)

    def __drawColliders(self):
        YELLOW_COLOR = (255,255,0)
        GREEN_COLOR = (0,255,0)
        for col in self.levelMap.colliders:
            self.AddDrawDebugRectCall(col.position - self.camera.position, col.size, GREEN_COLOR)
        for trig in self.levelMap.triggers:
            self.AddDrawDebugRectCall(trig.position - self.camera.position, trig.size, YELLOW_COLOR)

        player_collider = self.player.colliderData()
        self.AddDrawDebugCircleCall(player_collider[0] - self.camera.position, player_collider[1], GREEN_COLOR)

    def __handleCollision(self):
        BLUE_COL = (0, 0, 255)

        player_collider = self.player.colliderData()
        # Collision between player and world
        for colider in self.levelMap.colliders:
            collision = Engine.Utilities.CircleAABB(player_collider[0], player_collider[1], colider.position, colider.position + colider.size)
            if collision.hit:
                # Resolve
                resolve_dir = (player_collider[0] - collision.contactPoint).Normalized()
                resolve_dist = self.player.radius - (player_collider[0] - collision.contactPoint).Length()
                self.player.position += resolve_dir * resolve_dist

                if resolve_dir.y <= -0.7:
                    self.player.velocity.y = 0
                    self.isOnGround = True
                if resolve_dir.y >= 0.7:
                    self.player.velocity.y = 0

                # Debug draw contact point
                if self.showDebug:
                    self.AddDrawDebugPointCall(collision.contactPoint - self.camera.position, BLUE_COL)

    def __handlePhysics(self, dt: float):
        # Gravity
        self.player.velocity.y += self.gravity * dt * 2
        # Terminal velocity
        if self.player.velocity.y > 33.0:
            self.player.velocity.y = 33.0

        # Friction
        if self.player.velocity.x > 0.3:
            self.player.velocity.x -= 0.2
        elif self.player.velocity.x < -0.3:
            self.player.velocity.x += 0.2
        else:
            self.player.velocity.x = 0.0

        self.player.position += self.player.velocity * 64.0 * dt # assume 64px = 1metre

    def __handleKeyInput(self):
        # Trigger once
        # Toggle Debug
        for env in self.eventlist:
            if env.type == pygame.KEYDOWN:            
                if env.key == K_F1:
                    self.showDebug = not self.showDebug
                if env.key == K_UP and self.isOnGround:
                    self.isOnGround = False
                    self.player.velocity.y = -7.5
        #elif keypress[K_DOWN]:
        #    self.playerVel.y = 5

        # Repeated call
        keypress = pygame.key.get_pressed()
        if keypress[K_LEFT]:
            if self.player.velocity.x > -3:
                self.player.velocity.x -= 1
        elif keypress[K_RIGHT]:
            if self.player.velocity.x < 3:
                self.player.velocity.x += 1

    def __updateCamera(self):
        self.camera.position = self.player.position - Vector2(400, 400)
        self.camera.clampToBoundary()

    def Load(self):
        super().Load()
        self.levelMap.LoadMap(os.path.join("Assets", "Level", f'Level{self.level}.dat'))
        self.levelMap.GenerateColliders()
        # Init camera settings
        self.camera.boundary = (Vector2(), Vector2(self.levelMap.mapDim[0] * 64 - self.camera.size.x,
                                                   self.levelMap.mapDim[1] * 64 - self.camera.size.y))
        # Init player starting position
        self.player.position = self.levelMap.GetStartPoint_ScreenPos() - Vector2(0,64)


    def Update(self, dt):
        # Temp fix 
        if dt > 2.0/60.0:
            return

        self.__handleKeyInput()
        self.__handlePhysics(dt)
        self.__handleCollision()

        self.__drawMap()
        self.__updateCamera()
        super().AddDrawCall("Ball", self.player.position - self.camera.position)
        super().AddDrawUIText(f'Lives : {self.player.lives}')

        if self.showDebug:
            self.__drawColliders()

        super().Update(dt)
        super().Draw()
