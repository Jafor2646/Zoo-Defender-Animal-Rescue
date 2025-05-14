from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import random
import math
import time

# Camera-related variables
camera_pos = (0, 500, 350)  # Adjusted camera height
camera_angle = 0
camera_mode = "third_person"  # "first_person" or "third_person"

fovY = 90  # Reduced field of view for better perspective
GRID_LENGTH = 600  # Length of grid lines

# Game state
game_score = 0
currency = 1000  # Starting currency
game_time = 0
game_paused = False
last_time = time.time()

# Player-related variables
player_pos = [0, 0, 30]  # x, y, z position
player_angle = 0
player_speed = 10
interaction_range = 100  # Range for animal interaction
shoot_cooldown = 0
selected_animal_index = None
feed_cost = 50

# OpenGL utilities
quad = gluNewQuadric()


SKY_COLOR = (0.6, 0.8, 1.0)  # Light blue sky
GROUND_COLOR = (0.35, 0.25, 0.1)  # Brown soil
FENCE_HEIGHT = 50
FENCE_POST_THICKNESS = 8

game_over = False
restart_timer = None

# Animals
class Animal:
    def __init__(self, pos, type_name, habitat_color, size):
        self.pos = list(pos)
        self.type = type_name
        self.habitat_color = habitat_color
        self.size = size
        self.happiness = 100
        self.health = 100
        self.last_move_time = time.time()
        self.move_dir = [random.uniform(-1, 1), random.uniform(-1, 1), 0]
        self.normalize_dir()
        self.captured = False
        self.last_happiness_decay = time.time()
        self.is_eating = False
        self.habitat_index = None  # Will be set when creating the animal
        self.last_food_check = time.time()
        self.last_food_check = time.time()
        self.hunger_rate = random.uniform(0.15, 0.25)  # Different hunger rates for animals
        self.dead = False
    def normalize_dir(self):
        length = math.sqrt(self.move_dir[0]**2 + self.move_dir[1]**2)
        if length > 0:
            self.move_dir[0] /= length
            self.move_dir[1] /= length
    
    def update(self, current_time):
        if self.dead or self.captured:
            return
            
        # Move randomly or go to feeding station if hungry
        if self.happiness < 70 and FOOD_LEVEL[self.habitat_index] > 0:
            # Calculate direction to feeding station
            habitat = habitats[self.habitat_index]
            feeding_x = habitat["center"][0] + 50  # Feeding station offset
            feeding_y = habitat["center"][1] - 50
            
            dir_to_food = [feeding_x - self.pos[0], feeding_y - self.pos[1]]
            food_dist = math.sqrt(dir_to_food[0]**2 + dir_to_food[1]**2)
            
            if food_dist < 30:  # Close enough to eat - increased range
                self.is_eating = True
                # Check if we can consume food every 5 seconds
                if current_time - self.last_food_check > 5 and FOOD_LEVEL[self.habitat_index] > 0:
                    self.happiness = min(100, self.happiness + 20)
                    self.health = min(100, self.health + 15)
                    FOOD_LEVEL[self.habitat_index] -= 1  # Consume food
                    self.last_food_check = current_time
            else:
                # Move toward feeding station
                self.is_eating = False
                if food_dist > 0:
                    self.move_dir[0] = dir_to_food[0] / food_dist
                    self.move_dir[1] = dir_to_food[1] / food_dist
                    self.pos[0] += self.move_dir[0] * 2  # Move faster when hungry
                    self.pos[1] += self.move_dir[1] * 2
        else:
            self.is_eating = False
            # Normal random movement
            if current_time - self.last_move_time > 3:
                self.move_dir = [random.uniform(-1, 1), random.uniform(-1, 1), 0]
                self.normalize_dir()
                self.last_move_time = current_time
            
            # Stay within habitat bounds (radius 200 from habitat center)
            dist_from_habitat = math.sqrt((self.pos[0] - self.habitat_pos[0])**2 + 
                                         (self.pos[1] - self.habitat_pos[1])**2)
            
            if dist_from_habitat < 180:  # Normal movement inside habitat
                self.pos[0] += self.move_dir[0] * 1
                self.pos[1] += self.move_dir[1] * 1
            else:  # Move back toward habitat center
                dir_to_center = [self.habitat_pos[0] - self.pos[0], 
                                self.habitat_pos[1] - self.pos[1]]
                length = math.sqrt(dir_to_center[0]**2 + dir_to_center[1]**2)
                if length > 0:
                    dir_to_center[0] /= length
                    dir_to_center[1] /= length
                self.pos[0] += dir_to_center[0] * 2
                self.pos[1] += dir_to_center[1] * 2
        
        # Happiness and health decay over time - more significant impact of hunger
        if current_time - self.last_happiness_decay > 10:  # Every 10 seconds
            self.happiness = max(0, self.happiness - 3)  # Faster happiness decay
            
            # Health decay based on happiness level
            if self.happiness < 30:
                self.health = max(0, self.health - self.hunger_rate * 4)  # Severe health impact
            elif self.happiness < 60:
                self.health = max(0, self.health - self.hunger_rate * 2)  # Moderate health impact
            else:
                # Minor health decay even when happy, to ensure feeding is needed
                self.health = max(0, self.health - self.hunger_rate)
                
            self.last_happiness_decay = current_time
            
        # Check if animal has died from starvation
        if self.health <= 0:
            self.dead = True
    
    def feed(self):
        # Old direct feeding method (still used for backward compatibility)
        self.happiness = min(100, self.happiness + 30)
        self.health = min(100, self.health + 20)
        
    def get_color(self):
        # Health-based color (red component increases as health decreases)
        r = 1.0 - (self.health / 100) * 0.8
        g = (self.health / 100) * 0.8
        b = 0.2
        return (r, g, b)
