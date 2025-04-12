import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()

# Get display info and create a resizable window
infoObject = pygame.display.Info()
screen_width = infoObject.current_w
screen_height = infoObject.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("Retro Fusion")
clock = pygame.time.Clock()
FPS = 60  # Retro feel at 60 FPS

# Colors and font
BACKGROUND_COLOR = (20, 20, 20)
TEXT_COLOR = (200, 200, 200)
GROUND_COLOR = (255, 255, 255)
BALL_COLOR = (255, 0, 0)
OBSTACLE_COLOR = (0, 200, 0)  # Green obstacles (cactus-like)
font = pygame.font.SysFont('Arial', 48)

# Physics parameters
GRAVITY = 0.5
BASE_JUMP_VELOCITY = -10  # base jump (negative = upward)
HORIZONTAL_SPEED = 5

# Ball parameters
BALL_RADIUS = 20
MAX_BOUNCE_MULTIPLIER = 5  # bounce multiplier cap

# Tolerance for collision detection (in pixels)
TOLERANCE = 10

# Camera settings (world scroll)
camera_x = 0
CAMERA_OFFSET = 0.5  # ball is kept at half the screen width

# --- Ground Manager (Continuous Terrain) ---
ground_min_y = int(screen_height * 0.7)
ground_max_y = screen_height - 50
segment_min_length = 100
segment_max_length = 300
delta_y_range = 100

class GroundManager:
    def __init__(self):
        start_y = random.randint(ground_min_y, ground_max_y)
        self.points = [(0, start_y)]
        self.generate_points_until(camera_x + screen_width + 500)

    def generate_points_until(self, target_x):
        while self.points[-1][0] < target_x:
            last_x, last_y = self.points[-1]
            seg_length = random.randint(segment_min_length, segment_max_length)
            new_x = last_x + seg_length
            delta = random.randint(-delta_y_range, delta_y_range)
            new_y = last_y + delta
            new_y = max(ground_min_y, min(ground_max_y, new_y))
            self.points.append((new_x, new_y))

    def get_ground_height(self, x):
        if x <= self.points[0][0]:
            return self.points[0][1]
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i+1]
            if x1 <= x <= x2:
                t = (x - x1) / (x2 - x1)
                return y1 + t * (y2 - y1)
        self.generate_points_until(x + 500)
        return self.get_ground_height(x)

    def draw(self, surface, camera_x):
        shifted_points = []
        for x, y in self.points:
            sx = x - camera_x
            if -100 < sx < screen_width + 100:
                shifted_points.append((sx, y))
        if shifted_points:
            shifted_points.append((shifted_points[-1][0], screen_height))
            shifted_points.append((shifted_points[0][0], screen_height))
            pygame.draw.polygon(surface, GROUND_COLOR, shifted_points)

ground = GroundManager()

# --- Floating Platforms ---
class FloatingPlatform:
    def __init__(self, x, y, width, height=10):
        self.x = x
        self.y = y  # top of platform
        self.width = width
        self.height = height

    def draw(self, surface, camera_x):
        sx = self.x - camera_x
        pygame.draw.rect(surface, GROUND_COLOR, (sx, self.y, self.width, self.height))

floating_platforms = []

def update_floating_platforms(camera_x):
    global floating_platforms
    floating_platforms = [p for p in floating_platforms if p.x + p.width > camera_x - 100]
    last_x = camera_x + screen_width
    if floating_platforms:
        last_x = max(p.x + p.width for p in floating_platforms)
    while last_x < camera_x + screen_width + 500:
        width = random.randint(80, 200)
        new_x = last_x + random.randint(50, 200)
        ground_y = ground.get_ground_height(new_x)
        max_plat_y = max(50, ground_y - 50)
        new_y = random.randint(50, int(max_plat_y))
        floating_platforms.append(FloatingPlatform(new_x, new_y, width))
        last_x = new_x + width

# --- Obstacles ---

