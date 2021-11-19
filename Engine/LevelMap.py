from Engine.Vector2 import Vector2

class Box:
    def __init__(self, name, pos = None, size = None):
        self.name = name
        self.position = Vector2() if pos == None else pos
        self.size = Vector2() if size == None else size

class LevelMap:
    Tiles = ["-", "Brick", "Slope", "Ring", "Spike", "Startpoint", "Endpoint",
            "Checkpoint_Active", "Checkpoint_NotActive"]
    TilesToIndexMap = {"-" : 0, "Brick" : 1, "Slope" : 2, "Ring" : 3, 
                        "Spike" : 4, "Startpoint" : 5, "Endpoint" : 6,
                        "Checkpoint_Active" : 7, "Checkpoint_NotActive" : 8}
            
    def __init__(self, gridsize):
        self.gridsize = gridsize
        self.mapDim = ()
        self.colliders = []
        self.triggers = []
        self.map = []
        self.startpoint = Vector2()
        self.endpoint = Vector2()

    def GetStartPoint_ScreenPos(self):
        return self.startpoint * self.gridsize

    def LoadMap(self, path):
        with open(path, "r") as f:
            x, y = 0, 0
            self.map.clear()
            for line in f:
                list = line.split(',')
                x = 0
                for index in list:
                    value = int(index, 10)
                    self.map.append(value)
                    if value == LevelMap.TilesToIndexMap["Startpoint"]:
                        self.startpoint = Vector2(x,y)
                    elif value == LevelMap.TilesToIndexMap["Endpoint"]:
                        self.endpoint = Vector2(x,y)
                    x += 1
                y += 1
            self.mapDim = (x,y)
    
    def GenerateColliders(self):
        # Reset existing colliders
        self.colliders.clear()
        # Find colliders
        mymap = self.map.copy()
        dimension = self.mapDim
        for y in range(dimension[1]):
            for x in range(dimension[0]):
                value =  mymap[y * dimension[0] + x]
                if value == 0: # Nothing
                    continue
                if value == 1: # Wall
                    combinedSize = Vector2(1,1) # using normalized coord
                    # Combine horizonal colliders
                    if x < dimension[0]:
                        for i in range(x+1, dimension[0]):
                            if mymap[y * dimension[0] + (i)] == 1:
                                mymap[y * dimension[0] + (i)] = 0
                                combinedSize.x += 1
                            else:
                                break
                    # If no horizontal then check vertical and combine
                    if y < dimension[1] and combinedSize.x == 1:
                        for i in range(y+1, dimension[1]):
                            if mymap[(i) * dimension[0] + x] == 1:
                                mymap[(i) * dimension[0] + x] = 0
                                combinedSize.y += 1
                            else:
                                break
                    self.colliders.append(Box(LevelMap.Tiles[value], 
                                                Vector2(x,y) * self.gridsize, 
                                                combinedSize * self.gridsize))
                elif value == 3: # Ring
                    self.triggers.append(Box(LevelMap.Tiles[value], 
                                                Vector2(x,y) * self.gridsize + Vector2(self.gridsize/4,0), 
                                                Vector2(self.gridsize/2, self.gridsize)))
                elif value == 4: # Spike
                    self.triggers.append(Box(LevelMap.Tiles[value], 
                                                Vector2(x,y) * self.gridsize + Vector2(0,self.gridsize/2), 
                                                Vector2(self.gridsize, self.gridsize/2)))
                elif value == 5 or value == 6: # Startpoint / Endpoint
                    self.triggers.append(Box(LevelMap.Tiles[value], 
                                                Vector2(x,y) * self.gridsize, 
                                                Vector2(self.gridsize, self.gridsize)))
                elif value == 8: # Checkpoint_NotActive, ignore 6(Checkpoint_Active)
                    self.triggers.append(Box(LevelMap.Tiles[value], 
                                                Vector2(x,y) * self.gridsize, 
                                                Vector2(self.gridsize, self.gridsize)))
    