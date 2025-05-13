from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import sys

# Camera settings
camera_pos = [0, -400, 200]
camera_angle = 45
fovY = 60
GRID_SIZE = 600
TERRAIN_HEIGHT = 50

# Game state
score = 0
currency = 1000  # Starting currency for the player
animals = []
poachers = []
trees = []
rocks = []
water_areas = []
game_time = 0.0  # Add game time variable for animations

class Habitat:
    def __init__(self, name, base_color, highlight_color, position=(0,0,0), size=200):
        self.name = name
        self.base_color = base_color      # Primary terrain color
        self.highlight_color = highlight_color  # Secondary terrain color
        self.position = position          # (x, y, z) position
        self.size = size                  # Size of the habitat area

# Natural habitat colors (greens, browns, blues) and their positions
habitats = [
    Habitat("Savannah", 
           (0.6, 0.7, 0.4), (0.8, 0.7, 0.3),
           (-GRID_SIZE/2, GRID_SIZE/2, 0)),  # Top-left quadrant
    Habitat("Rainforest", 
           (0.3, 0.6, 0.4), (0.2, 0.5, 0.3),
           (GRID_SIZE/2, GRID_SIZE/2, 0)),   # Top-right quadrant
    Habitat("Arctic", 
           (0.95, 0.95, 0.98), (0.85, 0.9, 0.95),
           (GRID_SIZE/2, -GRID_SIZE/2, 0)),  # Bottom-right quadrant
    Habitat("Wetlands", 
           (0.4, 0.6, 0.5), (0.3, 0.5, 0.7),
           (-GRID_SIZE/2, -GRID_SIZE/2, 0))  # Bottom-left quadrant
]

def init_environment():
    """Initialize the 3D zoo environment with terrain features"""
    global animals, trees, rocks, water_areas
    
    # Create terrain features
    for i in range(50):
        trees.append({
            'x': random.uniform(-GRID_SIZE, GRID_SIZE),
            'y': random.uniform(-GRID_SIZE, GRID_SIZE),
            'size': random.uniform(0.5, 1.5),
            'type': random.choice(["palm", "pine", "oak"])
        })
        
    for i in range(30):
        rocks.append({
            'x': random.uniform(-GRID_SIZE, GRID_SIZE),
            'y': random.uniform(-GRID_SIZE, GRID_SIZE),
            'size': random.uniform(0.3, 1.2),
            'color': (0.5, 0.5, 0.5)  # Gray rocks
        })
    
    # Create water areas
    for i in range(5):
        water_areas.append({
            'x': random.uniform(-GRID_SIZE/2, GRID_SIZE/2),
            'y': random.uniform(-GRID_SIZE/2, GRID_SIZE/2),
            'radius': random.uniform(50, 150),
            'color': (0.3, 0.5, 0.8, 0.6)  # Blue water with transparency
        })
    
    # Place animals with proper structure
    animals = [
        {
            'type': 'lion',
            'position': (-200, 150, 0),
            'health': 100,
            'happiness': 100,
            'color': (0.8, 0.6, 0.2),
            'size': 1.0,
            'angle': 0
        },
        {
            'type': 'elephant',
            'position': (100, -100, 0),
            'health': 100,
            'happiness': 100,
            'color': (0.7, 0.7, 0.7),
            'size': 1.5,
            'angle': 0
        },
        {
            'type': 'panda',
            'position': (250, 250, 0),
            'health': 100,
            'happiness': 100,
            'color': (1.0, 1.0, 1.0),
            'size': 1.2,
            'angle': 0
        },
        {
            'type': 'penguin',
            'position': (-150, -250, 0),
            'health': 100,
            'happiness': 100,
            'color': (0.3, 0.3, 0.3),
            'size': 0.8,
            'angle': 0
        }
    ]

def draw_terrain():
    """Draw the 3D terrain with natural colors"""
    glPushMatrix()
    
    # Draw base terrain with elevation and color variation
    glBegin(GL_QUADS)
    for x in range(-GRID_SIZE, GRID_SIZE, 20):
        for y in range(-GRID_SIZE, GRID_SIZE, 20):
            z = TERRAIN_HEIGHT * math.sin(x/100) * math.cos(y/100)
            
            # Determine habitat and blend colors
            if x < 0 and y > 0:  # Savannah
                base_color = habitats[0].base_color
                highlight = habitats[0].highlight_color
            elif x > 0 and y > 0:  # Rainforest
                base_color = habitats[1].base_color
                highlight = habitats[1].highlight_color
            elif x > 0 and y < 0:  # Arctic
                base_color = habitats[2].base_color
                highlight = habitats[2].highlight_color
            else:  # Wetlands
                base_color = habitats[3].base_color
                highlight = habitats[3].highlight_color
            
            # Add natural color variation
            blend = 0.7 + 0.3 * math.sin(x/50) * math.cos(y/50)
            r = base_color[0] * blend + highlight[0] * (1 - blend)
            g = base_color[1] * blend + highlight[1] * (1 - blend)
            b = base_color[2] * blend + highlight[2] * (1 - blend)
            
            glColor3f(r, g, b)
            glVertex3f(x, y, z)
            glVertex3f(x+20, y, z)
            glVertex3f(x+20, y+20, z)
            glVertex3f(x, y+20, z)
    glEnd()
    
    glPopMatrix()