# Initialize animal habitats and animals
# Update habitats to rename Desert to Farm
habitats = [
    {"center": (-400, 400, 0), "color": (0.2, 0.7, 0.2), "name": "Savannah"},
    {"center": (400, 400, 0), "color": (0.2, 0.2, 0.7), "name": "Arctic"},
    {"center": (-400, -400, 0), "color": (0.7, 0.5, 0.2), "name": "Farm"},  # Changed from Desert
    {"center": (400, -400, 0), "color": (0.1, 0.5, 0.1), "name": "Jungle"}
]
FEEDING_STATION_SIZE = 40
FOOD_LEVEL = {}
# Initialize feeding stations for each habitat
for i, habitat in enumerate(habitats):
    FOOD_LEVEL[i] = 0  # Start with empty feeding stations

# Expand animal types with farm animals
animal_types = [
    # Savannah zone
    {"name": "Elephant", "size": 60, "habitat_index": 0},
    {"name": "Lion", "size": 40, "habitat_index": 0},
    {"name": "Giraffe", "size": 50, "habitat_index": 0},
    {"name": "Zebra", "size": 35, "habitat_index": 0},
    
    # Arctic zone
    {"name": "Polar Bear", "size": 50, "habitat_index": 1},
    {"name": "Penguin", "size": 30, "habitat_index": 1},
    {"name": "Arctic Fox", "size": 25, "habitat_index": 1},
    
    # Farm zone (replacing Desert)
    {"name": "Cow", "size": 45, "habitat_index": 2},
    {"name": "Horse", "size": 50, "habitat_index": 2},
    {"name": "Goat", "size": 30, "habitat_index": 2},
    {"name": "Sheep", "size": 35, "habitat_index": 2},
    
    # Jungle zone
    {"name": "Tiger", "size": 40, "habitat_index": 3},
    {"name": "Monkey", "size": 25, "habitat_index": 3},
    {"name": "Panda", "size": 45, "habitat_index": 3}
]

# Initialize animals in their habitats (modify the existing initialization)
animals = []
for animal_type in animal_types:
    habitat = habitats[animal_type["habitat_index"]]
    pos_x = habitat["center"][0] + random.uniform(-150, 150)
    pos_y = habitat["center"][1] + random.uniform(-150, 150)
    animal = Animal((pos_x, pos_y, 20), animal_type["name"], habitat["color"], animal_type["size"])
    animal.habitat_pos = habitat["center"]
    animal.habitat_index = animal_type["habitat_index"]  # Set the habitat index
    animals.append(animal)
# Poachers
class Poacher:
    def __init__(self, pos, target_animal):
        self.pos = list(pos)
        self.target_animal = target_animal
        self.speed = 10
        self.captured = False
        self.active = True
        self.direction_change_time = time.time()
        
    def update(self):
        if not self.active or self.captured:
            return
        
        current_time = time.time()
        
        # Move towards target animal
        if self.target_animal and not self.target_animal.captured and not self.target_animal.dead:
            # Change direction less frequently for slower, more predictable movement
            if current_time - self.direction_change_time > 2:
                dir_x = self.target_animal.pos[0] - self.pos[0]
                dir_y = self.target_animal.pos[1] - self.pos[1]
                length = math.sqrt(dir_x**2 + dir_y**2)
                
                if length < 20:  # Captured animal
                    self.target_animal.captured = True
                    self.active = False
                elif length > 0:
                    dir_x /= length
                    dir_y /= length
                    
                    # Add some randomness to movement for less direct pathing
                    dir_x += random.uniform(-0.3, 0.3)
                    dir_y += random.uniform(-0.3, 0.3)
                    
                    # Re-normalize
                    new_length = math.sqrt(dir_x**2 + dir_y**2)
                    if new_length > 0:
                        dir_x /= new_length
                        dir_y /= new_length
                    
                    # Update position
                    self.pos[0] += dir_x * self.speed
                    self.pos[1] += dir_y * self.speed
                    
                self.direction_change_time = current_time
        else:
            # Find a new target if the current one is captured or dead
            valid_targets = [a for a in animals if not a.captured and not a.dead]
            if valid_targets:
                self.target_animal = random.choice(valid_targets)
            else:
                self.active = False  # No more targets available

poachers = []
last_poacher_spawn_time = time.time()
poacher_spawn_interval = 15  # Spawn a poacher every 15 seconds

# Tranquilizer darts
class Dart:
    def __init__(self, pos, direction):
        self.pos = list(pos)
        self.direction = direction
        self.speed = 15
        self.active = True
        self.life_time = time.time() + 5  # Dart exists for 5 seconds
        
    def update(self):
        if not self.active:
            return
        
        self.pos[0] += self.direction[0] * self.speed
        self.pos[1] += self.direction[1] * self.speed
        self.pos[2] += self.direction[2] * self.speed
        
        # Check if dart has expired
        if time.time() > self.life_time:
            self.active = False
        
        # Check collision with poachers
        for poacher in poachers:
            if poacher.active and not poacher.captured:
                dist = math.sqrt((self.pos[0] - poacher.pos[0])**2 + 
                                (self.pos[1] - poacher.pos[1])**2 + 
                                (self.pos[2] - poacher.pos[2])**2)
                if dist < 30:  # Hit detection radius
                    poacher.captured = True
                    self.active = False
                    global game_score
                    game_score += 100

darts = []

def draw_sky():
    # Draw a sky gradient as a large quad backdrop
    glPushMatrix()
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    # Draw sky gradient from top to bottom
    glBegin(GL_QUADS)
    # Top (lighter blue)
    glColor3f(0.7, 0.85, 1.0)
    glVertex3f(-2000, -2000, 1000)
    glVertex3f(2000, -2000, 1000)
    # Bottom (deeper blue)
    glColor3f(0.5, 0.7, 0.9)
    glVertex3f(2000, 2000, -100)
    glVertex3f(-2000, 2000, -100)
    glEnd()
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glPopMatrix()