class Obstacle:
    def __init__(self, x, y, width, height, on_platform=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.on_platform = on_platform  # True if on a platform, else on ground

    def draw(self, surface, camera_x):
        sx = self.x - camera_x
        pygame.draw.rect(surface, OBSTACLE_COLOR, (sx, self.y, self.width, self.height))

# Global obstacle lists
ground_obstacles = []
platform_obstacles = []

def update_ground_obstacles(camera_x):
    global ground_obstacles
    ground_obstacles = [o for o in ground_obstacles if o.x + o.width > camera_x - 100]
    # Begin generating ground obstacles after x=300.
    last_x = max(camera_x, 300)
    if ground_obstacles:
        last_x = max(last_x, max(o.x + o.width for o in ground_obstacles))
    while last_x < camera_x + screen_width + 500:
        spacing = random.randint(100, 200)  # Increase spacing further
        new_x = last_x + spacing
        obs_width = random.randint(20, 40)
        obs_height = random.randint(10, 20)
        ground_y = ground.get_ground_height(new_x)
        new_y = ground_y - obs_height
        if random.random() < 0.05:  # 5% chance for ground obstacle
            ground_obstacles.append(Obstacle(new_x, new_y, obs_width, obs_height, on_platform=False))
        last_x = new_x + obs_width

def update_platform_obstacles(camera_x):
    global platform_obstacles
    platform_obstacles = [o for o in platform_obstacles if o.x + o.width > camera_x - 100]
    for p in floating_platforms:
        # Only consider platforms wider than 150
        if p.width < 150:
            continue
        # 3% chance to add an obstacle on an eligible platform.
        if random.random() < 0.03:
            margin = 10
            # Obstacle width: between 5% and 10% of platform width.
            min_obs_width = max(5, int(p.width * 0.05))
            max_obs_width = max(min_obs_width, int(p.width * 0.1))
            obs_width = random.randint(min_obs_width, max_obs_width)
            obs_height = random.randint(10, 20)
            # Ensure the obstacle doesn't cover the entire platform.
            available_space = p.width - 2 * margin - obs_width
            if available_space < 0:
                continue
            obs_x = random.randint(p.x + margin, p.x + p.width - margin - obs_width)
            obs_y = p.y - obs_height
            platform_obstacles.append(Obstacle(obs_x, obs_y, obs_width, obs_height, on_platform=True))

def check_collision(ball, obstacle):
    circle_x, circle_y, radius = ball.x, ball.y, ball.radius
    rect_x, rect_y, rect_w, rect_h = obstacle.x, obstacle.y, obstacle.width, obstacle.height
    closest_x = max(rect_x, min(circle_x, rect_x + rect_w))
    closest_y = max(rect_y, min(circle_y, rect_y + rect_h))
    distance_sq = (circle_x - closest_x) ** 2 + (circle_y - closest_y) ** 2
    return distance_sq < radius ** 2

def check_obstacle_collisions(ball):
    for o in ground_obstacles + platform_obstacles:
        if check_collision(ball, o):
            return True
    return False

# --- Ball Class with Incremental Bounce and Swept Collision ---
class Ball:
    def __init__(self, x, y):
        self.x = x            # world coordinate
        self.y = y            # world coordinate
        self.prev_y = y       # previous vertical position
        self.radius = BALL_RADIUS
        self.velocity_y = 0
        self.bounce_multiplier = 1  # increases additively on successive bounces
        self.was_on_surface = True  # for detecting landing events
        self.key_was_pressed = False  # for edge detection on Up key

    def get_surface(self, ground, platforms):
        candidate = ground.get_ground_height(self.x)
        for p in platforms:
            if p.x <= self.x <= p.x + p.width:
                if (self.prev_y + self.radius) <= p.y and (self.y + self.radius) >= (p.y - TOLERANCE):
                    candidate = min(candidate, p.y)
        return candidate

    def is_on_surface(self, ground, platforms):
        candidate = self.get_surface(ground, platforms)
        return abs((self.y + self.radius) - candidate) < TOLERANCE and self.velocity_y == 0

    def update(self, keys, ground, platforms):
        slope = ground.get_ground_height(self.x + 5) - ground.get_ground_height(self.x)
        factor = 1 + slope / 100.0
        factor = max(0.8, min(1.2, factor))
        eff_speed = HORIZONTAL_SPEED * factor

        if keys[pygame.K_LEFT]:
            self.x -= eff_speed
        if keys[pygame.K_RIGHT]:
            if self.is_on_surface(ground, platforms):
                ground_height = ground.get_ground_height(self.x)
                if abs((self.y + self.radius) - ground_height) < TOLERANCE:
                    blocked = False
                    for p in platforms:
                        if p.x > self.x and p.x < self.x + eff_speed:
                            if (ground_height - p.y) < (2 * self.radius):
                                self.x = p.x - self.radius
                                blocked = True
                                break
                    if not blocked:
                        self.x += eff_speed
                else:
                    self.x += eff_speed
            else:
                self.x += eff_speed

        self.prev_y = self.y

        if not self.is_on_surface(ground, platforms):
            self.velocity_y += GRAVITY
        self.y += self.velocity_y

        if self.velocity_y < 0:
            for p in platforms:
                if p.x <= self.x <= p.x + p.width:
                    platform_bottom = p.y + p.height
                    if (self.y - self.radius) < platform_bottom <= (self.prev_y - self.radius):
                        self.y = platform_bottom + self.radius
                        self.velocity_y = 0
                        break

        candidate = self.get_surface(ground, platforms)
        if self.y + self.radius > candidate:
            self.y = candidate - self.radius
            self.velocity_y = 0
        current_on_surface = self.is_on_surface(ground, platforms)

        # Jump (Bounce) Logic: Trigger jump if on surface and Up is pressed.
        if current_on_surface and keys[pygame.K_UP]:
            if (not self.key_was_pressed) or (not self.was_on_surface):
                self.bounce_multiplier = min(self.bounce_multiplier + 1, MAX_BOUNCE_MULTIPLIER)
                jump_v = BASE_JUMP_VELOCITY - (self.bounce_multiplier - 1) * 2
                if self.y + jump_v - self.radius < 0:
                    jump_v = -(self.y - self.radius)
                self.velocity_y = jump_v
                current_on_surface = False
        elif not keys[pygame.K_UP]:
            self.bounce_multiplier = 1

        self.was_on_surface = current_on_surface
        self.key_was_pressed = keys[pygame.K_UP]

        if self.x < self.radius:
            self.x = self.radius

    def draw(self, surface, camera_x):
        sx = self.x - camera_x
        pygame.draw.circle(surface, BALL_COLOR, (int(sx), int(self.y)), self.radius)

ball = None

game_state = "start"  # "start", "playing", or "gameover"

def draw_start_screen():
    screen.fill(BACKGROUND_COLOR)
    text = font.render("Press Space to Start", True, TEXT_COLOR)
    text_rect = text.get_rect(center=(screen_width//2, screen_height//2))
    screen.blit(text, text_rect)
    pygame.display.flip()

def draw_game_over():
    screen.fill(BACKGROUND_COLOR)
    text = font.render("Game Over", True, TEXT_COLOR)
    text_rect = text.get_rect(center=(screen_width//2, screen_height//2))
    screen.blit(text, text_rect)
    subtext = font.render("Press R to Restart", True, TEXT_COLOR)
    subrect = subtext.get_rect(center=(screen_width//2, screen_height//2+50))
    screen.blit(subtext, subrect)
    pygame.display.flip()

def draw_play_screen():
    screen.fill(BACKGROUND_COLOR)
    ground.draw(screen, camera_x)
    for p in floating_platforms:
        p.draw(screen, camera_x)
    for o in ground_obstacles:
        o.draw(screen, camera_x)
    for o in platform_obstacles:
        o.draw(screen, camera_x)
    if ball:
        ball.draw(screen, camera_x)
    pygame.display.flip()

update_floating_platforms(camera_x)
update_ground_obstacles(camera_x)
update_platform_obstacles(camera_x)

running = True
while running:
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            screen_width, screen_height = event.size
            screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
            ground_min_y = int(screen_height * 0.7)
            ground_max_y = screen_height - 50
        elif event.type == pygame.KEYDOWN:
            if game_state == "start" and event.key == pygame.K_SPACE:
                game_state = "playing"
                init_ground = ground.get_ground_height(100)
                ball = Ball(100, init_ground - BALL_RADIUS)
                ground_obstacles = []
                platform_obstacles = []
                camera_x = 0
            elif game_state == "gameover" and event.key == pygame.K_r:
                game_state = "playing"
                init_ground = ground.get_ground_height(100)
                ball = Ball(100, init_ground - BALL_RADIUS)
                ground_obstacles = []
                platform_obstacles = []
                camera_x = 0

    if game_state == "start":
        draw_start_screen()
    elif game_state == "playing":
        if ball:
            ball.update(keys, ground, floating_platforms)
            if check_obstacle_collisions(ball):
                game_state = "gameover"
        ground.generate_points_until(camera_x + screen_width + 500)
        update_floating_platforms(camera_x)
        update_ground_obstacles(camera_x)
        update_platform_obstacles(camera_x)
        if ball and (ball.x - camera_x > screen_width * CAMERA_OFFSET):
            camera_x = ball.x - screen_width * CAMERA_OFFSET
        draw_play_screen()
    elif game_state == "gameover":
        draw_game_over()

    clock.tick(FPS)

pygame.quit()
sys.exit()