def draw_water(x, y, radius):
    """Draw water areas with natural blue colors"""
    glPushMatrix()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    glColor4f(0.3, 0.5, 0.8, 0.6)  # Blue water with transparency
    glBegin(GL_POLYGON)
    for i in range(360):
        angle = math.radians(i)
        px = x + math.cos(angle) * radius
        py = y + math.sin(angle) * radius
        pz = 0.2 * math.sin(glutGet(GLUT_ELAPSED_TIME)/1000.0 )+ 0.5  # Animated ripple
        glVertex3f(px, py, pz)
    glEnd()
    
    glDisable(GL_BLEND)
    glPopMatrix()

def draw_tree(x, y, z, size, tree_type):
    """Draw 3D trees with natural colors"""
    glPushMatrix()
    glTranslatef(x, y, z)
    
    # Trunk (brown)
    glColor3f(0.4, 0.3, 0.2)
    gluCylinder(gluNewQuadric(), size*3, size*2, size*15, 8, 2)
    
    # Leaves/Foliage (green variations)
    if tree_type == "palm":
        glColor3f(0.3, 0.6, 0.3)
        glTranslatef(0, 0, size*15)
        glutSolidSphere(size*10, 10, 10)
    elif tree_type == "pine":
        glColor3f(0.2, 0.4, 0.2)
        for i in range(3):
            glTranslatef(0, 0, size*5)
            glutSolidCone(size*8, size*15, 8, 2)
    else:  # oak
        glColor3f(0.3, 0.5, 0.3)
        glTranslatef(0, 0, size*12)
        glutSolidSphere(size*12, 10, 10)
    
    glPopMatrix()

def draw_health_bar(x, y, width, health, happiness, size):
    """Draw health and happiness bars above the animal"""
    glPushMatrix()
    
    # Disable lighting for 2D HUD elements
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    # Move to position above animal
    glTranslatef(x, y, size * 2)
    
    # Make bars always face camera
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    camera_x = modelview[0][2]
    camera_y = modelview[1][2]
    angle = math.degrees(math.atan2(camera_y, camera_x))
    glRotatef(-angle, 0, 0, 1)
    
    bar_height = size * 0.2
    bar_spacing = size * 0.3
    
    # Health bar background
    glColor4f(0.2, 0.2, 0.2, 0.7)
    glBegin(GL_QUADS)
    glVertex3f(-width/2, bar_spacing, 0)
    glVertex3f(width/2, bar_spacing, 0)
    glVertex3f(width/2, bar_spacing + bar_height, 0)
    glVertex3f(-width/2, bar_spacing + bar_height, 0)
    glEnd()
    
    # Health bar fill
    health_width = width * (health / 100.0)
    glColor4f(2.0 * (1.0 - health/100.0),  # Red to green gradient
              2.0 * (health/100.0),
              0.0,
              0.8)
    glBegin(GL_QUADS)
    glVertex3f(-width/2, bar_spacing, 0)
    glVertex3f(-width/2 + health_width, bar_spacing, 0)
    glVertex3f(-width/2 + health_width, bar_spacing + bar_height, 0)
    glVertex3f(-width/2, bar_spacing + bar_height, 0)
    glEnd()
    
    # Happiness bar background
    glColor4f(0.2, 0.2, 0.2, 0.7)
    glBegin(GL_QUADS)
    glVertex3f(-width/2, 0, 0)
    glVertex3f(width/2, 0, 0)
    glVertex3f(width/2, bar_height, 0)
    glVertex3f(-width/2, bar_height, 0)
    glEnd()
    
    # Happiness bar fill
    happiness_width = width * (happiness / 100.0)
    glColor4f(0.2, 0.2, 1.0, 0.8)  # Blue for happiness
    glBegin(GL_QUADS)
    glVertex3f(-width/2, 0, 0)
    glVertex3f(-width/2 + happiness_width, 0, 0)
    glVertex3f(-width/2 + happiness_width, bar_height, 0)
    glVertex3f(-width/2, bar_height, 0)
    glEnd()
    
    # Re-enable lighting and depth test
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    glPopMatrix()

