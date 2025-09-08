from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import sys, time, math, random

# Window
WIN_W = 1000
WIN_H = 800
fovY = 120.0
GRID_LENGTH = 600

# World
GROUND_HALF_X = 400.0
TILE_SIZE_Y = 600.0
NUM_TILES = 8
LOOP_LENGTH = TILE_SIZE_Y * NUM_TILES * 2.0

# Camera settings
camera_distance = 500.0 
camera_height = 600.0    
camera_angle = 0.0       
camera_tilt_x = 0.0     
camera_tilt_y = 0.0    
first_person_mode = False 

CAMERA_MOVE_SPEED = 20.0
CAMERA_ROTATE_SPEED = 5.0
CAMERA_HEIGHT_LIMIT = 1000.0  
CAMERA_ANGLE_LIMIT = 80.0    

# Ball 
BALL_RADIUS = 60.0  
ball_x = 0.0
ball_z = BALL_RADIUS
ball_vz = 0.0
roll_x = 0.0
roll_y = 0.0
is_jumping = False
ground_offset = 0.0

# Ball speed
game_start_time = time.time()
base_move_speed = 300.0  
current_move_speed = base_move_speed
speed_increase_rate = 0.5 
max_move_speed = 600.0

# Movement
key_left = False
key_right = False

# Clouds, flowers
NUM_CLOUDS = 8
clouds = []
GRASS_WIDTH = 80.0
FLOWER_COUNT_PER_SIDE = 120
flowers_left = []
flowers_right = []

# Obstacles
OBSTACLE_COUNT = 3
LANES = [-200, 0, 200]
obstacles = []

# Coins/powerups
coins = []
COIN_COUNT = 12
coins_collected = 0

# Powerup timers (seconds)
shield_time = 0.0  
speed_time = 0.0     

# Score / status
lives = 5
score = 0
distance_score = 0.0
game_over = False
game_start_time = 0.0

# GL state helpers
quad = None
_last_time = None

# Colors
SKY_COLOR = (0.52, 0.82, 0.92, 1.0)
GROUND_COLOR = (0.06, 0.45, 0.09)
GRASS_COLOR = (0.08, 0.55, 0.12)
FLOWER_COLORS = [
    (1.0, 0.2, 0.2),
    (1.0, 0.85, 0.0),
    (1.0, 0.5, 0.9),
    (0.6, 0.3, 1.0),
]

random.seed(0)

# Spin attack 
spin_time = 0.0
attack_power = 5       

# Special rotating-cylinder obstacles
special_obstacles = []       
last_special_spawn = time.time() - 25.0  
special_next_interval = random.randint(20, 30)
SPECIAL_SPAWN_MIN = 20
SPECIAL_SPAWN_MAX = 30

# Power-up timers
last_life_spawn = time.time() - 30.0
last_attack_spawn = time.time() - 20.0
last_speed_spawn = time.time() - 20.0
last_shield_spawn = time.time() - 30.0
life_spawn_interval = random.randint(30, 40)
attack_spawn_interval = random.randint(20, 30)
speed_spawn_interval = random.randint(20, 30)
shield_spawn_interval = random.randint(30, 40)

# Pop up text
bonus_text = ""
bonus_timer = 0.0
BONUS_DURATION = 2.0

# Cylinder wall obstacle
cylinder_walls = []
last_wall_spawn = time.time() - 20.0
wall_spawn_interval = 20.0

# Tall cylinder obstacle
tall_cylinders = []
last_tall_spawn = time.time() - 45.0
tall_spawn_interval = 12.0

# Growing/shrinking cube obstacle
growing_cubes = []
last_cube_spawn = time.time() - 70.0
cube_spawn_interval = 16.0

# Ball shrink feature
shrink_time = 0.0
SHRINK_DURATION = 2.0
game_over_shrink = 1.0

# Cheat mode
cheat_mode = False 

def clamp(x, a, b):
    return max(a, min(b, x))

def wrap_to_range(v, length):
    half = length / 2.0
    return ((v + half) % length) - half

def sphere_aabb_collision(sphere_pos, sphere_r, aabb_center, aabb_half):
    sp = sphere_pos
    min_corner = (
        aabb_center[0] - aabb_half[0],
        aabb_center[1] - aabb_half[1],
        aabb_center[2] - aabb_half[2],
    )
    max_corner = (
        aabb_center[0] + aabb_half[0],
        aabb_center[1] + aabb_half[1],
        aabb_center[2] + aabb_half[2],
    )
    cx = clamp(sp[0], min_corner[0], max_corner[0])
    cy = clamp(sp[1], min_corner[1], max_corner[1])
    cz = clamp(sp[2], min_corner[2], max_corner[2])
    dx = sp[0] - cx
    dy = sp[1] - cy
    dz = sp[2] - cz
    return (dx*dx + dy*dy + dz*dz) <= (sphere_r * sphere_r)

def init_clouds():
    clouds.clear()
    for _ in range(NUM_CLOUDS):
        c = {
            "x": random.uniform(-1400.0, 1400.0),
            "y": random.uniform(-LOOP_LENGTH/2, LOOP_LENGTH/2),
            "z": random.uniform(350.0, 520.0),
            "speed": random.uniform(8.0, 35.0),
            "scale": random.uniform(0.8, 1.6),
        }
        clouds.append(c)

