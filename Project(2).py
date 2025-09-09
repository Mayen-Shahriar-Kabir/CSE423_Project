from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import sys, time, math, random

# =================================================
# Rolling Ball Runner - Template-constrained final
# - Uses only GL/GLU/GLUT drawing functions found in your template
# - shield makes ball blue and gives 5x speed for 3s
# - speed coin gives 2x speed for 3s
# - identical power-ups while active are ignored (not counted)
# =================================================

# Window / camera
WIN_W = 1000
WIN_H = 800
camera_pos = (0.0, 400.0, 600.0)
fovY = 120.0
GRID_LENGTH = 600

# World
GROUND_HALF_X = 400.0
TILE_SIZE_Y = 600.0
NUM_TILES = 8
LOOP_LENGTH = TILE_SIZE_Y * NUM_TILES * 2.0

# Ball / player
BALL_RADIUS = 60.0   # smaller ball
ball_x = 0.0
ball_z = BALL_RADIUS
ball_vz = 0.0
roll_x = 0.0
roll_y = 0.0
is_jumping = False

# Movement
MOVE_SPEED = 300.0
ground_offset = 0.0

# Input flags
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
shield_time = 0.0    # shield + 5x speed for 3s
speed_time = 0.0     # speed 2x for 3s

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

# ------------------------------
# Utility
# ------------------------------
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

# ------------------------------
# Clouds & flowers
# ------------------------------
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
        # use gluSphere (template allowed)
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

# ------------------------------
# Ground & grass
# ------------------------------
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

# ------------------------------
# Obstacles (cuboids, grey)
# ------------------------------
def spawn_obstacle(init_y = -1000.0):
    x = random.choice(LANES)
    o = {"active": True, "passed": False, "x": x, "y": init_y}
    o["size_x"] = random.uniform(60.0, 140.0)
    o["size_y"] = o["size_x"]
    o["size_z"] = random.uniform(80.0, 200.0)
    o["center_z"] = o["size_z"] / 2.0
    o["color"] = (0.5, 0.5, 0.5)   # grey
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

# ------------------------------
# Coins (normal / shield / speed)
# ------------------------------
def spawn_coin(init_y=None):
    if init_y is None:
        init_y = -300.0 - random.uniform(0.0, 600.0)

    r = random.random()
    if r < 0.9:        # 90% normal
        ctype = "normal"; size = 16.0
    elif r < 0.05:     # 5% speed
        ctype = "speed"; size = 34.0
    else:              # 5% shield
        ctype = "shield"; size = 34.0

    c = {"active": True, "x": random.choice(LANES), "y": init_y,
         "z": BALL_RADIUS + 18.0, "r": size, "type": ctype}
    coins.append(c)
def init_coins():
    coins.clear()
    for i in range(COIN_COUNT):
        spawn_coin(init_y = -200.0 - i * 180.0)

def draw_coin(c):
    if not c["active"]:
        return
    glPushMatrix()
    glTranslatef(c["x"], c["y"], c["z"])
    if c["type"] == "normal":
        glColor3f(1.0, 0.85, 0.0)
    elif c["type"] == "shield":
        glColor3f(0.0, 1.0, 1.0)
    else:
        glColor3f(1.0, 0.4, 0.0)
    q = gluNewQuadric()
    gluSphere(q, c["r"], 16, 12)
    glPopMatrix()

# ------------------------------
# Ball drawing (white band; blue when shield)
# ------------------------------
def draw_ball():
    glPushMatrix()
    glTranslatef(ball_x, 0.0, ball_z)
    # invert visual rotation so it looks forward
    glRotatef(-roll_x, 1.0, 0.0, 0.0)
    glRotatef(-roll_y, 0.0, 1.0, 0.0)

    # color based on shield
    if shield_time > 0.0:
        glColor3f(0.2, 0.4, 1.0)  # blue when shield active
    else:
        glColor3f(0.85, 0.18, 0.18)  # normal red

    q = gluNewQuadric()
    gluSphere(q, BALL_RADIUS, 28, 20)

    # white band using cylinder
    glColor3f(1.0, 1.0, 1.0)
    band_h = BALL_RADIUS * 0.48
    glPushMatrix()
    glTranslatef(0.0, 0.0, -band_h / 2.0)
    q2 = gluNewQuadric()
    gluCylinder(q2, BALL_RADIUS * 1.05, BALL_RADIUS * 1.05, band_h, 36, 4)
    glPopMatrix()

    glPopMatrix()