def draw_mountain_ring(center_x, center_y, radius=1200, base_z=-1, peak_min=250, peak_max=400, segments=48):
    # Draw a ring of stylized mountains around the play area
    glPushMatrix()
    glTranslatef(center_x, center_y, 0)
    angle_step = 2 * math.pi / segments
    
    for i in range(segments):
        a0 = i * angle_step
        a1 = (i + 1) * angle_step
        
        # Base points with varying radius for more natural look
        base_variation = 150 * math.sin(i * 2.5)  # Increased base variation
        current_radius = radius + base_variation
        
        # Make mountains wider by increasing the angular spread
        spread = angle_step * 0.7  # Wider angular spread for each mountain
        x0, y0 = current_radius * math.cos(a0 - spread), current_radius * math.sin(a0 - spread)
        x1, y1 = current_radius * math.cos(a1 + spread), current_radius * math.sin(a1 + spread)
          # Peak (deterministic for no flicker)
        peak_angle = (a0 + a1) / 2
        peak_radius = current_radius + 300 + 150 * math.sin(i * 1.7)  # Increased peak distance
        px = peak_radius * math.cos(peak_angle)
        py = peak_radius * math.sin(peak_angle)
        
        # More varied peak heights with wider base relationship
        peak_height = peak_min + (peak_max - peak_min) * (0.6 + 0.4 * math.sin(i * 2.3))
        # Adjust height based on width for more natural proportion
        width_factor = 1.0 + 0.3 * abs(math.sin(i * 1.7))
        peak_height *= width_factor
        
        # Draw mountain face with gradient
        glBegin(GL_TRIANGLES)
        # Base color (darker for depth)
        glColor3f(0.35, 0.3, 0.25)
        glVertex3f(x0, y0, base_z)
        glVertex3f(x1, y1, base_z)
        
        # Peak color (lighter for snow caps and height definition)
        peak_brightness = 0.6 + 0.4 * (peak_height / peak_max)
        glColor3f(peak_brightness, peak_brightness, peak_brightness)
        glVertex3f(px, py, peak_height)
        glEnd()
        
        # Optional: Add ridge lines for better definition
        glColor3f(0.3, 0.25, 0.2)
        glBegin(GL_LINES)
        glVertex3f(x0, y0, base_z)
        glVertex3f(px, py, peak_height)
        glVertex3f(x1, y1, base_z)
        glVertex3f(px, py, peak_height)
        glEnd()
    
    glPopMatrix()

def draw_environment():
    draw_sky()
    
    # Draw ground (large enough for all habitats and mountains)
    # Ground color (sandy/dirt color)
    glDisable(GL_LIGHTING)  # Disable lighting for consistent ground color
    glColor3f(0.76, 0.70, 0.50)  # Sandy/dirt color
    glBegin(GL_QUADS)
    glVertex3f(-1400, -1400, -1)
    glVertex3f(1400, -1400, -1)
    glVertex3f(1400, 1400, -1)
    glVertex3f(-1400, 1400, -1)
    glEnd()
    glEnable(GL_LIGHTING)  # Re-enable lighting for other objects
    
    # Draw mountains ring around the play area
    draw_mountain_ring(0, 0, radius=1200, base_z=-1, peak_min=250, peak_max=400, segments=64)
    
    # Draw habitats (main area, detailed)
    for i, habitat in enumerate(habitats):
        glPushMatrix()
        x, y, z = habitat["center"]
        glTranslatef(x, y, z)
        
        # Draw habitat circular ground with unique texture
        glColor3f(*habitat["color"])
        glBegin(GL_POLYGON)
        for j in range(36):
            angle = j * 10 * math.pi / 180
            glVertex3f(200 * math.cos(angle), 200 * math.sin(angle), 0.1)  # Slightly above ground
        glEnd()
        
        # Draw fences around habitats
        glColor3f(0.6, 0.4, 0.2)  # Wood color
        for j in range(36):
            angle1 = j * 10 * math.pi / 180
            angle2 = (j+1) * 10 * math.pi / 180
            
            # Draw fence post
            glPushMatrix()
            glTranslatef(200 * math.cos(angle1), 200 * math.sin(angle1), 0)
            glRotatef(angle1 * 180/math.pi + 90, 0, 0, 1)
            
            # Fence post
            glPushMatrix()
            glScalef(FENCE_POST_THICKNESS, FENCE_POST_THICKNESS, FENCE_HEIGHT)
            glutSolidCube(1)
            glPopMatrix()
            
            # Horizontal rails (2 rails)
            for h in range(1, 3):
                rail_height = FENCE_HEIGHT * h/3
                glPushMatrix()
                glTranslatef(0, 0, rail_height)
                glRotatef(90, 0, 1, 0)
                gluCylinder(gluNewQuadric(), FENCE_POST_THICKNESS/2, FENCE_POST_THICKNESS/2, 
                           2 * math.pi * 200/36, 4, 1)
                glPopMatrix()
                
            glPopMatrix()
        
        # Draw feeding station for this habitat
        glPushMatrix()
        glTranslatef(50, -50, 0)  # Offset from center
        
        # Base of feeding trough
        glColor3f(0.4, 0.3, 0.2)  # Dark wood color
        glPushMatrix()
        glScalef(FEEDING_STATION_SIZE, FEEDING_STATION_SIZE/2, FEEDING_STATION_SIZE/4)
        glutSolidCube(1)
        glPopMatrix()
        
        # Legs for the feeding trough
        for leg_x, leg_y in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            glPushMatrix()
            glTranslatef(
                leg_x * (FEEDING_STATION_SIZE/2 - 5), 
                leg_y * (FEEDING_STATION_SIZE/4 - 5), 
                -FEEDING_STATION_SIZE/8
            )
            glScalef(4, 4, FEEDING_STATION_SIZE/4)
            glutSolidCube(1)
            glPopMatrix()
            
        # Draw food pile (height based on food level)
        if FOOD_LEVEL[i] > 0:
            food_height = min(FOOD_LEVEL[i] * 2, 20)
            
            # Food color depends on habitat
            if i == 0:  # Savannah - yellowish grass
                glColor3f(0.8, 0.7, 0.2)
            elif i == 1:  # Arctic - fish
                glColor3f(0.7, 0.7, 0.8)
            elif i == 2:  # Farm - hay
                glColor3f(0.9, 0.8, 0.2)
            else:  # Jungle - fruits
                glColor3f(0.8, 0.2, 0.2)
                
            glPushMatrix()
            glTranslatef(0, 0, food_height/2)
            glScalef(FEEDING_STATION_SIZE - 10, FEEDING_STATION_SIZE/2 - 5, food_height)
            glutSolidCube(1)
            glPopMatrix()
            
        glPopMatrix()  # End feeding station
        
        glPopMatrix()  # End of habitat drawing

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    # Set up an orthographic projection that matches window coordinates
    gluOrtho2D(0, 1000, 0, 800)  # left, right, bottom, top

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw text at (x, y) in screen coordinates
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    
    # Restore original projection and modelview matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_player():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(player_angle, 0, 0, 1)  # Rotate in XY plane

    # Main body - upright cylinder
    glColor3f(0.2, 0.5, 0.2)  # Green color
    quad = gluNewQuadric()
    gluCylinder(quad, 10, 10, 40, 8, 1)  # Simple cylinder body

    # Head (only if not in first-person view)
    if camera_mode != "first_person":
        glColor3f(0.3, 0.3, 0.3)  # Dark gray
        glPushMatrix()
        glTranslatef(0, 0, 40)  # Top of cylinder
        glutSolidSphere(8, 8, 8)  # Simple sphere for head
        glPopMatrix()

    # Legs
    glColor3f(0.2, 0.5, 0.2)  # Match body color
    # Left leg
    glPushMatrix()
    glTranslatef(-5, 0, 0)  # Left side
    gluCylinder(quad, 3, 3, 20, 8, 1)  # Upper leg
    glTranslatef(0, 2, 0)  # Foot points forward
    glColor3f(0.3, 0.3, 0.3)  # Dark gray for shoes
    glutSolidCube(6)
    glPopMatrix()

    # Right leg
    glPushMatrix()
    glTranslatef(5, 0, 0)  # Right side
    glColor3f(0.2, 0.5, 0.2)
    gluCylinder(quad, 3, 3, 20, 8, 1)
    glTranslatef(0, 2, 0)
    glColor3f(0.3, 0.3, 0.3)
    glutSolidCube(6)
    glPopMatrix()

    # Arms and hands positioned to hold the gun
    glPushMatrix()
    glTranslatef(0, 6, 25)  # Move to chest height and slightly forward

    # Left arm
    glColor3f(0.2, 0.5, 0.2)
    glPushMatrix()
    glTranslatef(-10, -2, 0)  # Position for holding gun
    glRotatef(30, 0, 0, 1)  # Angle arm to hold gun
    gluCylinder(quad, 3, 3, 12, 8, 1)
    glTranslatef(0, 0, 12)
    glColor3f(0.8, 0.6, 0.4)  # Hand color
    glutSolidSphere(4, 8, 8)
    glPopMatrix()

    # Right arm
    glColor3f(0.2, 0.5, 0.2)
    glPushMatrix()
    glTranslatef(10, -2, 0)  # Position for holding gun
    glRotatef(-30, 0, 0, 1)  # Angle arm to hold gun
    gluCylinder(quad, 3, 3, 12, 8, 1)
    glTranslatef(0, 0, 12)
    glColor3f(0.8, 0.6, 0.4)  # Hand color
    glutSolidSphere(4, 8, 8)
    glPopMatrix()

    # Gun between hands, aligned with shooting direction
    glColor3f(0.4, 0.4, 0.4)  # Gray
    glPushMatrix()
    glTranslatef(0, 10, 6)  # Position between hands
    gluCylinder(quad, 3, 2, 20, 8, 1)  # Gun barrel (cylinder)
    
    # Gun sight on top
    glPushMatrix()
    glTranslatef(0, 0, 10)  # Middle of barrel
    glScalef(1, 1, 0.3)
    glutSolidCube(4)
    glPopMatrix()

    glPopMatrix()  # End gun

    glPopMatrix()  # End arms assembly
    glPopMatrix()