def draw_cloud(c):
    x, y, z, s = c["x"], c["y"], c["z"], c["scale"]
    glColor3f(1.0, 1.0, 1.0)
    offsets = [(-0.8, 0.1), (0.8, 0.1), (0.0, 0.4), (0.0, 0.0)]
    for dx, dy in offsets:
        glPushMatrix()
        glTranslatef(x + dx*120*s, y + dy*80*s, z)
        q = gluNewQuadric()
        gluSphere(q, 60.0 * s, 16, 12)
        glPopMatrix()

def init_flowers():
    flowers_left.clear()
    flowers_right.clear()
    for _ in range(FLOWER_COUNT_PER_SIDE):
        wy = random.uniform(-LOOP_LENGTH/2, LOOP_LENGTH/2)
        x_off = random.uniform(-GRASS_WIDTH/2 + 8, GRASS_WIDTH/2 - 8)
        color = random.choice(FLOWER_COLORS)
        flowers_left.append({"world_y": wy, "x_off": -(GROUND_HALF_X+GRASS_WIDTH/2) + x_off, "color": color})
    for _ in range(FLOWER_COUNT_PER_SIDE):
        wy = random.uniform(-LOOP_LENGTH/2, LOOP_LENGTH/2)
        x_off = random.uniform(-GRASS_WIDTH/2 + 8, GRASS_WIDTH/2 - 8)
        color = random.choice(FLOWER_COLORS)
        flowers_right.append({"world_y": wy, "x_off": (GROUND_HALF_X+GRASS_WIDTH/2) + x_off, "color": color})

def draw_flower(x, y, size, color):
    glColor3f(0.05, 0.45, 0.05)
    glBegin(GL_LINES)
    glVertex3f(x, y, 0.0)
    glVertex3f(x, y, 10.0)
    glEnd()
    glColor3f(*color)
    glPushMatrix()
    glTranslatef(x, y, 14.0)
    q = gluNewQuadric()
    gluSphere(q, size, 8, 6)
    glPopMatrix()

def draw_ground():
    glColor3f(*GROUND_COLOR)
    size = TILE_SIZE_Y
    for i in range(-NUM_TILES, NUM_TILES+2):
        y0 = (i * size * 2.0) + (ground_offset % (size*2.0))
        y1 = y0 + size*2.0
        glBegin(GL_QUADS)
        glVertex3f(-GROUND_HALF_X, y0, 0.0)
        glVertex3f(GROUND_HALF_X, y0, 0.0)
        glVertex3f(GROUND_HALF_X, y1, 0.0)
        glVertex3f(-GROUND_HALF_X, y1, 0.0)
        glEnd()

def draw_grass_and_flowers():
    glColor3f(*GRASS_COLOR)
    left_x0 = -(GROUND_HALF_X + GRASS_WIDTH); left_x1 = -GROUND_HALF_X
    right_x0 = GROUND_HALF_X; right_x1 = GROUND_HALF_X + GRASS_WIDTH
    for i in range(-NUM_TILES, NUM_TILES+2):
        y0 = (i * TILE_SIZE_Y) + (ground_offset % (TILE_SIZE_Y * NUM_TILES))
        y1 = y0 + TILE_SIZE_Y
        glBegin(GL_QUADS)
        glVertex3f(left_x0, y0, 0.0)
        glVertex3f(left_x1, y0, 0.0)
        glVertex3f(left_x1, y1, 0.0)
        glVertex3f(left_x0, y1, 0.0)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(right_x0, y0, 0.0)
        glVertex3f(right_x1, y0, 0.0)
        glVertex3f(right_x1, y1, 0.0)
        glVertex3f(right_x0, y1, 0.0)
        glEnd()
    for f in flowers_left:
        wy = wrap_to_range(f["world_y"] + ground_offset, LOOP_LENGTH)
        draw_flower(f["x_off"], wy, 6.0, f["color"])
    for f in flowers_right:
        wy = wrap_to_range(f["world_y"] + ground_offset, LOOP_LENGTH)
        draw_flower(f["x_off"], wy, 6.0, f["color"])

def spawn_obstacle(init_y = -1000.0):
    x = random.choice(LANES)
    o = {"active": True, "passed": False, "x": x, "y": init_y}
    o["size_x"] = random.uniform(60.0, 100.0)
    o["size_y"] = o["size_x"]
    o["size_z"] = random.uniform(80.0, 170.0)
    o["center_z"] = o["size_z"] / 2.0
    o["color"] = (0.5, 0.5, 0.5)   
    obstacles.append(o)

def init_obstacles():
    obstacles.clear()
    for i in range(OBSTACLE_COUNT):
        spawn_obstacle(init_y = -1000.0 - i * 600.0)

def draw_obstacle(o):
    if not o["active"]:
        return
    glPushMatrix()
    glColor3f(*o["color"])
    glTranslatef(o["x"], o["y"], o["center_z"])
    glScalef(o["size_x"], o["size_y"], o["size_z"])
    glutSolidCube(1.0)
    glPopMatrix()



def spawn_special_cylinder(init_y=None):
    if init_y is None:
        init_y = -2500.0 - random.uniform(0.0, 500.0) 

    z_start = random.uniform(BALL_RADIUS, BALL_RADIUS + 200.0)
    
    o = {
        "active": True,
        "x": random.choice(LANES),
        "y": init_y,  
        "z": z_start, 
        "angle": 0.0,
        "angle_vel": 360.0,
        "shrinking": False,
        "shrink_timer": 0.0,
        "shrink_duration": 1.5,
        "shrink_scale": 1.0,
    }
    special_obstacles.append(o)