# ------------------------------
# Text (template draw_text)
# ------------------------------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    # Save state
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

    glColor3f(1, 1, 1)  # bright white
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    # Restore
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopAttrib()

# ------------------------------
# Camera setup (template style)
# ------------------------------
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WIN_W / float(WIN_H), 0.1, 5000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    x, y, z = camera_pos
    gluLookAt(x, y, z, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)

# ------------------------------
# Input: keyboard (down/up), special, mouse
# ------------------------------
def keyboard_down(key, x, y):
    global key_left, key_right, is_jumping, ball_vz, game_over
    k = key.decode("utf-8") if isinstance(key, bytes) else key
    if k == '\x1b':
        sys.exit(0)
    if k in ('a','A'):
        key_left = True
    if k in ('d','D'):
        key_right = True
    if k in ('r','R'):
        restart_game()
    if k == ' ':
        if not is_jumping:
            is_jumping = True
            ball_vz = 600.0

def keyboard_up(key, x, y):
    global key_left, key_right
    k = key.decode("utf-8") if isinstance(key, bytes) else key
    if k in ('a','A'):
        key_left = False
    if k in ('d','D'):
        key_right = False

def specialKeyListener(key, x, y):
    global camera_pos
    cx, cy, cz = camera_pos
    if key == GLUT_KEY_LEFT:
        cx -= 4.0
    if key == GLUT_KEY_RIGHT:
        cx += 4.0
    camera_pos = (cx, cy, cz)

def mouseListener(button, state, x, y):
    pass

# ------------------------------
# Restart / reset
# ------------------------------
def restart_game():
    global lives, score, distance_score, ground_offset
    global obstacles, coins, ball_x, roll_x, roll_y, ball_z, ball_vz, is_jumping
    global game_over, game_start_time, shield_time, speed_time, coins_collected
    lives = 5
    score = 0
    distance_score = 0.0
    ground_offset = 0.0
    ball_x = 0.0
    roll_x = roll_y = 0.0
    ball_z = BALL_RADIUS
    ball_vz = 0.0
    is_jumping = False
    obstacles.clear()
    coins.clear()
    init_obstacles()
    init_coins()
    shield_time = 0.0
    speed_time = 0.0
    coins_collected = 0
    game_over = False
    game_start_time = time.time()

