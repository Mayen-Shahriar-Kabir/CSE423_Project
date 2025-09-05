from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import sys
import time
import math
import random

# =================================================
# Rolling Ball Runner - Full Version (Sphere Clouds)
# =================================================

WIN_W = 1000
WIN_H = 800

camera_pos = (0.0, 400.0, 600.0)
fovY = 120.0

GROUND_HALF_X = 400.0
TILE_SIZE_Y = 600.0
NUM_TILES = 8          # Increased number of tiles for longer distance
LOOP_LENGTH = TILE_SIZE_Y * NUM_TILES * 2.0

BALL_RADIUS = 80.0
ball_x = 0.0
ball_z = BALL_RADIUS
roll_x = 0.0
roll_y = 0.0

MOVE_SPEED = 300.0
ground_offset = 0.0

key_forward = False
key_left = False
key_right = False

NUM_CLOUDS = 8
clouds = []

GRASS_WIDTH = 80.0
FLOWER_COUNT_PER_SIDE = 120
flowers_left = []
flowers_right = []

OBSTACLE_COUNT = 5
LANES = [-200, 0, 200]  # 3 lanes for X positions
obstacles = []

lives = 5
score = 0
distance_score = 0.0
game_over = False
game_start_time = 0.0  # Added to track game start

quad = None
_last_time = None

SKY_COLOR = (0.52, 0.82, 0.92, 1.0)
GROUND_COLOR = (0.06, 0.45, 0.09)
GRASS_COLOR = (0.08, 0.55, 0.12)
FLOWER_COLORS = [(1.0, 0.2, 0.2), (1.0, 0.85, 0.0), (1.0, 0.5, 0.9), (0.6, 0.3, 1.0)]

random.seed(0)

# ------------------------------
# Utility Functions
# ------------------------------

def clamp(x, a, b):
    return max(a, min(b, x))

def wrap_to_range(v, length):
    half = length / 2.0
    return ((v + half) % length) - half

def sphere_aabb_collision(sphere_pos, sphere_r, aabb_center, aabb_half):
    sp = sphere_pos
    min_corner = (aabb_center[0]-aabb_half[0], aabb_center[1]-aabb_half[1], aabb_center[2]-aabb_half[2])
    max_corner = (aabb_center[0]+aabb_half[0], aabb_center[1]+aabb_half[1], aabb_center[2]+aabb_half[2])
    cx = clamp(sp[0], min_corner[0], max_corner[0])
    cy = clamp(sp[1], min_corner[1], max_corner[1])
    cz = clamp(sp[2], min_corner[2], max_corner[2])
    dx = sp[0]-cx; dy = sp[1]-cy; dz = sp[2]-cz
    return (dx*dx + dy*dy + dz*dz) <= (sphere_r * sphere_r)

# ------------------------------
# Clouds (Sphere Version)
# ------------------------------

def init_clouds():
    clouds.clear()
    for _ in range(NUM_CLOUDS):
        c = {"x":random.uniform(-1400.0,1400.0),
             "y":random.uniform(-LOOP_LENGTH/2, LOOP_LENGTH/2),
             "z":random.uniform(350.0,520.0),
             "speed":random.uniform(10.0,45.0),
             "scale":random.uniform(0.8,1.6)}
        clouds.append(c)

def draw_cloud(c):
    x, y, z, s = c["x"], c["y"], c["z"], c["scale"]
    glColor3f(1.0,1.0,1.0)
    # Use spheres to represent a cloud
    offsets = [(-0.8,0.1), (0.8,0.1), (0.0,0.4), (0.0,0.0)]
    for dx, dy in offsets:
        glPushMatrix()
        glTranslatef(x+dx*120*s, y+dy*80*s, z)
        glutSolidSphere(60*s, 20, 20)
        glPopMatrix()

# ------------------------------
# Grass and Flowers
# ------------------------------