def draw_special_cylinder(o):
    if not (o["active"] or o["shrinking"]):
        return
    glPushMatrix()
    glTranslatef(o["x"], o["y"], o["z"])
    if o["active"] and not o["shrinking"]:
        glRotatef(o["angle"], 0.0, 1.0, 0.0)
    s = o.get("shrink_scale", 1.0)
    glScalef(s, s, s)
    glColor3f(0.9, 0.2, 0.2)
    q = gluNewQuadric()
    glPushMatrix()
    glTranslatef(0.0, 0.0, -40.0) 
    gluCylinder(q, 40.0, 40.0, 80.0, 20, 4)
    glPopMatrix()

    glPopMatrix()

def spawn_cylinder_wall(init_y=None):
    if init_y is None:
        init_y = -3000.0 
        
    wall = {
        "active": True,
        "y": init_y,
        "cylinders": [],
        "passed": False
    }
    
    total_width = GROUND_HALF_X * 2
    gap_size = 40.0 
    cylinder_width = (total_width - gap_size * 3) / 4 
    
    for i in range(4):
        x = -GROUND_HALF_X + gap_size/2 + (cylinder_width + gap_size) * i + cylinder_width/2
        cylinder = {
            "x": x,
            "base_radius": cylinder_width / 2,  
            "top_radius": cylinder_width / 4,   
            "height": 120.0,                    
        }
        wall["cylinders"].append(cylinder)
    
    cylinder_walls.append(wall)


def draw_cylinder_wall(wall):
    if not wall["active"]:
        return
        
    for cylinder in wall["cylinders"]:
        glPushMatrix()
        glTranslatef(cylinder["x"], wall["y"], 0) 
        
        glColor3f(0.93, 0.78, 0.17)
        
        q = gluNewQuadric()
        gluCylinder(q, cylinder["base_radius"], cylinder["top_radius"], 
                   cylinder["height"], 20, 4)
        
        glPopMatrix()


def spawn_tall_cylinder(init_y=None):
    if init_y is None:
        init_y = -3500.0 
    
    side = random.choice(["left", "right"])
    
    if side == "left":
        x = -GROUND_HALF_X / 2  
        base_radius = GROUND_HALF_X / 2 
    else:
        x = GROUND_HALF_X / 2  
        base_radius = GROUND_HALF_X / 2  
    
    cylinder = {
        "active": True,
        "x": x,
        "y": init_y,
        "base_radius": base_radius,
        "top_radius": base_radius / 2,  
        "height": 250.0,  
        "side": side,  
        "passed": False,
        "angle": 0.0, 
        "angle_vel": 180.0
    }
    
    tall_cylinders.append(cylinder)


def draw_tall_cylinder(cylinder):
    if not cylinder["active"]:
        return
        
    glPushMatrix()
    glTranslatef(cylinder["x"], cylinder["y"], 0)  
    glRotatef(cylinder["angle"], 1.0, 1.0, 0.0)
    
    glColor3f(0.0, 0.5, 0.5)
    
    q = gluNewQuadric()
    gluCylinder(q, cylinder["base_radius"], cylinder["top_radius"], 
               cylinder["height"], 24, 6)
    
    glPopMatrix()


def spawn_growing_cube(init_y=None):
    if init_y is None:
        init_y = -4000.0 
    
    cube = {
        "active": True,
        "x": 0.0,  
        "y": init_y,
        "z": ball_z + 100.0,  
        "size_x": GROUND_HALF_X * 2,  
        "size_y": 100.0,  
        "size_z": 120.0,  
        "min_size_z": 120.0,  
        "max_size_z": 250.0,  
        "growing": True,  
        "growth_speed": 50.0,  
        "passed": False
    }
    
    growing_cubes.append(cube)


def draw_growing_cube(cube):
    if not cube["active"]:
        return
        
    glPushMatrix()
    glTranslatef(cube["x"], cube["y"], cube["z"])
    
    glColor3f(0.84, 0.08, 0.72)
    
    glScalef(cube["size_x"], cube["size_y"], cube["size_z"])
    glutSolidCube(1.0)
    
    glPopMatrix()


def spawn_coin(init_y=None, coin_type="normal"):
    if init_y is None:
        init_y = -300.0 - random.uniform(0.0, 600.0)

    if coin_type == "normal":
        size = 16.0
    elif coin_type == "shield":
        size = 34.0
    elif coin_type == "speed":
        size = 34.0
    elif coin_type == "life":
        size = 28.0
    elif coin_type == "attack":
        size = 28.0

    c = {"active": True, "x": random.choice(LANES), "y": init_y,
         "z": BALL_RADIUS + 18.0, "r": size, "type": coin_type}
    coins.append(c)

def init_coins():
    coins.clear()
    for i in range(COIN_COUNT):
        spawn_coin(init_y = -200.0 - i * 180.0, coin_type="normal")