def draw_shapes():
    # Draw environment first
    draw_environment()
    
    # Draw animals
    for i, animal in enumerate(animals):
        if animal.captured:
            continue
            
        glPushMatrix()
        glTranslatef(animal.pos[0], animal.pos[1], animal.pos[2])
        
        # Rotate in the direction of movement
        angle = math.atan2(animal.move_dir[1], animal.move_dir[0]) * 180/math.pi
        glRotatef(angle, 0, 0, 1)
        
        # Draw selection indicator if this animal is selected
        if selected_animal_index == i:
            glColor3f(1, 1, 0)  # Yellow selection ring
            glutWireSphere(animal.size + 10, 10, 10)
        
        # Draw different animal shapes based on type
        if "Cow" in animal.type:
            # Body
            glColor3f(0.9, 0.9, 0.9)  # White/cream color
            glPushMatrix()
            glScalef(1.5, 0.9, 0.8)
            glutSolidSphere(animal.size * 0.8, 20, 20)
            glPopMatrix()
            
            # Head
            glPushMatrix()
            glTranslatef(animal.size * 1.0, 0, animal.size * 0.3)
            glScalef(0.8, 0.6, 0.5)
            glutSolidSphere(animal.size * 0.5, 16, 16)
            
            # Eyes
            glColor3f(0.1, 0.1, 0.1)  # Black eyes
            glPushMatrix()
            glTranslatef(animal.size * 0.3, animal.size * 0.25, animal.size * 0.15)
            glutSolidSphere(animal.size * 0.07, 8, 8)
            glPopMatrix()
            
            glPushMatrix()
            glTranslatef(animal.size * 0.3, -animal.size * 0.25, animal.size * 0.15)
            glutSolidSphere(animal.size * 0.07, 8, 8)
            glPopMatrix()
            
            # Horns
            glColor3f(0.8, 0.8, 0.7)  # Horn color
            glPushMatrix()
            glTranslatef(0, animal.size * 0.3, animal.size * 0.35)
            glRotatef(45, 0, 1, 0)
            gluCylinder(gluNewQuadric(), animal.size * 0.08, animal.size * 0.02, animal.size * 0.4, 8, 8)
            glPopMatrix()
            
            glPushMatrix()
            glTranslatef(0, -animal.size * 0.3, animal.size * 0.35)
            glRotatef(-45, 0, 1, 0)
            gluCylinder(gluNewQuadric(), animal.size * 0.08, animal.size * 0.02, animal.size * 0.4, 8, 8)
            glPopMatrix()
            
            glPopMatrix()  # End head
            
            # Legs
            glColor3f(0.8, 0.8, 0.8)  # Leg color
            leg_positions = [
                (animal.size * 0.7, animal.size * 0.4, -animal.size * 0.8),
                (animal.size * 0.7, -animal.size * 0.4, -animal.size * 0.8),
                (-animal.size * 0.7, animal.size * 0.4, -animal.size * 0.8),
                (-animal.size * 0.7, -animal.size * 0.4, -animal.size * 0.8)
            ]
            
            for leg_x, leg_y, leg_z in leg_positions:
                glPushMatrix()
                glTranslatef(leg_x, leg_y, leg_z)
                glRotatef(90, 1, 0, 0)
                gluCylinder(gluNewQuadric(), animal.size * 0.12, animal.size * 0.1, animal.size * 0.8, 8, 8)
                glPopMatrix()
                
        elif "Horse" in animal.type:
            # Body
            glColor3f(0.6, 0.4, 0.2)  # Brown color
            glPushMatrix()
            glScalef(1.7, 0.8, 0.9)
            glutSolidSphere(animal.size * 0.7, 20, 20)
            glPopMatrix()
            
            # Neck
            glPushMatrix()
            glTranslatef(animal.size * 0.8, 0, animal.size * 0.3)
            glRotatef(45, 0, 1, 0)
            gluCylinder(gluNewQuadric(), animal.size * 0.25, animal.size * 0.2, animal.size * 0.7, 12, 8)
            
            # Head
            glTranslatef(0, 0, animal.size * 0.7)
            glRotatef(20, 0, 1, 0)
            glScalef(0.8, 0.5, 0.4)
            glutSolidSphere(animal.size * 0.5, 16, 16)
            glPopMatrix()
            
            # Legs
            glColor3f(0.5, 0.3, 0.2)  # Leg color
            leg_positions = [
                (animal.size * 0.7, animal.size * 0.3, -animal.size * 0.9),
                (animal.size * 0.7, -animal.size * 0.3, -animal.size * 0.9),
                (-animal.size * 0.7, animal.size * 0.3, -animal.size * 0.9),
                (-animal.size * 0.7, -animal.size * 0.3, -animal.size * 0.9)
            ]
            
            for leg_x, leg_y, leg_z in leg_positions:
                glPushMatrix()
                glTranslatef(leg_x, leg_y, leg_z)
                glRotatef(90, 1, 0, 0)
                gluCylinder(gluNewQuadric(), animal.size * 0.1, animal.size * 0.08, animal.size * 0.9, 8, 8)
                glPopMatrix()
                
            # Tail
            glColor3f(0.1, 0.1, 0.1)  # Black tail
            glPushMatrix()
            glTranslatef(-animal.size * 1.2, 0, animal.size * 0.2)
            glRotatef(-20, 0, 0, 1)
            gluCylinder(gluNewQuadric(), animal.size * 0.08, animal.size * 0.02, animal.size * 0.9, 8, 8)
            glPopMatrix()
            
        elif "Goat" in animal.type:
            # Body
            glColor3f(0.8, 0.8, 0.8)  # Light gray
            glPushMatrix()
            glScalef(1.3, 0.7, 0.8)
            glutSolidSphere(animal.size * 0.6, 16, 16)
            glPopMatrix()
            
            # Head
            glPushMatrix()
            glTranslatef(animal.size * 0.8, 0, animal.size * 0.3)
            glScalef(0.8, 0.6, 0.5)
            glutSolidSphere(animal.size * 0.4, 16, 16)
            
            # Beard
            glColor3f(0.7, 0.7, 0.7)
            glPushMatrix()
            glTranslatef(animal.size * 0.1, 0, -animal.size * 0.4)
            glRotatef(90, 1, 0, 0)
            glutSolidCone(animal.size * 0.2, animal.size * 0.4, 8, 8)
            glPopMatrix()
            
            # Horns
            glColor3f(0.4, 0.3, 0.2)
            
            # Left horn
            glPushMatrix()
            glTranslatef(-animal.size * 0.1, animal.size * 0.3, animal.size * 0.3)
            glRotatef(-30, 1, 0, 0)
            glRotatef(45, 0, 0, 1)
            gluCylinder(gluNewQuadric(), animal.size * 0.08, animal.size * 0.03, animal.size * 0.6, 8, 8)
            glPopMatrix()
            
            # Right horn
            glPushMatrix()
            glTranslatef(-animal.size * 0.1, -animal.size * 0.3, animal.size * 0.3)
            glRotatef(-30, 1, 0, 0)
            glRotatef(-45, 0, 0, 1)
            gluCylinder(gluNewQuadric(), animal.size * 0.08, animal.size * 0.03, animal.size * 0.6, 8, 8)
            glPopMatrix()
            
            glPopMatrix()  # End head
            
        elif "Sheep" in animal.type:
            # Fluffy body
            glColor3f(0.9, 0.9, 0.9)  # White wool
            glPushMatrix()
            
            # Add wool texture with small spheres
            for _ in range(20):
                wool_x = random.uniform(-animal.size * 0.5, animal.size * 0.5)
                wool_y = random.uniform(-animal.size * 0.4, animal.size * 0.4)
                wool_z = random.uniform(0, animal.size * 0.5)
                wool_size = random.uniform(animal.size * 0.15, animal.size * 0.25)
                
                glPushMatrix()
                glTranslatef(wool_x, wool_y, wool_z)
                glutSolidSphere(wool_size, 8, 8)
                glPopMatrix()
            
            glPopMatrix()
            
            # Head
            glColor3f(0.3, 0.3, 0.3)  # Black face
            glPushMatrix()
            glTranslatef(animal.size * 0.7, 0, animal.size * 0.5)
            glScalef(0.8, 0.5, 0.5)
            glutSolidSphere(animal.size * 0.35, 16, 16)
            glPopMatrix()
            
            # Legs
            glColor3f(0.3, 0.3, 0.3)  # Black legs
            leg_positions = [
                (animal.size * 0.5, animal.size * 0.3, -animal.size * 0.8),
                (animal.size * 0.5, -animal.size * 0.3, -animal.size * 0.8),
                (-animal.size * 0.5, animal.size * 0.3, -animal.size * 0.8),
                (-animal.size * 0.5, -animal.size * 0.3, -animal.size * 0.8)
            ]
            
            for leg_x, leg_y, leg_z in leg_positions:
                glPushMatrix()
                glTranslatef(leg_x, leg_y, leg_z)
                glRotatef(90, 1, 0, 0)
                gluCylinder(gluNewQuadric(), animal.size * 0.08, animal.size * 0.06, animal.size * 0.8, 8, 8)
                glPopMatrix()
                
        elif "Elephant" in animal.type:
            # Body
            glColor3f(0.6, 0.6, 0.6)  # Gray color
            glutSolidSphere(animal.size, 20, 20)
            
            # Trunk
            glPushMatrix()
            glTranslatef(animal.size*0.8, 0, 0)
            glRotatef(90, 0, 1, 0)
            # Make trunk move if eating
            if animal.is_eating:
                trunk_bend = 30 * math.sin(time.time() * 3)
                glRotatef(trunk_bend, 0, 0, 1)
            glColor3f(0.55, 0.55, 0.55)
            gluCylinder(gluNewQuadric(), animal.size*0.2, animal.size*0.1, animal.size*1.3, 12, 8)
            glPopMatrix()
            
            # Ears
            glPushMatrix()
            glTranslatef(0, animal.size*0.6, animal.size*0.4)
            glScalef(0.5, 1, 1)
            glColor3f(0.5, 0.5, 0.5)
            glutSolidSphere(animal.size*0.4, 12, 12)
            glPopMatrix()
            
            glPushMatrix()
            glTranslatef(0, -animal.size*0.6, animal.size*0.4)
            glScalef(0.5, 1, 1)
            glutSolidSphere(animal.size*0.4, 12, 12)
            glPopMatrix()
            
        else:
            # Default animal shape (for other animals)
            glColor3f(*animal.get_color())
            glutSolidSphere(animal.size, 20, 20)
            
            # Head for generic animal
            glPushMatrix()
            glTranslatef(animal.size*0.6, 0, animal.size*0.2)
            glutSolidSphere(animal.size*0.4, 12, 12)
            glPopMatrix()
        
        # Draw health bar above animal
        glTranslatef(0, 0, animal.size + 20)
        
        # Health bar background
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_QUADS)
        glVertex3f(-20, -5, 0)
        glVertex3f(20, -5, 0)
        glVertex3f(20, 5, 0)
        glVertex3f(-20, 5, 0)
        glEnd()
        
        # Health bar fill
        health_width = 40 * (animal.health / 100) - 20
        glColor3f(0, 1, 0)
        glBegin(GL_QUADS)
        glVertex3f(-20, -5, 0)
        glVertex3f(health_width, -5, 0)
        glVertex3f(health_width, 5, 0)
        glVertex3f(-20, 5, 0)
        glEnd()
        
        # Happiness indicator (above health bar)
        glTranslatef(0, 0, 10)
        happiness_width = 40 * (animal.happiness / 100) - 20
        glColor3f(1, 1, 0)  # Yellow for happiness
        glBegin(GL_QUADS)
        glVertex3f(-20, -5, 0)
        glVertex3f(happiness_width, -5, 0)
        glVertex3f(happiness_width, 5, 0)
        glVertex3f(-20, 5, 0)
        glEnd()
        
        # Show eating animation if animal is eating
        if animal.is_eating:
            glTranslatef(0, 0, 10)
            glColor3f(0.2, 0.8, 0.2)
            glutSolidSphere(5 + math.sin(time.time() * 5) * 2, 8, 8)
        
        glPopMatrix()  # End of animal drawing
    
    # Draw poachers
    for poacher in poachers:
        if not poacher.active:
            continue
            
        glPushMatrix()
        glTranslatef(poacher.pos[0], poacher.pos[1], poacher.pos[2])
        
        if poacher.captured:
            glColor3f(0.5, 0, 0.5)  # Purple for captured
        else:
            glColor3f(1, 0, 0)  # Red for active poacher
        
        # Draw poacher as cone
        glutSolidCone(20, 50, 10, 10)
        
        glPopMatrix()  # End of poacher drawing
    
    # Draw darts
    for dart in darts:
        if not dart.active:
            continue
            
        glPushMatrix()
        glTranslatef(dart.pos[0], dart.pos[1], dart.pos[2])
        glColor3f(0, 0, 1)  # Blue for darts
        
        # Point the dart in the direction of travel
        if dart.direction[0] != 0 or dart.direction[1] != 0:
            angle = math.atan2(dart.direction[1], dart.direction[0]) * 180 / math.pi
            glRotatef(angle, 0, 0, 1)
        
        # Draw dart as cylinder
        glRotatef(90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 2, 2, 20, 8, 1)
        
        glPopMatrix()  # End of dart drawing
    
    # Draw player
    draw_player()