def init_flowers():
    flowers_left.clear(); flowers_right.clear()
    for _ in range(FLOWER_COUNT_PER_SIDE):
        wy = random.uniform(-LOOP_LENGTH/2, LOOP_LENGTH/2)
        x_off = random.uniform(-GRASS_WIDTH/2+8, GRASS_WIDTH/2-8)
        color = random.choice(FLOWER_COLORS)
        flowers_left.append({"world_y":wy, "x_off":-(GROUND_HALF_X+GRASS_WIDTH/2)+x_off, "color":color})
    for _ in range(FLOWER_COUNT_PER_SIDE):
        wy = random.uniform(-LOOP_LENGTH/2, LOOP_LENGTH/2)
        x_off = random.uniform(-GRASS_WIDTH/2+8, GRASS_WIDTH/2-8)
        color = random.choice(FLOWER_COLORS)
        flowers_right.append({"world_y":wy, "x_off":(GROUND_HALF_X+GRASS_WIDTH/2)+x_off, "color":color})

def draw_flower(x,y,size,color):
    glColor3f(0.05,0.45,0.05)
    glBegin(GL_LINES)
    glVertex3f(x,y,0.0)
    glVertex3f(x,y,10.0)
    glEnd()
    glColor3f(*color)
    glPushMatrix()
    glTranslatef(x,y,14.0)
    glutSolidSphere(size,8,8)
    glPopMatrix()

def draw_grass_and_flowers():
    glColor3f(*GRASS_COLOR)
    left_x0 = -(GROUND_HALF_X+GRASS_WIDTH); left_x1=-GROUND_HALF_X
    right_x0 = GROUND_HALF_X; right_x1=GROUND_HALF_X+GRASS_WIDTH
    for i in range(-NUM_TILES, NUM_TILES+2):
        y0=(i*TILE_SIZE_Y)+(ground_offset % (TILE_SIZE_Y*NUM_TILES))
        y1=y0+TILE_SIZE_Y
        glBegin(GL_QUADS)
        glVertex3f(left_x0,y0,0.0)
        glVertex3f(left_x1,y0,0.0)
        glVertex3f(left_x1,y1,0.0)
        glVertex3f(left_x0,y1,0.0)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(right_x0,y0,0.0)
        glVertex3f(right_x1,y0,0.0)
        glVertex3f(right_x1,y1,0.0)
        glVertex3f(right_x0,y1,0.0)
        glEnd()
    for f in flowers_left:
        wy = wrap_to_range(f["world_y"]+ground_offset, LOOP_LENGTH)
        draw_flower(f["x_off"], wy, 6.0, f["color"])
    for f in flowers_right:
        wy = wrap_to_range(f["world_y"]+ground_offset, LOOP_LENGTH)
        draw_flower(f["x_off"], wy, 6.0, f["color"])

# ------------------------------
# Ground
# ------------------------------

def draw_ground():
    glColor3f(*GROUND_COLOR)
    size=TILE_SIZE_Y
    for i in range(-NUM_TILES, NUM_TILES+2):
        y0=(i*size*2.0)+(ground_offset % (size*2.0))
        y1=y0+size*2.0
        glBegin(GL_QUADS)
        glVertex3f(-GROUND_HALF_X,y0,0.0)
        glVertex3f(GROUND_HALF_X,y0,0.0)
        glVertex3f(GROUND_HALF_X,y1,0.0)
        glVertex3f(-GROUND_HALF_X,y1,0.0)
        glEnd()

# ------------------------------
# Ball
# ------------------------------

def draw_ball():
    glPushMatrix()
    glTranslatef(ball_x, 0.0, ball_z)
    glRotatef(roll_x,1.0,0.0,0.0)
    glRotatef(roll_y,0.0,1.0,0.0)
    glColor3f(0.85,0.18,0.18)
    gluSphere(quad,BALL_RADIUS,36,28)
    glColor3f(1.0,1.0,1.0)
    band_height = BALL_RADIUS*0.48
    glPushMatrix()
    glTranslatef(0.0,0.0,-band_height/2.0)
    gluCylinder(quad,BALL_RADIUS*1.05,BALL_RADIUS*1.05,band_height,40,4)
    glPopMatrix()
    glPopMatrix()

# ------------------------------
# Obstacles
# ------------------------------

def init_obstacles():
    obstacles.clear()
    # Start obstacles much further away to avoid initial collision
    for i in range(OBSTACLE_COUNT):
        spawn_obstacle(init_y=-500.0 - i*400.0)  # Changed from -i*400.0 to ensure they're far away