def draw_animal(animal):
    """Draw a more detailed and realistic animal"""
    x, y, z = animal["position"]
    size = animal["size"]
    r, g, b = animal["color"]
    angle = animal["angle"]
    
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(angle, 0, 0, 1)
    
    if animal["type"] == "elephant":
        # Enhanced elephant model
        # Body
        glColor3f(r, g, b)
        glPushMatrix()
        glScalef(1.8, 1, 1.2)
        glutSolidSphere(size * 0.8, 24, 24)
        glPopMatrix()
        
        # Head with detailed features
        glPushMatrix()
        glTranslatef(size, 0, size * 0.5)
        glScalef(1.2, 0.8, 1)
        glutSolidSphere(size * 0.5, 20, 20)
        
        # Eyes with reflection
        glPushMatrix()
        glColor3f(0.1, 0.1, 0.1)
        glTranslatef(size * 0.2, size * 0.2, size * 0.1)
        glutSolidSphere(size * 0.05, 12, 12)
        glColor3f(1, 1, 1)
        glTranslatef(size * 0.02, size * 0.02, 0)
        glutSolidSphere(size * 0.01, 8, 8)
        glTranslatef(-size * 0.02, -size * 0.42, 0)
        glColor3f(0.1, 0.1, 0.1)
        glutSolidSphere(size * 0.05, 12, 12)
        glColor3f(1, 1, 1)
        glTranslatef(size * 0.02, size * 0.02, 0)
        glutSolidSphere(size * 0.01, 8, 8)
        glPopMatrix()
        
        # Ears with movement
        glPushMatrix()
        ear_wave = math.sin(game_time * 2) * 10
        glColor3f(r * 0.9, g * 0.9, b * 0.9)
        
        # Left ear
        glPushMatrix()
        glTranslatef(0, size * 0.6, 0)
        glRotatef(-30 + ear_wave, 0, 1, 0)
        glScalef(0.1, 1, 1)
        glutSolidSphere(size * 0.6, 16, 16)
        glPopMatrix()
        
        # Right ear
        glTranslatef(0, -size * 0.6, 0)
        glRotatef(30 - ear_wave, 0, 1, 0)
        glScalef(0.1, 1, 1)
        glutSolidSphere(size * 0.6, 16, 16)
        glPopMatrix()
        
        # Trunk with segments and animation
        glColor3f(r * 0.9, g * 0.9, b * 0.9)
        glTranslatef(size * 0.4, 0, -size * 0.3)
        
        segments = 8
        trunk_wave = math.sin(game_time * 1.5) * 5
        for i in range(segments):
            angle = math.sin(game_time * 2 + i) * 10 + trunk_wave
            glRotatef(angle, 0, 1, 0)
            gluCylinder(gluNewQuadric(), 
                       size * (0.15 - i * 0.01), 
                       size * (0.14 - i * 0.01), 
                       size * 0.8 / segments, 16, 1)
            glTranslatef(0, 0, size * 0.8 / segments)
        glPopMatrix()
        
    elif animal["type"] == "lion":
        # Enhanced lion model
        # Body
        glColor3f(r, g, b)
        glPushMatrix()
        glScalef(1.4, 1, 1)
        glutSolidSphere(size * 0.7, 20, 20)
        glPopMatrix()
        
        # Head
        glPushMatrix()
        glTranslatef(size * 0.8, 0, size * 0.4)
        glutSolidSphere(size * 0.4, 16, 16)
        
        # Mane with wind effect
        glColor3f(r * 1.1, g * 0.8, b * 0.4)
        for i in range(20):
            glPushMatrix()
            angle = i * 18
            rad = math.radians(angle)
            wind = math.sin(game_time * 2 + angle) * 3
            x = (size * 0.5 + wind) * math.cos(rad)
            y = (size * 0.5 + wind) * math.sin(rad)
            glTranslatef(x, y, size * 0.2)
            glRotatef(angle, 0, 0, 1)
            glScalef(0.1, 0.4, 0.1)
            glutSolidSphere(size * 0.4, 8, 8)
            glPopMatrix()
        
        # Face features
        # Eyes
        glColor3f(0.1, 0.1, 0.1)
        glPushMatrix()
        glTranslatef(size * 0.2, size * 0.15, size * 0.1)
        glutSolidSphere(size * 0.05, 12, 12)
        glTranslatef(0, -size * 0.3, 0)
        glutSolidSphere(size * 0.05, 12, 12)
        glPopMatrix()
        
        # Nose
        glColor3f(0.3, 0.3, 0.3)
        glTranslatef(size * 0.3, 0, 0)
        glutSolidSphere(size * 0.08, 12, 12)
        glPopMatrix()
        
    elif animal["type"] == "panda":
        # Enhanced panda model
        # Body
        glColor3f(r, g, b)
        glPushMatrix()
        glScalef(1.2, 1, 1)
        glutSolidSphere(size * 0.8, 20, 20)
        
        # Black patches
        glColor3f(0.1, 0.1, 0.1)
        # Back patch
        glPushMatrix()
        glTranslatef(-size * 0.4, 0, size * 0.3)
        glScalef(0.8, 1, 0.5)
        glutSolidSphere(size * 0.5, 16, 16)
        glPopMatrix()
        
        # Leg patches
        for x, y in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            glPushMatrix()
            glTranslatef(size * 0.3 * x, size * 0.4 * y, -size * 0.4)
            glutSolidSphere(size * 0.25, 12, 12)
            glPopMatrix()
        glPopMatrix()
        
        # Head
        glPushMatrix()
        glTranslatef(size * 0.7, 0, size * 0.4)
        glColor3f(r, g, b)
        glutSolidSphere(size * 0.45, 16, 16)
        
        # Black eye patches
        glColor3f(0.1, 0.1, 0.1)
        for y in [-1, 1]:
            glPushMatrix()
            glTranslatef(size * 0.1, size * 0.2 * y, size * 0.1)
            glScalef(1, 0.7, 0.7)
            glutSolidSphere(size * 0.15, 12, 12)
            # Eyes
            glColor3f(0.05, 0.05, 0.05)
            glTranslatef(size * 0.05, 0, 0)
            glutSolidSphere(size * 0.06, 12, 12)
            glPopMatrix()
        
        # Nose
        glColor3f(0.1, 0.1, 0.1)
        glTranslatef(size * 0.2, 0, 0)
        glutSolidSphere(size * 0.08, 12, 12)
        glPopMatrix()
        
    elif animal["type"] == "penguin":
        # Enhanced penguin model
        # Body
        glColor3f(0.1, 0.1, 0.1)
        glPushMatrix()
        glScalef(0.8, 1, 1.2)
        glutSolidSphere(size * 0.7, 20, 20)
        
        # White belly
        glPushMatrix()
        glColor3f(0.95, 0.95, 0.95)
        glTranslatef(size * 0.2, 0, 0)
        glScalef(0.5, 0.8, 1)
        glutSolidSphere(size * 0.65, 16, 16)
        glPopMatrix()
        
        # Head
        glColor3f(0.1, 0.1, 0.1)
        glTranslatef(0, 0, size * 0.8)
        glutSolidSphere(size * 0.35, 16, 16)
        
        # Eyes
        glColor3f(1, 1, 1)
        for y in [-1, 1]:
            glPushMatrix()
            glTranslatef(size * 0.1, size * 0.15 * y, size * 0.1)
            glutSolidSphere(size * 0.08, 12, 12)
            glColor3f(0.1, 0.1, 0.1)
            glTranslatef(size * 0.02, 0, 0)
            glutSolidSphere(size * 0.04, 8, 8)
            glPopMatrix()
            glColor3f(1, 1, 1)
        
        # Beak
        glColor3f(1, 0.7, 0)
        glTranslatef(size * 0.2, 0, 0)
        glRotatef(90, 0, 1, 0)
        glutSolidCone(size * 0.1, size * 0.2, 12, 1)
        glPopMatrix()
        
        # Flippers with animation
        glColor3f(0.1, 0.1, 0.1)
        flipper_angle = math.sin(game_time * 3) * 20
        for y in [-1, 1]:
            glPushMatrix()
            glTranslatef(0, size * 0.4 * y, size * 0.4)
            glRotatef(60 * y + flipper_angle, 0, 0, 1)
            glScalef(0.2, 1, 0.4)
            glutSolidSphere(size * 0.5, 12, 12)
            glPopMatrix()
        
        # Feet
        glColor3f(1, 0.7, 0)
        for y in [-1, 1]:
            glPushMatrix()
            glTranslatef(0, size * 0.2 * y, -size * 0.6)
            glScalef(1, 0.3, 2)
            glutSolidCube(size * 0.2)
            glPopMatrix()
    
    # Draw health and happiness indicators
    draw_health_bar(0, 0, size * 2, animal["health"], animal["happiness"], size)
    
    glPopMatrix()