def draw_coin(c):
    if not c["active"]:
        return
    glPushMatrix()
    glTranslatef(c["x"], c["y"], c["z"])
    if c["type"] == "normal":
        glColor3f(1.0, 0.85, 0.0)  
    elif c["type"] == "shield":
        glColor3f(0.0, 1.0, 1.0)   
    elif c["type"] == "speed":
        glColor3f(1.0, 0.4, 0.0)  
    elif c["type"] == "life":
        glColor3f(0.2, 1.0, 0.2)  
    elif c["type"] == "attack":
        glColor3f(1.0, 0.2, 0.8)   
    q = gluNewQuadric()
    gluSphere(q, c["r"], 16, 12)
    glPopMatrix()

def spawn_speed_powerup():
    spawn_coin(init_y=-1800.0 - random.uniform(0.0, 400.0), coin_type="speed")

def spawn_shield_powerup():
    spawn_coin(init_y=-1800.0 - random.uniform(0.0, 400.0), coin_type="shield")

def spawn_life_powerup():
    spawn_coin(init_y=-1800.0 - random.uniform(0.0, 400.0), coin_type="life")

def spawn_attack_powerup():
    spawn_coin(init_y=-1800.0 - random.uniform(0.0, 400.0), coin_type="attack")


def draw_ball():
    glPushMatrix()
    glTranslatef(ball_x, 0.0, ball_z)
    glRotatef(-roll_x, 1.0, 0.0, 0.0)
    glRotatef(-roll_y, 0.0, 1.0, 0.0)

    if spin_time > 0.0:
        glRotatef(720.0 * (0.6 - spin_time), 0,0,1) 
        glScalef(1.4,1.4,1.4) 

    if shrink_time > 0.0:
        shrink_factor = 0.4 
        glScalef(shrink_factor, shrink_factor, shrink_factor)
    
    if game_over:
        glScalef(game_over_shrink, game_over_shrink, game_over_shrink)

    if game_over:
        glColor3f(0.0, 0.0, 0.0) 
    elif shield_time > 0.0:
        glColor3f(0.2, 0.4, 1.0)  
    else:
        glColor3f(0.85, 0.18, 0.18)  

    q = gluNewQuadric()
    gluSphere(q, BALL_RADIUS, 28, 20)

    glColor3f(1.0, 1.0, 1.0)
    band_h = BALL_RADIUS * 0.48
    glPushMatrix()
    glTranslatef(0.0, 0.0, -band_h / 2.0)
    q2 = gluNewQuadric()
    gluCylinder(q2, BALL_RADIUS * 1.05, BALL_RADIUS * 1.05, band_h, 36, 4)
    glPopMatrix()

    glPopMatrix()

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glPushAttrib(GL_ENABLE_BIT)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(1, 1, 1) 
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopAttrib()


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WIN_W / float(WIN_H), 0.1, 5000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if first_person_mode:
        fp_height = 150.0  
        fp_distance = 60.0  
        fp_look_down = -50.0  
        
        eye_x = ball_x
        eye_y = fp_distance 
        eye_z = ball_z + fp_height  
        
        look_x = ball_x
        look_y = -400.0  
        look_z = ball_z + fp_look_down  
        
        gluLookAt(eye_x, eye_y, eye_z, look_x, look_y, look_z, 0.0, 0.0, 1.0)
    else:
        rad = math.radians(camera_angle)
        eye_x = math.sin(rad) * camera_distance
        eye_y = math.cos(rad) * camera_distance
        eye_z = camera_height
        look_x = 0.0
        look_y = -200.0
        look_z = ball_z + 50.0
        gluLookAt(eye_x, eye_y, eye_z, look_x, look_y, look_z, 0.0, 0.0, 1.0)


def keyboard_down(key, x, y):
    global key_left, key_right, is_jumping, ball_vz, game_over
    global spin_time, attack_power, shrink_time, cheat_mode, bonus_text, bonus_timer, shield_time
    
    k = key.decode("utf-8") if isinstance(key, bytes) else key
    
    if k == '\x1b':
        sys.exit(0)
    if k in ('d','D'):     
        key_left = True
    if k in ('a','A'):     
        key_right = True
    if k in ('r','R'):
        restart_game()
    if k == ' ':
        if not is_jumping:
            is_jumping = True
            ball_vz = 800.0
    if k in ('f','F'):
        if spin_time <= 0.0 and attack_power > 0 and not game_over:
            spin_time = 0.6
            attack_power -= 1  
            bonus_text = "Spin Attack!"  
            bonus_timer = BONUS_DURATION

    if k in ('s','S'):  
        if shrink_time <= 0.0 and not game_over:
            shrink_time = SHRINK_DURATION

    if k in ('c','C'):  
        cheat_mode = not cheat_mode
        if cheat_mode:
            bonus_text = "CHEAT MODE: ON"
            bonus_timer = BONUS_DURATION
        else:
            bonus_text = "CHEAT MODE: OFF"
            bonus_timer = BONUS_DURATION
            shield_time = 0.0

def keyboard_up(key, x, y):
    global key_left, key_right
    
    k = key.decode("utf-8") if isinstance(key, bytes) else key
    
    if k in ('d','D'):      
        key_left = False
    if k in ('a','A'):     
        key_right = False


def specialKeyListener(key, x, y):
    global camera_height, camera_angle, camera_tilt_x, camera_tilt_y
    
    if key == GLUT_KEY_UP:  
        camera_height = min(camera_height + CAMERA_MOVE_SPEED, CAMERA_HEIGHT_LIMIT)
    elif key == GLUT_KEY_DOWN:  
        camera_height = max(camera_height - CAMERA_MOVE_SPEED, 100.0)
    elif key == GLUT_KEY_LEFT:  
        camera_angle = (camera_angle + CAMERA_ROTATE_SPEED) % 360.0
    elif key == GLUT_KEY_RIGHT:  
        camera_angle = (camera_angle - CAMERA_ROTATE_SPEED) % 360.0