def keyboardListener(key, x, y):
    global camera_mode, player_angle, game_paused, currency
    
    if key == b'\x1b':  # ESC key
        glutLeaveMainLoop()
    
    if key == b'p':  # Pause game
        game_paused = not game_paused
        
    # Switch camera mode
    if key == b'c':
        camera_mode = "first_person" if camera_mode == "third_person" else "third_person"
    
    # Rotate player left (A key)
    if key == b'a':
        player_angle += 5
    
    # Rotate player right (D key)
    if key == b'd':
        player_angle -= 5
    
    # Player movement
    if key == b'w':  # Forward
        angle_rad = player_angle * math.pi / 180
        player_pos[0] += math.cos(angle_rad) * player_speed
        player_pos[1] += math.sin(angle_rad) * player_speed
    
    if key == b's':  # Backward
        angle_rad = player_angle * math.pi / 180
        player_pos[0] -= math.cos(angle_rad) * player_speed
        player_pos[1] -= math.sin(angle_rad) * player_speed
    
    # Add food to feeding station
    if key == b'f':
        # Check if player is near a feeding station
        for i, habitat in enumerate(habitats):
            feeding_x = habitat["center"][0] + 50  # Feeding station offset
            feeding_y = habitat["center"][1] - 50
            
            dist = math.sqrt((player_pos[0] - feeding_x)**2 + 
                           (player_pos[1] - feeding_y)**2)
            
            if dist < 50:  # Close enough to feeding station
                if currency >= feed_cost:
                    FOOD_LEVEL[i] += 5  # Add food units
                    currency -= feed_cost
                    break