def draw_poacher(poacher):
    """Draw a more detailed poacher model with animations"""
    if not poacher["active"]:
        return
        
    x, y, z = poacher["position"]
    r, g, b = poacher["color"]
    
    glPushMatrix()
    glTranslatef(x, y, z)
    
    # Calculate angle based on movement direction
    if "last_position" in poacher:
        dx = x - poacher["last_position"][0]
        dy = y - poacher["last_position"][1]
        if abs(dx) > 0.01 or abs(dy) > 0.01:
            angle = math.degrees(math.atan2(dy, dx))
            poacher["angle"] = angle
    
    if "angle" in poacher:
        glRotatef(poacher["angle"], 0, 0, 1)
    
    # Walking animation
    walk_cycle = math.sin(game_time * 5) * 10
    
    # Body with more detail
    glColor3f(r, g, b)
    glPushMatrix()
    glScalef(0.7, 0.5, 1.0)
    glutSolidCube(30)
    
    # Add camouflage pattern
    glColor3f(r * 0.8, g * 0.8, b * 0.8)
    for _ in range(5):
        glPushMatrix()
        glTranslatef(random.uniform(-10, 10),
                    random.uniform(-10, 10),
                    15.1)
        glScalef(0.3, 0.3, 0.01)
        glutSolidCube(20)
        glPopMatrix()
    glPopMatrix()
    
    # Head with face features
    glPushMatrix()
    glTranslatef(0, 0, 40)
    glColor3f(r * 0.9, g * 0.9, b * 0.9)
    glutSolidSphere(10, 16, 16)
    
    # Eyes with mean expression
    glColor3f(0.1, 0.1, 0.1)
    for y in [-1, 1]:
        glPushMatrix()
        glTranslatef(3, 3 * y, 3)
        glRotatef(30, 0, 1, 0)
        glScalef(1, 0.5, 1)
        glutSolidSphere(2, 8, 8)
        glPopMatrix()
    
    # Hat
    glColor3f(r * 0.7, g * 0.7, b * 0.7)
    glTranslatef(0, 0, 5)
    glRotatef(-90, 1, 0, 0)
    glutSolidCone(12, 10, 12, 1)
    glPopMatrix()
    
    # Arms with joints and weapon
    glColor3f(r * 0.8, g * 0.8, b * 0.8)
    
    # Left arm
    glPushMatrix()
    glTranslatef(0, 20, 30)
    
    # Upper arm with animation
    glRotatef(30 + walk_cycle, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 4, 3, 15, 8, 1)
    
    # Elbow joint
    glTranslatef(0, 0, 15)
    glutSolidSphere(4, 8, 8)
    
    # Lower arm
    glRotatef(30, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 3, 2, 15, 8, 1)
    
    # Weapon with details
    glTranslatef(0, 0, 15)
    glColor3f(0.2, 0.2, 0.2)
    glRotatef(90, 0, 1, 0)
    
    # Main barrel
    gluCylinder(gluNewQuadric(), 2, 2, 25, 8, 1)
    
    # Scope
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(10, 3, 0)
    gluCylinder(gluNewQuadric(), 1.5, 1.5, 8, 8, 1)
    glTranslatef(0, 0, 0)
    glutSolidTorus(0.5, 2, 8, 8)
    glPopMatrix()
    
    # Stock
    glColor3f(0.3, 0.2, 0.1)
    glPushMatrix()
    glTranslatef(-5, 0, 0)
    glScalef(1, 1, 0.3)
    glutSolidCube(8)
    glPopMatrix()
    glPopMatrix()
    
    # Right arm
    glPushMatrix()
    glTranslatef(0, -20, 30)
    glColor3f(r * 0.8, g * 0.8, b * 0.8)
    
    # Upper arm with opposite animation
    glRotatef(30 - walk_cycle, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 4, 3, 15, 8, 1)
    
    # Elbow joint
    glTranslatef(0, 0, 15)
    glutSolidSphere(4, 8, 8)
    
    # Lower arm
    glRotatef(-20, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 3, 2, 15, 8, 1)
    glPopMatrix()
    
    # Legs with walking animation
    for y in [-1, 1]:
        glPushMatrix()
        glTranslatef(0, 10 * y, 0)
        glColor3f(r * 0.7, g * 0.7, b * 0.7)
        
        # Upper leg
        glRotatef(walk_cycle * y, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 5, 4, 20, 8, 1)
        
        # Knee
        glTranslatef(0, 0, 20)
        glutSolidSphere(4, 8, 8)
        
        # Lower leg
        glRotatef(-abs(walk_cycle) * 0.5, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 4, 3, 20, 8, 1)
        
        # Foot
        glTranslatef(0, 0, 20)
        glScalef(1, 1, 0.3)
        glutSolidCube(8)
        glPopMatrix()
    
    glPopMatrix()
    
    # Store current position for next frame's angle calculation
    poacher["last_position"] = (x, y, z)