def mouseListener(button, state, x, y):
    global first_person_mode
    
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person_mode = not first_person_mode


def restart_game():
    global lives, score, distance_score, ground_offset
    global obstacles, coins, ball_x, roll_x, roll_y, ball_z, ball_vz, is_jumping
    global game_over, game_start_time, shield_time, speed_time, coins_collected
    global attack_power, last_life_spawn, last_attack_spawn, last_speed_spawn, last_shield_spawn
    global life_spawn_interval, attack_spawn_interval, speed_spawn_interval, shield_spawn_interval
    global current_move_speed
    global current_move_speed, cylinder_walls, last_wall_spawn 
    global current_move_speed, cylinder_walls, last_wall_spawn, tall_cylinders, last_tall_spawn 
    global growing_cubes, last_cube_spawn, shrink_time
    global cheat_mode
    global game_over_shrink
    global camera_distance, camera_height, camera_angle, camera_tilt_x, camera_tilt_y, first_person_mode
    
    attack_power = 5
    lives = 5
    score = 0
    distance_score = 0.0
    ground_offset = 0.0
    ball_x = 0.0
    roll_x = roll_y = 0.0
    ball_z = BALL_RADIUS
    ball_vz = 0.0
    is_jumping = False
    cheat_mode = False
    obstacles.clear()
    coins.clear()
    cylinder_walls.clear()
    tall_cylinders.clear()
    growing_cubes.clear()  
    init_obstacles()
    init_coins()
    shield_time = 0.0
    speed_time = 0.0
    shrink_time = 0.0  
    coins_collected = 0
    game_over_shrink = 1.0 
    game_over = False
    game_start_time = time.time()
    current_move_speed = base_move_speed  
    
    last_speed_spawn = time.time() - 20.0
    last_shield_spawn = time.time() - 30.0
    last_life_spawn = time.time() - 30.0
    last_attack_spawn = time.time() - 20.0
    last_wall_spawn = time.time() - 20.0 
    last_tall_spawn = time.time() - 45.0
    last_cube_spawn = time.time() - 70.0
    speed_spawn_interval = random.randint(20, 30)
    shield_spawn_interval = random.randint(30, 40)
    life_spawn_interval = random.randint(30, 40)
    attack_spawn_interval = random.randint(20, 30)

    camera_distance = 500.0
    camera_height = 600.0
    camera_angle = 0.0
    camera_tilt_x = 0.0
    camera_tilt_y = 0.0
    first_person_mode = False


