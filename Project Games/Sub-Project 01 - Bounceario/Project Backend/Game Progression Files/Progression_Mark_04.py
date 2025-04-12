import pygame
import sys
import random

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
font = pygame.font.SysFont('Arial', 48)

# Physics parameters
GRAVITY = 0.5
BASE_JUMP_VELOCITY = -10  # base jump velocity (negative = upward)
HORIZONTAL_SPEED = 5

# Ball parameters
BALL_RADIUS = 20
MAX_BOUNCE_MULTIPLIER = 5  # cap for incremental bounce (first: -10, second: -12, etc.)

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

# --- Ball Class with Incremental Bounce and Swept Collision ---
class Ball:
    def __init__(self, x, y):
        self.x = x            # world coordinate
        self.y = y            # world coordinate
        self.prev_y = y       # previous vertical position
        self.radius = BALL_RADIUS
        self.velocity_y = 0
        # Bounce control:
        self.bounce_multiplier = 1  # increases additively with successive bounces
        # To detect landing events
        self.was_on_surface = True
        self.key_was_pressed = False  # for edge detection on Up key

    def get_surface(self, ground, platforms):
        # Start with the continuous ground height.
        candidate = ground.get_ground_height(self.x)
        # For each platform that spans the ball's x, check if the ball's bottom swept through its top.
        for p in platforms:
            if p.x <= self.x <= p.x + p.width:
                # If last frame the bottom was above the platform and now (within tolerance) it's at or below the platform top.
                if (self.prev_y + self.radius) <= p.y and (self.y + self.radius) >= (p.y - TOLERANCE):
                    candidate = min(candidate, p.y)
        return candidate

    def is_on_surface(self, ground, platforms):
        candidate = self.get_surface(ground, platforms)
        return abs((self.y + self.radius) - candidate) < TOLERANCE and self.velocity_y == 0

    def update(self, keys, ground, platforms):
        # --- Horizontal Movement with Slope Adjustment and Blocking ---
        slope = ground.get_ground_height(self.x + 5) - ground.get_ground_height(self.x)
        factor = 1 + slope / 100.0
        factor = max(0.8, min(1.2, factor))
        eff_speed = HORIZONTAL_SPEED * factor

        if keys[pygame.K_LEFT]:
            self.x -= eff_speed
        if keys[pygame.K_RIGHT]:
            # If on surface, check for blocking by a low platform ahead.
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

        # Save previous vertical position for swept collision.
        self.prev_y = self.y

        # --- Vertical Movement ---
        # If not on a surface, apply gravity.
        if not self.is_on_surface(ground, platforms):
            self.velocity_y += GRAVITY
        self.y += self.velocity_y

        # --- Head-Bump Detection (when moving upward) ---
        if self.velocity_y < 0:
            for p in platforms:
                if p.x <= self.x <= p.x + p.width:
                    platform_bottom = p.y + p.height
                    if (self.y - self.radius) < platform_bottom <= (self.prev_y - self.radius):
                        self.y = platform_bottom + self.radius
                        self.velocity_y = 0
                        break

        # --- Landing Collision ---
        candidate = self.get_surface(ground, platforms)
        if self.y + self.radius > candidate:
            self.y = candidate - self.radius
            self.velocity_y = 0

        # --- Detect Landing Event and Trigger Jump (Incremental Bounce) ---
        current_on_surface = self.is_on_surface(ground, platforms)
        # Detect landing: if last frame was not on surface but now is.
        if not self.was_on_surface and current_on_surface:
            # If Up is held on landing, trigger a jump.
            if keys[pygame.K_UP]:
                self.bounce_multiplier = min(self.bounce_multiplier + 1, MAX_BOUNCE_MULTIPLIER)
                jump_v = BASE_JUMP_VELOCITY - (self.bounce_multiplier - 1) * 2
                # Clamp so that ball doesn't go above top.
                if self.y + jump_v - self.radius < 0:
                    jump_v = -(self.y - self.radius)
                self.velocity_y = jump_v
                current_on_surface = False  # ball now becomes airborne
            else:
                # Reset multiplier if no jump initiated.
                self.bounce_multiplier = 1
        # Update state for next frame.
        self.was_on_surface = current_on_surface

        # --- Edge Detection for Up Key (for continuous bounce)
        self.key_was_pressed = keys[pygame.K_UP]

        # Prevent leaving the left edge.
        if self.x < self.radius:
            self.x = self.radius

    def draw(self, surface, camera_x):
        sx = self.x - camera_x
        pygame.draw.circle(surface, BALL_COLOR, (int(sx), int(self.y)), self.radius)

ball = None  # Will be created on game start

# --- Start Screen ---
def draw_start_screen():
    screen.fill(BACKGROUND_COLOR)
    text = font.render("Press Space to Start", True, TEXT_COLOR)
    text_rect = text.get_rect(center=(screen_width // 2, screen_height // 2))
    screen.blit(text, text_rect)
    pygame.display.flip()

def draw_play_screen():
    screen.fill(BACKGROUND_COLOR)
    ground.draw(screen, camera_x)
    for p in floating_platforms:
        p.draw(screen, camera_x)
    if ball:
        ball.draw(screen, camera_x)
    pygame.display.flip()

# --- Main Game Loop ---
game_state = "start"  # "start" or "playing"
update_floating_platforms(camera_x)

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

    if game_state == "start":
        draw_start_screen()
    elif game_state == "playing":
        if ball:
            ball.update(keys, ground, floating_platforms)
        ground.generate_points_until(camera_x + screen_width + 500)
        update_floating_platforms(camera_x)
        if ball and (ball.x - camera_x > screen_width * CAMERA_OFFSET):
            camera_x = ball.x - screen_width * CAMERA_OFFSET
        draw_play_screen()

    clock.tick(FPS)

pygame.quit()
sys.exit()