def update_poacher_positions():
    """Update poacher positions with improved AI behavior"""
    for poacher in poachers:
        if not poacher["active"]:
            continue
            
        # Get current position and target animal
        px, py, pz = poacher["position"]
        target = None
        min_distance = float('inf')
        
        # Find closest animal
        for animal in animals:
            ax, ay, az = animal["position"]
            distance = math.sqrt((ax - px)**2 + (ay - py)**2)
            if distance < min_distance:
                min_distance = distance
                target = animal
        
        if target:
            tx, ty, tz = target["position"]
            
            # Calculate direction vector
            dx = tx - px
            dy = ty - py
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 0:
                # Normalize direction vector
                dx /= distance
                dy /= distance
                
                # Add some randomness to movement
                dx += random.uniform(-0.2, 0.2)
                dy += random.uniform(-0.2, 0.2)
                
                # Normalize again after adding randomness
                mag = math.sqrt(dx*dx + dy*dy)
                if mag > 0:
                    dx /= mag
                    dy /= mag
                
                # Move poacher toward target with speed variation
                speed = poacher["speed"] * (0.8 + math.sin(game_time) * 0.2)
                new_x = px + dx * speed
                new_y = py + dy * speed
                
                # Check for collisions with obstacles (simplified)
                collision = False
                for other in poachers:
                    if other != poacher and other["active"]:
                        ox, oy, _ = other["position"]
                        if math.sqrt((new_x - ox)**2 + (new_y - oy)**2) < 30:
                            collision = True
                            break
                
                if not collision:
                    poacher["position"] = (new_x, new_y, pz)
                    
                # Update poacher state
                poacher["target_distance"] = distance
                if "last_position" not in poacher:
                    poacher["last_position"] = poacher["position"]