def draw_obstacle(o):
    if not o["active"]: return
    glPushMatrix()
    glColor3f(*o["color"])
    glTranslatef(o["x"], o["y"], o["center_z"])
    if o["type"]=="cube":
        glPushMatrix()
        glScalef(o["size_x"], o["size_y"], o["size_z"])
        glutSolidCube(1.0)
        glPopMatrix()
    elif o["type"]=="cyl":
        glPushMatrix()
        glTranslatef(0,0,-o["size_z"]/2.0)
        gluCylinder(quad,o["radius"],o["radius"],o["size_z"],20,3)
        glPopMatrix()
    else:
        glPushMatrix()
        glScalef(o["size_x"], o["size_y"], o["size_z"]/2.0)
        glutSolidCube(1.0)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0,0,o["size_z"]/4.0)
        gluCylinder(quad,o["radius"],o["radius"],o["size_z"]/2.0,18,2)
        glPopMatrix()
    glPopMatrix()

def spawn_obstacle(init_y=-800.0):
    # Ensure at least 1 lane free
    lane_counts = {lane:0 for lane in LANES}
    for ob in obstacles:
        if ob["active"]: lane_counts[ob["x"]]+=1
    possible_lanes=[lane for lane in LANES if lane_counts[lane]<2]
    free_lanes=[lane for lane in LANES if lane not in [o["x"] for o in obstacles if o["active"]]]
    if free_lanes:
        x=random.choice(free_lanes)
    else:
        x=random.choice(possible_lanes)
    o={"active":True,"passed":False,"x":x,"y":init_y}
    o["type"]=random.choice(["cube","cyl","mixed"])
    o["size_x"]=random.uniform(50,140)
    o["size_y"]=o["size_x"]
    o["size_z"]=random.uniform(50,200)
    o["center_z"]=o["size_z"]/2.0
    o["radius"]=o.get("size_x",40.0)/2.0
    o["color"]=(random.random(),random.random(),random.random())
    obstacles.append(o)

# ------------------------------
# Camera
# ------------------------------

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WIN_W/float(WIN_H), 0.1, 5000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    x,y,z=camera_pos
    gluLookAt(x,y,z,0.0,0.0,0.0,0.0,0.0,1.0)

# ------------------------------
# OpenGL Init
# ------------------------------

def init_gl():
    global quad, _last_time, game_start_time
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE|GLUT_RGB|GLUT_DEPTH)
    glutInitWindowSize(WIN_W,WIN_H)
    glutCreateWindow(b"Rolling Ball Runner")
    glClearColor(*SKY_COLOR)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glEnable(GL_NORMALIZE)
    quad=gluNewQuadric()
    gluQuadricNormals(quad,GLU_SMOOTH)
    init_clouds()
    init_flowers()
    init_obstacles()
    _last_time=time.time()
    game_start_time=time.time()  # Track when game starts

def reshape(w,h):
    global WIN_W,WIN_H
    WIN_W=max(1,w)
    WIN_H=max(1,h)
    glViewport(0,0,WIN_W,WIN_H)

# ------------------------------
# Keyboard
# ------------------------------

def keyboard_down(key,x,y):
    global key_forward,key_left,key_right,game_over
    k=key.decode("utf-8") if isinstance(key,bytes) else key
    if k=='\x1b': sys.exit(0)
    if k in ('w','W') and not game_over: key_forward=True
    if k in ('d','D'): key_left=True
    if k in ('a','A'): key_right=True
    if k in ('r','R'): restart_game()

def keyboard_up(key,x,y):
    global key_forward,key_left,key_right
    k=key.decode("utf-8") if isinstance(key,bytes) else key
    if k in ('w','W'): key_forward=False
    if k in ('d','D'): key_left=False
    if k in ('a','A'): key_right=False

def restart_game():
    global lives,score,distance_score,ground_offset,obstacles,ball_x,roll_x,roll_y,game_over,game_start_time
    lives=5; score=0; distance_score=0.0
    ground_offset=0.0; ball_x=0.0; roll_x=0.0; roll_y=0.0
    obstacles.clear()
    init_obstacles()
    game_over=False
    game_start_time=time.time()  # Reset game start time

# ------------------------------
# Idle & Update
# ------------------------------