# ------------------------------
# Idle / update (main game loop)
# ------------------------------
def idle():
    global _last_time, ground_offset, roll_x, roll_y, ball_x, ball_z, ball_vz, is_jumping
    global score, distance_score, lives, game_over, shield_time, speed_time, coins_collected

    now = time.time()
    if _last_time is None:
        _last_time = now
    dt = clamp(now - _last_time, 0.0, 0.05)
    _last_time = now

    if game_over:
        glutPostRedisplay()
        return

    # reduce timers
    if shield_time > 0.0:
        shield_time -= dt
        if shield_time < 0.0:
            shield_time = 0.0
    if speed_time > 0.0:
        speed_time -= dt
        if speed_time < 0.0:
            speed_time = 0.0

    # compute forward speed; shield has priority (5x) when active
    speed = MOVE_SPEED
    if shield_time > 0.0:
        speed *= 5.0
    elif speed_time > 0.0:
        speed *= 2.0

    # always move forward
    ground_offset += speed * dt
    distance = speed * dt
    distance_score += distance * 0.1

    # forward rotation
    deg = (distance / (2.0 * math.pi * BALL_RADIUS)) * 360.0
    roll_x = (roll_x - deg) % 360.0

    # strafing
    if key_left:
        sx = MOVE_SPEED * dt
        ball_x = clamp(ball_x - sx, -GROUND_HALF_X + BALL_RADIUS, GROUND_HALF_X - BALL_RADIUS)
        lat_deg = (sx / (2.0 * math.pi * BALL_RADIUS)) * 360.0
        roll_y = (roll_y + lat_deg) % 360.0
    if key_right:
        sx = MOVE_SPEED * dt
        ball_x = clamp(ball_x + sx, -GROUND_HALF_X + BALL_RADIUS, GROUND_HALF_X - BALL_RADIUS)
        lat_deg = (sx / (2.0 * math.pi * BALL_RADIUS)) * 360.0
        roll_y = (roll_y - lat_deg) % 360.0

    # clamp horizontal
    edge = GROUND_HALF_X - BALL_RADIUS - 10.0
    ball_x = clamp(ball_x, -edge, edge)

    # jump physics
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

    # update coins and recycle passed ones
    for c in list(coins):
        if c["active"]:
            c["y"] += speed * dt
        if c["y"] > 420.0:
            # remove and respawn a new coin near the front
            try:
                coins.remove(c)
            except ValueError:
                pass
            spawn_coin(init_y = -200.0 - random.uniform(0.0, 600.0))
    while sum(1 for c in coins if c["active"]) < COIN_COUNT:
        spawn_coin(init_y = -200.0 - random.uniform(0.0, 600.0))

    # obstacle collisions (only if not shielded)
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

    # coin collection logic
    for c in list(coins):
        if not c["active"]:
            continue
        dx = ball_x - c["x"]
        dz = ball_z - c["z"]
        dist2 = dx*dx + dz*dz
        if dist2 <= (BALL_RADIUS + c["r"])**2 and abs(c["y"]) < 150.0:
            # if same power-up already active: ignore (do not count)
            if c["type"] == "shield" and shield_time > 0.0:
                # nudge forward to let it reappear later (not collected)
                c["y"] -= 300.0
                continue
            if c["type"] == "speed" and speed_time > 0.0:
                c["y"] -= 300.0
                continue

            # collect
            c["active"] = False
            coins_collected += 1
            if c["type"] == "normal":
                score += 5
            elif c["type"] == "shield":
                # only apply if not active (we checked above)
                if shield_time <= 0.0:
                    shield_time = 3.0
                    speed_time = 3.0   # shield gives speed for same duration
                    score += 10
            elif c["type"] == "speed":
                if speed_time <= 0.0:
                    speed_time = 3.0
                    score += 10

    glutPostRedisplay()

# ------------------------------
# Display (template showScreen)
# ------------------------------
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIN_W, WIN_H)

    setupCamera()

    # template-style random point demonstration
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

    draw_ball()
        # ---- HUD ----
    total_score = score + int(distance_score)
    draw_text(10, WIN_H - 24, f"Lives: {lives}   Score: {total_score}   Distance: {int(distance_score)}")
    draw_text(10, WIN_H - 50, f"Coins: {coins_collected}")

    if shield_time > 0:
        draw_text(10, WIN_H - 75, f"Shield Active: {shield_time:.1f}s")
    if speed_time > 0:
        draw_text(10, WIN_H - 100, f"2x Speed Active: {speed_time:.1f}s")

    if game_over:
        draw_text(WIN_W // 2 - 100, WIN_H // 2, "GAME OVER - Press R to Restart")

    glutSwapBuffers()


# ------------------------------
# Initialization & main
# ------------------------------
def main():
    global quad, _last_time, game_start_time
    glutInit()
    # use depth flag in display mode (template used it), but do not call glEnable
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Rolling Ball Runner - Template Safe")

    # set background (template used glClearColor)
    glClearColor(SKY_COLOR[0], SKY_COLOR[1], SKY_COLOR[2], SKY_COLOR[3])

    # prepare a quadric when needed (we still use gluNewQuadric locally; keep a global one too)
    quad = gluNewQuadric()

    init_clouds()
    init_flowers()
    init_obstacles()
    init_coins()

    _last_time = time.time()
    game_start_time = _last_time

    # register callbacks (template-style names)
    glutDisplayFunc(showScreen)
    # use keyboard down/up handlers
    glutKeyboardFunc(keyboard_down)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()