def draw_mini_map_dot(x, y, size):
    """Draw a dot on the mini-map"""
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(x, y)
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        glVertex2f(x + math.cos(rad) * size, y + math.sin(rad) * size)
    glVertex2f(x + size, y)
    glEnd()

def draw_text(x, y, text):
    """Draw text at the specified position"""
    glPushMatrix()
    glLoadIdentity()
    
    # Disable lighting for text
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    # Position the text
    glRasterPos2f(x, y)
    
    # Draw each character
    for char in str(text):
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Re-enable lighting and depth test
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    glPopMatrix()

def draw_ui():
    """Draw an enhanced game UI with modern styling"""
    viewport = glGetIntegerv(GL_VIEWPORT)
    width = viewport[2]
    height = viewport[3]
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Enable blending for transparency
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Draw top bar background
    glColor4f(0.2, 0.2, 0.2, 0.8)
    glBegin(GL_QUADS)
    glVertex2f(0, height - 60)
    glVertex2f(width, height - 60)
    glVertex2f(width, height)
    glVertex2f(0, height)
    glEnd()
    
    # Draw score and currency with icons
    glColor3f(1.0, 1.0, 1.0)
    draw_text(20, height - 40, f"Score: {score}")
    draw_text(200, height - 40, f"Currency: ${currency}")
    
    # Draw mini-map in top right corner
    map_size = 150
    margin = 20
    glColor4f(0.1, 0.1, 0.1, 0.8)
    glBegin(GL_QUADS)
    glVertex2f(width - map_size - margin, height - map_size - margin)
    glVertex2f(width - margin, height - map_size - margin)
    glVertex2f(width - margin, height - margin)
    glVertex2f(width - map_size - margin, height - margin)
    glEnd()
    
    # Draw habitat zones on mini-map
    for habitat in habitats:
        x, y, _ = habitat.position
        size = habitat.size
        r, g, b = habitat.base_color
        
        # Scale coordinates to mini-map
        map_x = width - map_size - margin + (x + GRID_SIZE) * map_size / (2 * GRID_SIZE)
        map_y = height - map_size - margin + (y + GRID_SIZE) * map_size / (2 * GRID_SIZE)
        map_size_scaled = size * map_size / (2 * GRID_SIZE)
        
        glColor4f(r, g, b, 0.6)
        glBegin(GL_QUADS)
        glVertex2f(map_x - map_size_scaled, map_y - map_size_scaled)
        glVertex2f(map_x + map_size_scaled, map_y - map_size_scaled)
        glVertex2f(map_x + map_size_scaled, map_y + map_size_scaled)
        glVertex2f(map_x - map_size_scaled, map_y + map_size_scaled)
        glEnd()
    
    # Draw animals and poachers on mini-map
    for animal in animals:
        x, y, _ = animal["position"]
        map_x = width - map_size - margin + (x + GRID_SIZE) * map_size / (2 * GRID_SIZE)
        map_y = height - map_size - margin + (y + GRID_SIZE) * map_size / (2 * GRID_SIZE)
        
        glColor3f(0.2, 0.8, 0.2)  # Green for animals
        draw_mini_map_dot(map_x, map_y, 4)
    
    for poacher in poachers:
        if poacher["active"]:
            x, y, _ = poacher["position"]
            map_x = width - map_size - margin + (x + GRID_SIZE) * map_size / (2 * GRID_SIZE)
            map_y = height - map_size - margin + (y + GRID_SIZE) * map_size / (2 * GRID_SIZE)
            
            glColor3f(1.0, 0.2, 0.2)  # Red for poachers
            draw_mini_map_dot(map_x, map_y, 4)
    
    # Draw animal status panels on the left
    panel_height = 80
    panel_width = 200
    margin = 20
    
    for i, animal in enumerate(animals):
        y_pos = height - 100 - (panel_height + 10) * (i + 1)
        
        # Panel background
        glColor4f(0.2, 0.2, 0.2, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(margin, y_pos)
        glVertex2f(margin + panel_width, y_pos)
        glVertex2f(margin + panel_width, y_pos + panel_height)
        glVertex2f(margin, y_pos + panel_height)
        glEnd()
        
        # Animal info
        glColor3f(1.0, 1.0, 1.0)
        draw_text(margin + 10, y_pos + panel_height - 25, f"{animal['type'].title()}")
        
        # Health bar
        bar_width = panel_width - 20
        health_width = bar_width * animal["health"] / 100
        
        # Health bar background
        glColor4f(0.3, 0.3, 0.3, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(margin + 10, y_pos + 40)
        glVertex2f(margin + 10 + bar_width, y_pos + 40)
        glVertex2f(margin + 10 + bar_width, y_pos + 50)
        glVertex2f(margin + 10, y_pos + 50)
        glEnd()
        
        # Health bar fill
        health_color = (
            2.0 * (1.0 - animal["health"] / 100.0),
            2.0 * (animal["health"] / 100.0),
            0.0
        )
        glColor3f(*health_color)
        glBegin(GL_QUADS)
        glVertex2f(margin + 10, y_pos + 40)
        glVertex2f(margin + 10 + health_width, y_pos + 40)
        glVertex2f(margin + 10 + health_width, y_pos + 50)
        glVertex2f(margin + 10, y_pos + 50)
        glEnd()
        
        # Happiness bar
        happiness_width = bar_width * animal["happiness"] / 100
        
        # Happiness bar background
        glColor4f(0.3, 0.3, 0.3, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(margin + 10, y_pos + 15)
        glVertex2f(margin + 10 + bar_width, y_pos + 15)
        glVertex2f(margin + 10 + bar_width, y_pos + 25)
        glVertex2f(margin + 10, y_pos + 25)
        glEnd()
        
        # Happiness bar fill
        glColor3f(0.2, 0.2, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(margin + 10, y_pos + 15)
        glVertex2f(margin + 10 + happiness_width, y_pos + 15)
        glVertex2f(margin + 10 + happiness_width, y_pos + 25)
        glVertex2f(margin + 10, y_pos + 25)
        glEnd()
    
    # Draw game controls help
    glColor4f(0.2, 0.2, 0.2, 0.8)
    glBegin(GL_QUADS)
    glVertex2f(width - 250, 20)
    glVertex2f(width - 20, 20)
    glVertex2f(width - 20, 120)
    glVertex2f(width - 250, 120)
    glEnd()
    
    glColor3f(1.0, 1.0, 1.0)
    draw_text(width - 240, 90, "Controls:")
    draw_text(width - 240, 70, "WASD - Move Camera")
    draw_text(width - 240, 50, "Mouse - Aim")
    draw_text(width - 240, 30, "Left Click - Shoot Tranquilizer")
    
    glDisable(GL_BLEND)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_sky():
    """Draw a gradient sky background"""
    glPushMatrix()
    glLoadIdentity()
    
    # Disable lighting for sky
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    # Draw sky as a gradient quad
    glBegin(GL_QUADS)
    # Top color (lighter blue)
    glColor3f(0.53, 0.81, 0.98)
    glVertex3f(-1000, -1000, 1000)
    glVertex3f(1000, -1000, 1000)
    # Bottom color (darker blue)
    glColor3f(0.7, 0.9, 1.0)
    glVertex3f(1000, 1000, -100)
    glVertex3f(-1000, 1000, -100)
    glEnd()
    
    # Re-enable depth testing for other objects
    glEnable(GL_DEPTH_TEST)
    
    glPopMatrix()

def draw_zoo_ground():
    """Draw the zoo ground with terrain features"""
    glPushMatrix()
    
    # Enable texturing for ground
    glEnable(GL_LIGHTING)
    glEnable(GL_COLOR_MATERIAL)
    
    # Draw main ground plane with terrain variation
    glBegin(GL_QUADS)
    for x in range(-GRID_SIZE, GRID_SIZE, 20):
        for y in range(-GRID_SIZE, GRID_SIZE, 20):
            # Calculate terrain height using sine waves for natural variation
            z1 = TERRAIN_HEIGHT * math.sin(x/100.0) * math.cos(y/100.0)
            z2 = TERRAIN_HEIGHT * math.sin((x+20)/100.0) * math.cos(y/100.0)
            z3 = TERRAIN_HEIGHT * math.sin((x+20)/100.0) * math.cos((y+20)/100.0)
            z4 = TERRAIN_HEIGHT * math.sin(x/100.0) * math.cos((y+20)/100.0)
            
            # Determine ground color based on position (different habitats)
            if x < 0 and y > 0:  # Savannah
                base_color = habitats[0].base_color
                highlight = habitats[0].highlight_color
            elif x > 0 and y > 0:  # Rainforest
                base_color = habitats[1].base_color
                highlight = habitats[1].highlight_color
            elif x > 0 and y < 0:  # Arctic
                base_color = habitats[2].base_color
                highlight = habitats[2].highlight_color
            else:  # Wetlands
                base_color = habitats[3].base_color
                highlight = habitats[3].highlight_color
            
            # Add color variation based on height
            blend = 0.7 + 0.3 * math.sin(x/50.0) * math.cos(y/50.0)
            r = base_color[0] * blend + highlight[0] * (1 - blend)
            g = base_color[1] * blend + highlight[1] * (1 - blend)
            b = base_color[2] * blend + highlight[2] * (1 - blend)
            
            glColor3f(r, g, b)
            
            # Draw quad with terrain height
            glVertex3f(x, y, z1)
            glVertex3f(x+20, y, z2)
            glVertex3f(x+20, y+20, z3)
            glVertex3f(x, y+20, z4)
            
            # Draw grid lines for visual reference
            if (x % 100 == 0 or y % 100 == 0):
                glColor3f(0.3, 0.3, 0.3)
                glVertex3f(x, y, z1+0.1)
                glVertex3f(x+20, y, z2+0.1)
                glVertex3f(x+20, y+20, z3+0.1)
                glVertex3f(x, y+20, z4+0.1)
    glEnd()
    
    glPopMatrix()

def display():
    """Main display function"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Setup camera
    gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
              0, 0, 50,
              0, 0, 1)
    
    # Draw sky background first
    draw_sky()
    
    # Enable lighting for 3D objects
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    
    # Draw zoo ground and habitats
    draw_zoo_ground()
    
    # Draw zoo elements
    for animal in animals:
        draw_animal(animal)
    
    for tree in trees:
        draw_tree(tree['x'], tree['y'], 0, tree['size'], tree['type'])
    
    for water in water_areas:
        draw_water(water['x'], water['y'], water['radius'])  # Fixed to call draw_water
    
    # Draw UI
    draw_ui()
    
    glutSwapBuffers()

def reshape(w, h):
    """Handle window resizing"""
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, float(w)/float(h), 1.0, 1000.0)
    glMatrixMode(GL_MODELVIEW)

def keyboard(key, x, y):
    """Handle keyboard input"""
    global camera_pos, camera_angle
    
    move_speed = 10
    rotate_speed = 5
    
    if key == b'w':
        camera_pos[0] += move_speed * math.sin(math.radians(camera_angle))
        camera_pos[1] -= move_speed * math.cos(math.radians(camera_angle))
    elif key == b's':
        camera_pos[0] -= move_speed * math.sin(math.radians(camera_angle))
        camera_pos[1] += move_speed * math.cos(math.radians(camera_angle))
    elif key == b'a':
        camera_angle -= rotate_speed
    elif key == b'd':
        camera_angle += rotate_speed
    elif key == b'q':
        camera_pos[2] += move_speed
    elif key == b'e':
        camera_pos[2] -= move_speed
    elif key == b'\x1b':  # Escape key
        sys.exit(0)
    
    glutPostRedisplay()

def special_keys(key, x, y):
    """Handle special keys"""
    global camera_pos
    
    if key == GLUT_KEY_UP:
        camera_pos[2] += 5
    elif key == GLUT_KEY_DOWN:
        camera_pos[2] -= 5
    elif key == GLUT_KEY_LEFT:
        camera_angle -= 5
    elif key == GLUT_KEY_RIGHT:
        camera_angle += 5
    
    glutPostRedisplay()

def idle():
    """Idle function for animations"""
    global game_time
    game_time = glutGet(GLUT_ELAPSED_TIME) / 1000.0  # Convert to seconds
    glutPostRedisplay()

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    
    # Get screen dimensions and create fullscreen window
    screen_width = glutGet(GLUT_SCREEN_WIDTH)
    screen_height = glutGet(GLUT_SCREEN_HEIGHT)
    glutInitWindowSize(screen_width, screen_height)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"3D Zoo Defender")
    
    # Initialize environment
    init_environment()
    
    # Set callback functions
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutIdleFunc(idle)
    
    # Enable depth testing and blending
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Set background to sky blue
    glClearColor(0.53, 0.81, 0.98, 1.0)
    
    glutFullScreen()
    glutMainLoop()

if __name__ == "__main__":
    main()