def specialKeyListener(key, x, y):
    global camera_pos, camera_angle
    
    # Camera rotation
    if key == GLUT_KEY_LEFT:
        camera_angle -= 5
    
    if key == GLUT_KEY_RIGHT:
        camera_angle += 5
    
    # Camera zoom
    if key == GLUT_KEY_UP:
        camera_pos = (camera_pos[0], camera_pos[1] - 20, camera_pos[2] - 20)
    
    if key == GLUT_KEY_DOWN:
        camera_pos = (camera_pos[0], camera_pos[1] + 20, camera_pos[2] + 20)

def mouseListener(button, state, x, y):
    global selected_animal_index, shoot_cooldown
    
    # Left mouse button for shooting
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        current_time = time.time()
        if shoot_cooldown <= current_time:
            shoot_cooldown = current_time + 1  # 1 second cooldown

            # Dart direction: player is facing along +Y rotated by player_angle
            angle_rad = math.radians(player_angle)
            direction = [-math.sin(angle_rad), math.cos(angle_rad), 0]

            # Dart position: match gun muzzle position visually
            dart_pos = [
                player_pos[0] + 30 * math.sin(angle_rad),  # Further forward
                player_pos[1] - 30 * math.cos(angle_rad),  # Further forward
                player_pos[2] + 31  # Match gun height (25 + 6)
            ]

            darts.append(Dart(dart_pos, direction))


    
    # Right mouse button for selecting animals
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        # Find closest animal to player within interaction range
        closest_animal = None
        closest_distance = interaction_range
        
        for i, animal in enumerate(animals):
            if animal.captured:
                continue
                
            dist = math.sqrt((player_pos[0] - animal.pos[0])**2 + 
                           (player_pos[1] - animal.pos[1])**2)
            
            if dist < closest_distance:
                closest_animal = i
                closest_distance = dist
        
        selected_animal_index = closest_animal