def idle():
    global _last_time, ground_offset, roll_x, roll_y, ball_x, ball_z, ball_vz, is_jumping
    global score, distance_score, lives, game_over, shield_time, speed_time, coins_collected
    global spin_time
    global last_special_spawn, special_next_interval, attack_power
    global bonus_text, bonus_timer
    global last_life_spawn, last_attack_spawn, last_speed_spawn, last_shield_spawn
    global life_spawn_interval, attack_spawn_interval, speed_spawn_interval, shield_spawn_interval
    global current_move_speed
    global last_wall_spawn, last_tall_spawn
    global shrink_time, last_cube_spawn
    global camera_distance, camera_height, camera_angle, camera_tilt_x, camera_tilt_y 
    global cheat_mode, game_over_shrink

    now = time.time()
    if _last_time is None:
        _last_time = now
    dt = clamp(now - _last_time, 0.0, 0.05)
    _last_time = now

    if not game_over:
        game_duration = now - game_start_time
        current_move_speed = min(base_move_speed + (speed_increase_rate * game_duration), max_move_speed)

    if game_over:
        if game_over_shrink > 0.3:
            game_over_shrink -= 0.5 * dt 
        else:
            game_over_shrink = 0.3 
        
        glutPostRedisplay()
        return 

    if not cheat_mode: 
        if shield_time > 0.0:
            shield_time -= dt
            if shield_time < 0.0:
                shield_time = 0.0
    else:
        shield_time = 9999.0  

    if speed_time > 0.0:
        speed_time -= dt
        if speed_time < 0.0:
            speed_time = 0.0

    if shrink_time > 0.0:
        shrink_time -= dt
        if shrink_time < 0.0:
            shrink_time = 0.0

    speed = current_move_speed
    if shield_time > 0.0:
        speed *= 5.0
    elif speed_time > 0.0:
        speed *= 2.0


    now = time.time()
    if now - last_special_spawn > special_next_interval:
        spawn_special_cylinder(init_y = -2200.0 - random.uniform(0.0, 400.0))
        last_special_spawn = now
        special_next_interval = random.randint(SPECIAL_SPAWN_MIN, SPECIAL_SPAWN_MAX)

    # always move forward
    ground_offset += speed * dt
    distance = speed * dt
    distance_score += distance * 0.1

    # forward rotation
    deg = (distance / (2.0 * math.pi * BALL_RADIUS)) * 360.0
    roll_x = (roll_x - deg) % 360.0


    if key_left:
        sx = current_move_speed * dt
        ball_x = clamp(ball_x - sx, -GROUND_HALF_X + BALL_RADIUS, GROUND_HALF_X - BALL_RADIUS)
        lat_deg = (sx / (2.0 * math.pi * BALL_RADIUS)) * 360.0
        roll_y = (roll_y + lat_deg) % 360.0
    if key_right:
        sx = current_move_speed * dt
        ball_x = clamp(ball_x + sx, -GROUND_HALF_X + BALL_RADIUS, GROUND_HALF_X - BALL_RADIUS)
        lat_deg = (sx / (2.0 * math.pi * BALL_RADIUS)) * 360.0
        roll_y = (roll_y - lat_deg) % 360.0

    # clamp horizontal
    edge = GROUND_HALF_X - BALL_RADIUS - 10.0
    ball_x = clamp(ball_x, -edge, edge)

    # jump
    if is_jumping:
        ball_z += ball_vz * dt
        ball_vz -= 1200.0 * dt
        if ball_z <= BALL_RADIUS:
            ball_z = BALL_RADIUS
            ball_vz = 0.0
            is_jumping = False

    # update clouds
    for c in clouds:
        c["x"] += c["speed"] * dt
        if c["x"] > 1600.0:
            c["x"] = -1600.0

    # update obstacles
    for o in obstacles:
        if o["active"]:
            o["y"] += speed * dt
    while sum(1 for o in obstacles if o["active"]) < OBSTACLE_COUNT:
        spawn_obstacle(init_y = -1000.0 - random.uniform(200.0, 900.0))

    for c in list(coins):
        if c["active"]:
            c["y"] += speed * dt
        if c["y"] > 420.0 and c["type"] == "normal":
            try:
                coins.remove(c)
            except ValueError:
                pass
            spawn_coin(init_y = -200.0 - random.uniform(0.0, 600.0), coin_type="normal")
    
    normal_coins_count = sum(1 for c in coins if c["type"] == "normal" and c["active"])
    while normal_coins_count < COIN_COUNT:
        spawn_coin(init_y = -200.0 - random.uniform(0.0, 600.0), coin_type="normal")
        normal_coins_count += 1

    for o in obstacles:
        if not o["active"]:
            continue
        if o["y"] > 300.0 and not o.get("passed", False):
            o["passed"] = True
            o["active"] = False
            score += 10
            continue
        if shield_time <= 0.0:
            sphere_pos = (ball_x, 0.0, ball_z)
            half = (o["size_x"]/2.0, o["size_y"]/2.0, o["size_z"]/2.0)
            center = (o["x"], o["y"], o["center_z"])
            if sphere_aabb_collision(sphere_pos, BALL_RADIUS, center, half):
                o["active"] = False
                lives -= 1
                if lives <= 0:
                    game_over = True

    # coin collection
    for c in list(coins):
        if not c["active"]:
            continue
        dx = ball_x - c["x"]
        dz = ball_z - c["z"]
        dist2 = dx*dx + dz*dz
        if dist2 <= (BALL_RADIUS + c["r"])**2 and abs(c["y"]) < 150.0:
            if c["type"] == "shield" and shield_time > 0.0:
                c["y"] -= 300.0
                continue
            if c["type"] == "speed" and speed_time > 0.0:
                c["y"] -= 300.0
                continue
            
            c["active"] = False
            coins_collected += 1
            
            if c["type"] == "normal":
                score += 5
            elif c["type"] == "shield":
                if shield_time <= 0.0:
                    shield_time = 3.0
                    speed_time = 3.0
                    bonus_text = "Shield Activated!"
                    bonus_timer = BONUS_DURATION
                    score += 10
            elif c["type"] == "speed":
                if speed_time <= 0.0:
                    speed_time = 3.0
                    bonus_text = "2x Speed Activated!"
                    bonus_timer = BONUS_DURATION
                    score += 10
            elif c["type"] == "life":
                if lives < 5:
                    lives += 1
                    bonus_text = "Life +1"
                    bonus_timer = BONUS_DURATION
                    score += 15
                else:
                    bonus_text = "Life Full!"
                    bonus_timer = BONUS_DURATION
            elif c["type"] == "attack":
                if attack_power < 5:
                    attack_power += 1
                    bonus_text = "AttackPower +1"
                    bonus_timer = BONUS_DURATION
                    score += 20
                else:
                    bonus_text = "Attack Full!"
                    bonus_timer = BONUS_DURATION

    coins[:] = [c for c in coins if c["active"] or c["type"] == "normal"]

    
    for o in list(special_obstacles):
        if o["active"]:
            o["y"] += speed * dt
            
            dx = ball_x - o["x"]      
            dy = 0 - o["y"]            
            dz = ball_z - o["z"]       
            
            max_move_x = 180.0 * dt
            if abs(dx) > 5.0:
                if abs(dx) > max_move_x:
                    o["x"] += max_move_x if dx > 0 else -max_move_x
                else:
                    o["x"] = ball_x
            
            max_move_z = 150.0 * dt
            if abs(dz) > 10.0:
                if abs(dz) > max_move_z:
                    o["z"] += max_move_z if dz > 0 else -max_move_z
                else:
                    o["z"] = ball_z
            
            max_move_y = 200.0 * dt  
            if abs(dy) > 50.0:  
                if abs(dy) > max_move_y:
                    o["y"] += max_move_y if dy > 0 else -max_move_y
                else:
                    o["y"] = 0  
            
            o["z"] = max(BALL_RADIUS + 20.0, o["z"])
            
            o["angle"] = (o["angle"] + o["angle_vel"] * dt) % 360.0
            
          
            if random.random() < 0.02: 
                print(f"Cylinder chasing: dx={dx:.1f}, dy={dy:.1f}, dz={dz:.1f}")
                print(f"  Ball: y=0, z={ball_z:.1f} | Cylinder: y={o['y']:.1f}, z={o['z']:.1f}")
            
            distance_x = abs(ball_x - o["x"])
            distance_z = abs(ball_z - o["z"])
            
            if abs(o["y"]) < 50.0 and distance_x < (BALL_RADIUS + 40.0) and distance_z < (BALL_RADIUS + 40.0):
                if spin_time > 0.0 and attack_power > 0:
                    o["shrinking"] = True
                    o["active"] = False
                    o["shrink_timer"] = o["shrink_duration"]
                    spin_time = 0.5
                    bonus_text = "Bonus +100"
                    bonus_timer = BONUS_DURATION
                    score += 100
                else:
                    if shield_time <= 0.0:
                        o["active"] = False
                        lives -= 2
                        if lives <= 0:
                            game_over = True
            
            if o["y"] > 200.0:
                try:
                    special_obstacles.remove(o)
                except ValueError:
                    pass
                    
        elif o["shrinking"]:
            o["shrink_timer"] -= dt
            if o["shrink_timer"] <= 0.0:
                try:
                    special_obstacles.remove(o)
                except ValueError:
                    pass
                continue
            frac = o["shrink_timer"] / max(0.0001, o["shrink_duration"])
            o["shrink_scale"] = max(0.05, frac)
            o["angle_vel"] = 0.0
       
    if now - last_speed_spawn > speed_spawn_interval:
        spawn_speed_powerup()
        last_speed_spawn = now
        speed_spawn_interval = random.randint(20, 30)
    
    if now - last_shield_spawn > shield_spawn_interval:
        spawn_shield_powerup()
        last_shield_spawn = now
        shield_spawn_interval = random.randint(30, 40)
    
    if now - last_life_spawn > life_spawn_interval:
        spawn_life_powerup()
        last_life_spawn = now
        life_spawn_interval = random.randint(30, 40)
    
    if now - last_attack_spawn > attack_spawn_interval:
        spawn_attack_powerup()
        last_attack_spawn = now
        attack_spawn_interval = random.randint(20, 30)

    if now - last_wall_spawn > wall_spawn_interval:
        spawn_cylinder_wall(init_y=-3000.0)
        last_wall_spawn = now


    for wall in list(cylinder_walls):
        if wall["active"]:
            wall["y"] += speed * dt
            
            if wall["y"] > 300.0 and not wall["passed"]:
                wall["passed"] = True
                wall["active"] = False
                score += 25 
            
            if abs(wall["y"]) < 100.0:  
                for cylinder in wall["cylinders"]:
                    dx = ball_x - cylinder["x"]
                    distance = abs(dx)
                    
                    if distance < (cylinder["base_radius"] + BALL_RADIUS):
                        if ball_z < cylinder["height"] + BALL_RADIUS:
                            if shield_time <= 0.0:
                                lives -= 1
                                wall["active"] = False
                                if lives <= 0:
                                    game_over = True
                            break  
            
            if wall["y"] > 500.0:
                cylinder_walls.remove(wall)


    if now - last_tall_spawn > tall_spawn_interval:
        spawn_tall_cylinder(init_y=-3500.0)
        last_tall_spawn = now


    for cylinder in list(tall_cylinders):
        if cylinder["active"]:
            cylinder["y"] += speed * dt
            cylinder["angle"] = (cylinder["angle"] + cylinder["angle_vel"] * dt) % 360.0

            if cylinder["y"] > 300.0 and not cylinder["passed"]:
                cylinder["passed"] = True
                cylinder["active"] = False
                score += 20  
            
            if abs(cylinder["y"]) < 100.0:  
                dx = ball_x - cylinder["x"]
                distance = abs(dx)
                
                if cylinder["side"] == "left" and ball_x < 0:  
                    if distance < (cylinder["base_radius"] + BALL_RADIUS):
                        if shield_time <= 0.0:
                            lives -= 1
                            cylinder["active"] = False
                            if lives <= 0:
                                game_over = True
                elif cylinder["side"] == "right" and ball_x > 0:  
                    if distance < (cylinder["base_radius"] + BALL_RADIUS):
                        if shield_time <= 0.0:
                            lives -= 1
                            cylinder["active"] = False
                            if lives <= 0:
                                game_over = True
            
            if cylinder["y"] > 500.0:
                tall_cylinders.remove(cylinder)


    if now - last_cube_spawn > cube_spawn_interval:
        spawn_growing_cube(init_y=-4000.0)
        last_cube_spawn = now

    for cube in list(growing_cubes):
        if cube["active"]:
            cube["y"] += speed * dt
            
            if cube["growing"]:
                cube["size_z"] += cube["growth_speed"] * dt
                if cube["size_z"] >= cube["max_size_z"]:
                    cube["size_z"] = cube["max_size_z"]
                    cube["growing"] = False
            else:
                cube["size_z"] -= cube["growth_speed"] * dt
                if cube["size_z"] <= cube["min_size_z"]:
                    cube["size_z"] = cube["min_size_z"]
                    cube["growing"] = True
            
            if cube["y"] > 300.0 and not cube["passed"]:
                cube["passed"] = True
                cube["active"] = False
                score += 30  
            
            if abs(cube["y"]) < 100.0:  
                half_width = cube["size_x"] / 2
                half_height = cube["size_z"] / 2
                cube_bottom = cube["z"] - half_height
                
                current_ball_radius = BALL_RADIUS * (0.4 if shrink_time > 0.0 else 1.0)
                ball_bottom = ball_z - current_ball_radius
                
                if abs(ball_x) < (current_ball_radius + half_width):
                    if ball_z + current_ball_radius > cube_bottom:
                        if shrink_time <= 0.0:
                            if shield_time <= 0.0:
                                lives -= 1
                                cube["active"] = False
                                if lives <= 0:
                                    game_over = True

    if bonus_timer > 0.0:
        bonus_timer -= dt
    if bonus_timer <= 0.0:
        bonus_text = ""

    if spin_time > 0.0:
        spin_time -= dt

    if first_person_mode and is_jumping:
        camera_tilt_y = min(10.0, camera_tilt_y + 5.0 * dt)
    else:
        camera_tilt_x *= 0.95
        camera_tilt_y *= 0.95

    glutPostRedisplay()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIN_W, WIN_H)

    setupCamera()

    glPointSize(20)
    glBegin(GL_POINTS)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0.0)
    glEnd()

    # floor pattern
    glBegin(GL_QUADS)
    glColor3f(1.0, 1.0, 1.0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0.0)
    glVertex3f(0.0, GRID_LENGTH, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(-GRID_LENGTH, 0.0, 0.0)

    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0.0)
    glVertex3f(0.0, -GRID_LENGTH, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(GRID_LENGTH, 0.0, 0.0)

    glColor3f(0.7, 0.5, 0.95)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0.0)
    glVertex3f(-GRID_LENGTH, 0.0, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, -GRID_LENGTH, 0.0)

    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0.0)
    glVertex3f(GRID_LENGTH, 0.0, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, GRID_LENGTH, 0.0)
    glEnd()

    # draw world
    draw_ground()
    draw_grass_and_flowers()

    for o in obstacles:
        draw_obstacle(o)
    for c in clouds:
        draw_cloud(c)
    for c in coins:
        draw_coin(c)

    for so in special_obstacles:
        draw_special_cylinder(so)

    draw_ball()

    total_score = score + int(distance_score)
    draw_text(10, WIN_H - 24, f"Lives: {lives}/5   Score: {total_score}   Distance: {int(distance_score)}")
    draw_text(10, WIN_H - 50, f"Coins: {coins_collected}")
    draw_text(10, WIN_H - 130, f"AttackPower: {attack_power}/5")

    if shield_time > 0:
        draw_text(10, WIN_H - 75, f"Shield Active: {shield_time:.1f}s")
        draw_text(10, WIN_H - 100, f"5x Speed Active: {speed_time:.1f}s")
    if speed_time > 0 and shield_time <= 0:
        draw_text(10, WIN_H - 100, f"2x Speed Active: {speed_time:.1f}s")

    if bonus_text:
        draw_text(WIN_W//2 - 50, WIN_H//2 + 50, bonus_text)

    if game_over:
        draw_text(WIN_W // 2 - 100, WIN_H // 2, "GAME OVER - Press R to Restart")
    else:
        speed_time_left = max(0, speed_spawn_interval - (time.time() - last_speed_spawn))
        shield_time_left = max(0, shield_spawn_interval - (time.time() - last_shield_spawn))
        life_time_left = max(0, life_spawn_interval - (time.time() - last_life_spawn))
        attack_time_left = max(0, attack_spawn_interval - (time.time() - last_attack_spawn))
        draw_text(10, WIN_H - 160, f"Next Speed: {speed_time_left:.1f}s")
        draw_text(10, WIN_H - 185, f"Next Shield: {shield_time_left:.1f}s")
        draw_text(10, WIN_H - 210, f"Next Life: {life_time_left:.1f}s")
        draw_text(10, WIN_H - 235, f"Next Attack: {attack_time_left:.1f}s")
        draw_text(10, WIN_H - 260, f"Speed: {current_move_speed:.1f}")

        if shrink_time > 0:
            draw_text(10, WIN_H - 285, f"Shrunk: {shrink_time:.1f}s")
        else:
            draw_text(10, WIN_H - 285, "Press S to Shrink")

    for wall in cylinder_walls:
        draw_cylinder_wall(wall)

    for cylinder in tall_cylinders:
        draw_tall_cylinder(cylinder)

    for cube in growing_cubes:
        draw_growing_cube(cube)

    if cheat_mode:
        draw_text(10, WIN_H - 310, "CHEAT MODE: ON")
        draw_text(10, WIN_H - 330, "Infinite Shield")

    glutSwapBuffers()

def main():
    global quad, _last_time, game_start_time
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"3D Ball Runner!")

    glClearColor(SKY_COLOR[0], SKY_COLOR[1], SKY_COLOR[2], SKY_COLOR[3])

    quad = gluNewQuadric()

    init_clouds()
    init_flowers()
    init_obstacles()
    init_coins()

    _last_time = time.time()
    game_start_time = _last_time

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboard_down)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()