def idle():
    global _last_time,ground_offset,roll_x,roll_y,ball_x,score,distance_score,lives,game_over
    now=time.time()
    dt=clamp(now-_last_time,0.0,0.05)
    _last_time=now
    if game_over:
        glutPostRedisplay(); return

    # Add a small grace period at the start to avoid immediate collisions
    grace_period = 1.0  # 1 second grace period
    in_grace_period = (now - game_start_time) < grace_period

    if key_forward:
        ground_offset+=MOVE_SPEED*dt
        distance=MOVE_SPEED*dt
        deg=(distance/(2.0*math.pi*BALL_RADIUS))*360.0
        roll_x=(roll_x+deg)%360.0
        distance_score+=distance*0.1
        for o in obstacles:
            if o["active"]: o["y"]+=MOVE_SPEED*dt
        for c in clouds:
            c["x"]+=c["speed"]*0.05*dt*60.0

    if key_left:
        ball_x-=MOVE_SPEED*dt
        deg=(MOVE_SPEED*dt/(2.0*math.pi*BALL_RADIUS))*360.0
        roll_y=(roll_y-deg)%360.0
    if key_right:
        ball_x+=MOVE_SPEED*dt
        deg=(MOVE_SPEED*dt/(2.0*math.pi*BALL_RADIUS))*360.0
        roll_y=(roll_y+deg)%360.0

    edge=GROUND_HALF_X-BALL_RADIUS-10.0
    ball_x=clamp(ball_x,-edge,edge)

    for c in clouds:
        c["x"]+=c["speed"]*dt
        if c["x"]>1600.0: c["x"]=-1600.0

    while sum(1 for o in obstacles if o["active"])<OBSTACLE_COUNT:
        spawn_obstacle()

    # Only check collisions after grace period
    if not in_grace_period:
        for o in obstacles:
            if not o["active"]: continue
            if o["y"]>300.0 and not o["passed"]:
                score+=10; o["passed"]=True; o["active"]=False
                continue
            sphere_pos=(ball_x,0.0,ball_z)
            half=(o.get("size_x",50)/2.0,o.get("size_y",50)/2.0,o.get("size_z",50)/2.0)
            center=(o["x"],o["y"],o["center_z"])
            if sphere_aabb_collision(sphere_pos,BALL_RADIUS,center,half):
                o["active"]=False
                lives-=1
                if lives<=0: game_over=True

    glutPostRedisplay()

# ------------------------------
# Text
# ------------------------------

def draw_text(x,y,text,font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1.0,1.0,1.0)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0,WIN_W,0,WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x,y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ------------------------------
# Display
# ------------------------------

def display():
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glViewport(0,0,WIN_W,WIN_H)
    setupCamera()
    draw_ground()
    draw_grass_and_flowers()
    for o in obstacles: draw_obstacle(o)
    for c in clouds: draw_cloud(c)
    draw_ball()
    total_score=score+int(distance_score)
    draw_text(10,WIN_H-24,f"Lives: {lives}   Score: {total_score}   Distance: {int(distance_score)}")
    if game_over: draw_text(WIN_W//2-80,WIN_H//2,"GAME OVER - Press R to Restart")
    glutSwapBuffers()

# ------------------------------
# Main
# ------------------------------

def main():
    global _last_time, game_start_time
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE|GLUT_RGB|GLUT_DEPTH)
    glutInitWindowSize(WIN_W,WIN_H)
    glutCreateWindow(b"Rolling Ball Runner")
    glClearColor(*SKY_COLOR)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glEnable(GL_NORMALIZE)
    global quad; quad=gluNewQuadric(); gluQuadricNormals(quad,GLU_SMOOTH)
    init_clouds()
    init_flowers()
    init_obstacles()
    _last_time=time.time()
    game_start_time=time.time()  # Initialize game start time
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutReshapeFunc(lambda w,h: (globals().__setitem__('WIN_W', max(1,w)), globals().__setitem__('WIN_H', max(1,h)), glViewport(0,0,WIN_W,WIN_H)))
    glutKeyboardFunc(keyboard_down)
    glutKeyboardUpFunc(keyboard_up)
    glutMainLoop()

if __name__=="__main__":
    main()