def setupCamera():
    """
    Configures the camera's projection and view settings.
    Uses a perspective projection and positions the camera to look at the target.
    """
    glMatrixMode(GL_PROJECTION)  # Switch to projection matrix mode
    glLoadIdentity()  # Reset the projection matrix
    # Set up a perspective projection (field of view, aspect ratio, near clip, far clip)
    gluPerspective(fovY, 1.25, 0.1, 1500) # Aspect ratio 1.25 (1000/800)
    glMatrixMode(GL_MODELVIEW)  # Switch to model-view matrix mode
    glLoadIdentity()  # Reset the model-view matrix

    # Position the camera based on mode
    if camera_mode == "third_person":
        cam_x = camera_pos[0]
        cam_y = camera_pos[1]
        cam_z = camera_pos[2]
        
        # Rotate camera based on camera_angle
        rotated_x = cam_x * math.cos(camera_angle * math.pi / 180) - cam_y * math.sin(camera_angle * math.pi / 180)
        rotated_y = cam_x * math.sin(camera_angle * math.pi / 180) + cam_y * math.cos(camera_angle * math.pi / 180)
        
        # Position the camera and set its orientation
        gluLookAt(rotated_x, rotated_y, cam_z,  # Camera position
                0, 0, 0,  # Look-at target
                0, 0, 1)  # Up vector (z-axis)
    else:  # First person
        # Calculate look-at point based on player angle
        angle_rad = player_angle * math.pi / 180
        look_x = player_pos[0] + 100 * math.cos(angle_rad)
        look_y = player_pos[1] + 100 * math.sin(angle_rad)
        look_z = player_pos[2] + 90

        # Position camera slightly above player's head
        gluLookAt(player_pos[0], player_pos[1], player_pos[2] + 40,
                look_x, look_y, look_z,
                0, 0, 1)

def reset_game():
    global animals, poachers, darts, game_time, currency, game_score, game_over, restart_timer
    global last_poacher_spawn_time, poacher_spawn_interval, FOOD_LEVEL, selected_animal_index
    
    # Reset game variables
    game_time = 0
    currency = 1000
    game_score = 0
    game_over = False
    restart_timer = None
    last_poacher_spawn_time = time.time()
    poacher_spawn_interval = 15
    selected_animal_index = None
    
    # Clear existing entities
    poachers = []
    darts = []
    
    # Reset feeding stations
    for i, habitat in enumerate(habitats):
        FOOD_LEVEL[i] = 0
    
    # Re-initialize animals
    animals = []
    for animal_type in animal_types:
        habitat = habitats[animal_type["habitat_index"]]
        pos_x = habitat["center"][0] + random.uniform(-150, 150)
        pos_y = habitat["center"][1] + random.uniform(-150, 150)
        animal = Animal((pos_x, pos_y, 20), animal_type["name"], habitat["color"], animal_type["size"])
        animal.habitat_pos = habitat["center"]
        animal.habitat_index = animal_type["habitat_index"]
        animal.dead = False
        animal.captured = False
        animal.health = 100
        animal.happiness = 100
        animals.append(animal)

def update_game():
    if game_paused:
        return
        
    global last_time, game_time, last_poacher_spawn_time, currency, darts, poacher_spawn_interval
    global game_over, restart_timer
    
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time
    
    # Check for game over
    if game_over:
        if restart_timer is None:
            restart_timer = current_time + 5  # Wait 5 seconds before restarting
        elif current_time >= restart_timer:
            reset_game()
        return
        
    # Check if all animals are dead or captured
    alive_animals = [a for a in animals if not a.dead and not a.captured]
    if not alive_animals:
        game_over = True
        return
    
    # Update game timer
    game_time += dt
    
    # Add currency over time
    if int(game_time) % 10 == 0 and int(game_time) > 0:  # Every 10 seconds
        currency += 25
    
    # Update all animals
    for animal in animals:
        animal.update(current_time)
    
    # Update all poachers
    for poacher in poachers:
        poacher.update()
    
    # Update all darts
    for dart in darts:
        dart.update()
    
    # Remove inactive darts
    darts = [d for d in darts if d.active]
    
    # Spawn new poachers
    if current_time - last_poacher_spawn_time > poacher_spawn_interval:
        # Find a valid animal target that's not already captured or dead
        valid_targets = [a for a in animals if not a.captured and not a.dead]
        
        if valid_targets:
            target_animal = random.choice(valid_targets)
            
            # Spawn poacher at edge of map
            spawn_side = random.randint(0, 3)  # 0=top, 1=right, 2=bottom, 3=left
            
            if spawn_side == 0:  # Top
                poacher_pos = [random.uniform(-GRID_LENGTH, GRID_LENGTH), GRID_LENGTH, 30]
            elif spawn_side == 1:  # Right
                poacher_pos = [GRID_LENGTH, random.uniform(-GRID_LENGTH, GRID_LENGTH), 30]
            elif spawn_side == 2:  # Bottom
                poacher_pos = [random.uniform(-GRID_LENGTH, GRID_LENGTH), -GRID_LENGTH, 30]
            else:  # Left
                poacher_pos = [-GRID_LENGTH, random.uniform(-GRID_LENGTH, GRID_LENGTH), 30]
                
            poachers.append(Poacher(poacher_pos, target_animal))
            last_poacher_spawn_time = current_time
            
            # Make poachers spawn more frequently as game progresses, but not too fast
            poacher_spawn_interval = max(8, 15 - game_time / 120)  # Slower scaling
def idle():
    """
    Idle function that runs continuously:
    - Updates game state
    - Triggers screen redraw for real-time updates.
    """
    update_game()
    glutPostRedisplay()

def showScreen():
    """
    Display function to render the game scene
    """
    # Clear color and depth buffers
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()  # Reset modelview matrix
    glViewport(0, 0, 1000, 800)  # Set viewport size
    
    # Enable lighting for 3D objects
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)

    setupCamera()  # Configure camera perspective

    # Remove grid drawing code and call draw_shapes directly
    draw_shapes()

    # Display habitat names in 2D
    for i, habitat in enumerate(habitats):
        x, y, z = habitat["center"]
        draw_text(x + 500, y + 400, habitat["name"])
        
        # Show food level for each habitat
        feeding_x = habitat["center"][0] + 50  # Feeding station offset
        feeding_y = habitat["center"][1] - 50
        
        # Convert to screen coordinates (rough approximation)
        screen_x = 500 + feeding_x / 2
        screen_y = 400 + feeding_y / 2
        
        # Draw food level text near feeding stations
        draw_text(screen_x, screen_y, f"Food: {FOOD_LEVEL[i]}")
    # Display game info
    draw_text(10, 770, f"Zoo Defender: Animal Rescue")
    draw_text(10, 740, f"Score: {game_score}  |  Currency: ${currency}")
    draw_text(10, 710, f"Game Time: {int(game_time)}s  |  Camera Mode: {camera_mode}")
    
    if game_paused:
        draw_text(400, 400, "GAME PAUSED - Press P to continue")
    
    if game_over:
        draw_text(350, 450, "GAME OVER - ALL ANIMALS LOST!")
        draw_text(350, 420, f"Final Score: {game_score}")
        
        # Show restart countdown
        if restart_timer:
            seconds_left = max(0, int(restart_timer - time.time()))
            draw_text(350, 390, f"Restarting in {seconds_left} seconds...")
    
    # Display controls
    draw_text(750, 770, "Controls:")
    draw_text(750, 740, "WASD - Move")
    draw_text(750, 710, "F - Feed selected animal ($50)")
    draw_text(750, 680, "Left click - Shoot dart")
    draw_text(750, 650, "Right click - Select animal")
    draw_text(750, 620, "C - Toggle camera")
    draw_text(750, 590, "P - Pause game")
    
    # Display selected animal info and animal statistics
    if selected_animal_index is not None and not game_over:
        animal = animals[selected_animal_index]
        draw_text(400, 50, f"Selected: {animal.type}")
        draw_text(400, 30, f"Health: {animal.health:.1f}%  Happiness: {animal.happiness:.1f}%")
        
    # Show animal count statistics
    living_count = sum(1 for a in animals if not a.dead and not a.captured)
    draw_text(10, 680, f"Animals: {living_count}/{len(animals)} alive")
    
    # Show warning if animals are hungry (average happiness < 50)
    avg_happiness = 0
    if living_count > 0:
        avg_happiness = sum(a.happiness for a in animals if not a.dead and not a.captured) / living_count
        if avg_happiness < 50:
            draw_text(10, 650, "WARNING: Animals are hungry!", GLUT_BITMAP_HELVETICA_18)
    # Swap buffers for smooth rendering (double buffering)
    glutSwapBuffers()
# Main function to set up OpenGL window and loop
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Double buffering, RGB color, depth test
    glutInitWindowSize(1000, 800)  # Window size
    glutInitWindowPosition(0, 0)  # Window position
    glutCreateWindow(b"Zoo Defender: Animal Rescue")  # Create the window

    # Enable depth testing and set up proper lighting
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glShadeModel(GL_SMOOTH)

    # Configure main light
    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 1.0, 0.0])  # Directional light from above
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.4, 0.4, 0.4, 1.0])   # Soft ambient light
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])   # Bright diffuse light
    glLightfv(GL_LIGHT0, GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])  # Moderate specular

    # Set up material properties
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 50.0)

    # Clear color to light blue
    glClearColor(0.7, 0.85, 1.0, 1.0)

    # Register callbacks
    glutDisplayFunc(showScreen)  # Register display function
    glutKeyboardFunc(keyboardListener)  # Register keyboard listener
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)  # Register the idle function

    # Start the main loop
    glutMainLoop()

if __name__ == "__main__":
    main()










