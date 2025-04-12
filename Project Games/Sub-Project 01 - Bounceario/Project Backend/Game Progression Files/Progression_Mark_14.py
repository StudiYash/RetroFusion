import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()

# Set up display
infoObject = pygame.display.Info()
screen_width = infoObject.current_w
screen_height = infoObject.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("Retro Fusion")
clock = pygame.time.Clock()
FPS = 60

# Load images (after video mode is set)
spider_image = pygame.image.load("assets/spider.png").convert_alpha()
coin_image = pygame.image.load("assets/coin.png").convert_alpha()
ball_image_orig = pygame.image.load("assets/ball.png").convert_alpha()
mushroom_image = pygame.image.load("assets/mushroom.png").convert_alpha()  # New mushroom image

# Colors and font
BACKGROUND_COLOR = (20, 20, 20)
GROUND_COLOR = (255, 255, 255)
BALL_COLOR = (255, 0, 0)
TEXT_COLOR = (200, 200, 200)
score_font = pygame.font.SysFont("Bahnschrift Semibold", 38, bold=True)

# Physics parameters
GRAVITY = 0.5
BASE_JUMP_VELOCITY = -10
HORIZONTAL_SPEED = 5

# Ball parameters
BALL_RADIUS = 20
MAX_BOUNCE_MULTIPLIER = 5

# Tolerance for collision detection
TOLERANCE = 10

# Camera settings
camera_x = 0
CAMERA_OFFSET = 0.5

# Constants for modifications:
OBSTACLE_SIZE = 50           # Fixed size for obstacles (spider image)
OBSTACLE_HOVER_OFFSET = 10   # Obstacles will be raised 10px above ground/platform
SAFE_PADDING = 20            # Safe padding for coin/spider spacing
MAX_COIN_ATTEMPTS = 10       # Maximum attempts to find a safe coin candidate

# --- Global variable for mushroom cooldown ---
# Once a mushroom is collected, no new mushroom will spawn for next 80 seconds (80000 ms)
last_mushroom_collect_time = -80000

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
        self.coin_spawned = False

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

# --- Obstacles & Mushrooms ---
class Obstacle:
    def __init__(self, x, y, angle, on_platform=False):
        self.x = x  # top-left x
        self.y = y  # top-left y
        self.width = OBSTACLE_SIZE
        self.height = OBSTACLE_SIZE
        self.on_platform = on_platform
        self.angle = angle  # in radians

    def draw(self, surface, camera_x):
        sx = self.x - camera_x
        scaled_img = pygame.transform.scale(spider_image, (OBSTACLE_SIZE, OBSTACLE_SIZE))
        rotated_img = pygame.transform.rotate(scaled_img, -math.degrees(self.angle))
        rect = rotated_img.get_rect()
        rect.midbottom = (sx + OBSTACLE_SIZE / 2, self.y + OBSTACLE_SIZE)
        surface.blit(rotated_img, rect)

    def get_mask(self):
        scaled_img = pygame.transform.scale(spider_image, (OBSTACLE_SIZE, OBSTACLE_SIZE))
        rotated_img = pygame.transform.rotate(scaled_img, -math.degrees(self.angle))
        return pygame.mask.from_surface(rotated_img)

class Mushroom:
    def __init__(self, x, y, angle, on_platform=False):
        self.x = x
        self.y = y
        self.width = OBSTACLE_SIZE
        self.height = OBSTACLE_SIZE
        self.on_platform = on_platform
        self.angle = angle  # in radians

    def draw(self, surface, camera_x):
        sx = self.x - camera_x
        scaled_img = pygame.transform.scale(mushroom_image, (OBSTACLE_SIZE, OBSTACLE_SIZE))
        rotated_img = pygame.transform.rotate(scaled_img, -math.degrees(self.angle))
        rect = rotated_img.get_rect()
        rect.midbottom = (sx + OBSTACLE_SIZE / 2, self.y + OBSTACLE_SIZE)
        surface.blit(rotated_img, rect)

    def get_mask(self):
        scaled_img = pygame.transform.scale(mushroom_image, (OBSTACLE_SIZE, OBSTACLE_SIZE))
        rotated_img = pygame.transform.rotate(scaled_img, -math.degrees(self.angle))
        return pygame.mask.from_surface(rotated_img)

ground_obstacles = []
platform_obstacles = []

def update_ground_obstacles(camera_x):
    global ground_obstacles
    ground_obstacles = [o for o in ground_obstacles if o.x + OBSTACLE_SIZE > camera_x - 100]
    last_x = max(camera_x, 300)
    if ground_obstacles:
        last_x = max(last_x, max(o.x + OBSTACLE_SIZE for o in ground_obstacles))
    while last_x < camera_x + screen_width + 500:
        spacing = random.randint(100, 200)
        new_x = last_x + spacing
        sample_dx = 5
        gh1 = ground.get_ground_height(new_x)
        gh2 = ground.get_ground_height(new_x + sample_dx)
        angle = math.atan2(gh2 - gh1, sample_dx)
        ground_y = ground.get_ground_height(new_x)
        new_y = ground_y - OBSTACLE_SIZE
        if random.random() < 0.05:
            ground_obstacles.append(Obstacle(new_x, new_y, angle, on_platform=False))
        last_x = new_x + OBSTACLE_SIZE

def update_platform_obstacles(camera_x):
    global platform_obstacles, last_mushroom_collect_time
    platform_obstacles = [o for o in platform_obstacles if o.x + OBSTACLE_SIZE > camera_x - 100]
    for p in floating_platforms:
        if p.width < 150:
            continue
        exists = False
        for o in platform_obstacles:
            if o.on_platform:
                center_x = o.x + OBSTACLE_SIZE / 2
                if center_x >= p.x and center_x <= p.x + p.width and abs((o.y + OBSTACLE_SIZE) - p.y) < 5:
                    exists = True
                    break
        if not exists and random.random() < 0.03:
            margin = 10
            spawn_choice = random.random()
            # 10% chance to spawn a mushroom provided cooldown has passed
            if spawn_choice < 0.1 and (pygame.time.get_ticks() - last_mushroom_collect_time >= 80000):
                mush_x = random.randint(p.x + margin, p.x + p.width - margin - OBSTACLE_SIZE)
                mush_y = p.y - OBSTACLE_SIZE
                platform_obstacles.append(Mushroom(mush_x, mush_y, 0, on_platform=True))
            else:
                obs_x = random.randint(p.x + margin, p.x + p.width - margin - OBSTACLE_SIZE)
                obs_y = p.y - OBSTACLE_SIZE
                platform_obstacles.append(Obstacle(obs_x, obs_y, 0, on_platform=True))

# --- Moving Obstacles ---
class MovingObstacle(Obstacle):
    def __init__(self, x, y, angle, speed):
        super().__init__(x, y, angle, on_platform=False)
        self.speed = speed

    def update(self):
        self.x -= self.speed
        self.y = ground.get_ground_height(self.x) - OBSTACLE_SIZE
        sample_dx = 5
        gh1 = ground.get_ground_height(self.x)
        gh2 = ground.get_ground_height(self.x + sample_dx)
        self.angle = math.atan2(gh2 - gh1, sample_dx)

moving_obstacles = []
last_moving_obstacle_x = 0
last_moving_group_size = 0

def update_moving_obstacles(camera_x):
    global moving_obstacles, last_moving_obstacle_x, last_moving_group_size
    moving_obstacles = [m for m in moving_obstacles if m.x + OBSTACLE_SIZE > camera_x - 100]
    if last_moving_obstacle_x < camera_x + screen_width:
        last_moving_obstacle_x = camera_x + screen_width + 100
    while last_moving_obstacle_x < camera_x + screen_width + 500:
        if last_moving_group_size >= 4:
            group_size = random.randint(1, 3)
        else:
            group_size = random.randint(1, 5)
        for i in range(group_size):
            offset = i * random.randint(30, 60)
            new_x = last_moving_obstacle_x + offset
            sample_dx = 5
            gh1 = ground.get_ground_height(new_x)
            gh2 = ground.get_ground_height(new_x + sample_dx)
            angle = math.atan2(gh2 - gh1, sample_dx)
            ground_y = ground.get_ground_height(new_x)
            new_y = ground_y - OBSTACLE_SIZE
            speed = random.uniform(2, 4) * 0.5
            moving_obstacles.append(MovingObstacle(new_x, new_y, angle, speed))
        last_moving_group_size = group_size
        last_moving_obstacle_x += random.randint(500, 800)

# --- Coins & Scoring ---
class Coin:
    def __init__(self, x, y, radius):
        self.x = x  # center
        self.y = y  # center
        self.radius = radius

    def draw(self, surface, camera_x):
        sx = self.x - camera_x
        scaled_coin = pygame.transform.scale(coin_image, (self.radius*2, self.radius*2))
        rect = scaled_coin.get_rect()
        rect.center = (sx, self.y)
        surface.blit(scaled_coin, rect)

    def get_mask(self):
        scaled_coin = pygame.transform.scale(coin_image, (self.radius*2, self.radius*2))
        return pygame.mask.from_surface(scaled_coin)

ground_coins = []
platform_coins = []
last_ground_coin_x = 0

def generate_safe_coin_candidate(last_x, for_platform=False, platform=None):
    attempts = 0
    while attempts < MAX_COIN_ATTEMPTS:
        spacing = random.randint(400, 600)
        new_x = last_x + spacing
        if for_platform:
            coin_x = random.randint(platform.x, platform.x + platform.width)
            coin_y = platform.y - BALL_RADIUS
        else:
            coin_x = new_x
            coin_y = ground.get_ground_height(new_x) - BALL_RADIUS
        candidate = Coin(coin_x, coin_y, BALL_RADIUS)
        obstacles = ground_obstacles + platform_obstacles + moving_obstacles
        if coin_safe_from_obstacles(candidate, obstacles):
            return candidate, new_x
        attempts += 1
        last_x = new_x
    return None, last_x

def coin_safe_from_obstacles(coin, obstacles, safe_padding=SAFE_PADDING):
    coin_rect = pygame.Rect(coin.x - coin.radius, coin.y - coin.radius, coin.radius*2, coin.radius*2)
    coin_rect.inflate_ip(safe_padding*2, safe_padding*2)
    for obs in obstacles:
        obs_rect = pygame.Rect(obs.x, obs.y, OBSTACLE_SIZE, OBSTACLE_SIZE)
        if coin_rect.colliderect(obs_rect):
            return False
        coin_center = (coin.x, coin.y)
        obs_center = (obs.x + OBSTACLE_SIZE / 2, obs.y + OBSTACLE_SIZE / 2)
        min_distance = coin.radius + OBSTACLE_SIZE / 2 + safe_padding
        if math.hypot(coin_center[0] - obs_center[0], coin_center[1] - obs_center[1]) < min_distance:
            return False
    return True

def update_coins(camera_x):
    global ground_coins, platform_coins, last_ground_coin_x
    ground_coins = [c for c in ground_coins if c.x + c.radius > camera_x - 50]
    platform_coins = [c for c in platform_coins if c.x + c.radius > camera_x - 50]
    if last_ground_coin_x < camera_x:
        last_ground_coin_x = camera_x
    while last_ground_coin_x < camera_x + screen_width + 500:
        candidate, last_ground_coin_x = generate_safe_coin_candidate(last_ground_coin_x, for_platform=False)
        if candidate:
            ground_coins.append(candidate)
    for p in floating_platforms:
        if not p.coin_spawned and random.random() < 0.03:
            candidate, _ = generate_safe_coin_candidate(0, for_platform=True, platform=p)
            if candidate:
                platform_coins.append(candidate)
                p.coin_spawned = True

# --- Scoring ---
score = 0

# --- Ball Class ---
class Ball:
    def __init__(self, x, y):
        self.x = x  # center
        self.y = y  # center
        self.prev_y = y
        self.radius = BALL_RADIUS
        self.velocity_y = 0
        self.bounce_multiplier = 1
        self.was_on_surface = True
        self.key_was_pressed = False
        self.rotation_angle = 0  # degrees
        self.invincible = False
        self.invincible_end_time = 0

    def get_mask(self):
        scaled_ball = pygame.transform.scale(ball_image_orig, (self.radius*2, self.radius*2))
        rotated_ball = pygame.transform.rotate(scaled_ball, self.rotation_angle)
        return pygame.mask.from_surface(rotated_ball)

    def get_surface(self, ground, platforms):
        candidate = ground.get_ground_height(self.x)
        for p in platforms:
            if (self.x + self.radius >= p.x) and (self.x - self.radius <= p.x + p.width):
                if (self.prev_y + self.radius) <= p.y and (self.y + self.radius) >= (p.y - TOLERANCE):
                    candidate = min(candidate, p.y)
        return candidate

    def is_on_surface(self, ground, platforms):
        candidate = self.get_surface(ground, platforms)
        return abs((self.y + self.radius) - candidate) < TOLERANCE and self.velocity_y == 0

    def update(self, keys, ground, platforms):
        if keys[pygame.K_RIGHT]:
            self.rotation_angle -= 5
        elif keys[pygame.K_LEFT]:
            self.rotation_angle += 5

        current_ground_height = ground.get_ground_height(self.x)
        ground_height_at_x_plus = ground.get_ground_height(self.x + 5)
        slope = ground_height_at_x_plus - current_ground_height
        factor = 1 + slope / 100.0
        factor = max(0.8, min(1.2, factor))
        eff_speed = HORIZONTAL_SPEED * factor

        on_surface = self.is_on_surface(ground, platforms)

        if keys[pygame.K_LEFT]:
            self.x -= eff_speed
        if keys[pygame.K_RIGHT]:
            if on_surface:
                blocked = False
                for p in platforms:
                    if p.x > self.x and p.x < self.x + eff_speed:
                        if (current_ground_height - p.y) < (2 * self.radius):
                            self.x = p.x - self.radius
                            blocked = True
                            break
                if not blocked:
                    self.x += eff_speed
            else:
                self.x += eff_speed

        self.prev_y = self.y
        if not on_surface:
            self.velocity_y += GRAVITY
        self.y += self.velocity_y

        if self.velocity_y < 0:
            for p in platforms:
                if (self.x + self.radius >= p.x) and (self.x - self.radius <= p.x + p.width):
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

    def death_update(self, ground):
        self.velocity_y += GRAVITY
        self.y += self.velocity_y

    def draw(self, surface, camera_x):
        sx = self.x - camera_x
        scaled_ball = pygame.transform.scale(ball_image_orig, (self.radius*2, self.radius*2))
        rotated_ball = pygame.transform.rotate(scaled_ball, self.rotation_angle)
        rect = rotated_ball.get_rect()
        rect.center = (int(sx), int(self.y))
        surface.blit(rotated_ball, rect)

ball = None
# Game states: "start", "playing", "dying", "gameover"
game_state = "start"
death_animation_start_time = None

# --- Collision Handling ---
def mask_collision(ball, obj):
    ball_mask = ball.get_mask()
    obj_mask = obj.get_mask()
    offset_x = int(obj.x - (ball.x - ball.radius))
    offset_y = int(obj.y - (ball.y - ball.radius))
    return ball_mask.overlap(obj_mask, (offset_x, offset_y)) is not None

def check_obstacle_collisions(ball):
    global platform_obstacles, ground_obstacles, moving_obstacles, last_mushroom_collect_time
    # Separate platform obstacles into mushrooms and non-mushrooms.
    non_mushrooms = []
    mushrooms = []
    for o in platform_obstacles:
        if isinstance(o, Mushroom):
            mushrooms.append(o)
        else:
            non_mushrooms.append(o)
    all_obs = ground_obstacles + moving_obstacles + non_mushrooms
    collision_detected = False
    for obs in all_obs:
        if mask_collision(ball, obs):
            collision_detected = True
            break
    for mush in mushrooms:
        if mask_collision(ball, mush):
            if not ball.invincible:
                ball.invincible = True
                ball.invincible_end_time = pygame.time.get_ticks() + 20000  # 20 seconds invincibility
            platform_obstacles.remove(mush)
            last_mushroom_collect_time = pygame.time.get_ticks()
    return collision_detected and (not ball.invincible)

def coin_collision(ball, coin):
    dx = ball.x - coin.x
    dy = ball.y - coin.y
    return (dx * dx + dy * dy) <= (ball.radius + coin.radius) ** 2

def check_coin_collisions(ball):
    global ground_coins, platform_coins, score
    collected = 0
    for coin in ground_coins[:]:
        if coin_collision(ball, coin):
            ground_coins.remove(coin)
            collected += 20
    for coin in platform_coins[:]:
        if coin_collision(ball, coin):
            platform_coins.remove(coin)
            collected += 20
    return collected

# --- Screen Drawing Functions ---
def draw_start_screen():
    screen.fill(BACKGROUND_COLOR)
    text = pygame.font.SysFont("Arial", 48).render("Press Space to Start", True, TEXT_COLOR)
    text_rect = text.get_rect(center=(screen_width//2, screen_height//2))
    screen.blit(text, text_rect)
    pygame.display.flip()

def draw_game_over():
    screen.fill(BACKGROUND_COLOR)
    text = pygame.font.SysFont("Arial", 48).render("Game Over", True, TEXT_COLOR)
    text_rect = text.get_rect(center=(screen_width//2, screen_height//2))
    screen.blit(text, text_rect)
    subtext = pygame.font.SysFont("Arial", 48).render("Press R to Restart", True, TEXT_COLOR)
    subrect = subtext.get_rect(center=(screen_width//2, screen_height//2+50))
    screen.blit(subtext, subrect)
    score_text = score_font.render(f"Score: {score}", True, (0, 0, 255))
    screen.blit(score_text, (20, 20))
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
    for m in moving_obstacles:
        m.draw(screen, camera_x)
    for coin in ground_coins:
        coin.draw(screen, camera_x)
    for coin in platform_coins:
        coin.draw(screen, camera_x)
    if ball:
        ball.draw(screen, camera_x)
    
    # Display score
    score_text = score_font.render(f"Score: {score}", True, (0, 0, 255))
    screen.blit(score_text, (20, 20))
    
    # Display invincibility timer if active
    if ball and ball.invincible:
        remaining = (ball.invincible_end_time - pygame.time.get_ticks()) / 1000
        if remaining < 0:
            ball.invincible = False
        else:
            timer_text = score_font.render(f"{int(remaining)}", True, (255,255,0))
            screen.blit(timer_text, (screen_width - 100, 20))
    
    pygame.display.flip()

update_floating_platforms(camera_x)
update_ground_obstacles(camera_x)
update_platform_obstacles(camera_x)
update_coins(camera_x)
update_moving_obstacles(camera_x)

# --- Main Game Loop ---
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
            if game_state in ("start", "gameover") and event.key == pygame.K_SPACE:
                game_state = "playing"
                init_ground = ground.get_ground_height(100)
                ball = Ball(100, init_ground - BALL_RADIUS)
                ground_obstacles = []
                platform_obstacles = []
                moving_obstacles = []
                ground_coins = []
                platform_coins = []
                last_ground_coin_x = 0
                last_moving_obstacle_x = camera_x + screen_width + 100
                camera_x = 0
                score = 0
                for p in floating_platforms:
                    p.coin_spawned = False
            elif game_state == "gameover" and event.key == pygame.K_r:
                game_state = "playing"
                init_ground = ground.get_ground_height(100)
                ball = Ball(100, init_ground - BALL_RADIUS)
                ground_obstacles = []
                platform_obstacles = []
                moving_obstacles = []
                ground_coins = []
                platform_coins = []
                last_ground_coin_x = 0
                last_moving_obstacle_x = camera_x + screen_width + 100
                camera_x = 0
                score = 0
                for p in floating_platforms:
                    p.coin_spawned = False

    if game_state == "start":
        draw_start_screen()
    elif game_state == "playing":
        if ball:
            ball.update(keys, ground, floating_platforms)
            score += check_coin_collisions(ball)
            # Only trigger dying if not invincible
            if ball and (not ball.invincible) and check_obstacle_collisions(ball):
                game_state = "dying"
                death_animation_start_time = pygame.time.get_ticks()
                ball.velocity_y = -12
        ground.generate_points_until(camera_x + screen_width + 500)
        update_floating_platforms(camera_x)
        update_ground_obstacles(camera_x)
        update_platform_obstacles(camera_x)
        update_coins(camera_x)
        update_moving_obstacles(camera_x)
        for m in moving_obstacles:
            m.update()
        if ball and (ball.x - camera_x > screen_width * CAMERA_OFFSET):
            camera_x = ball.x - screen_width * CAMERA_OFFSET
        draw_play_screen()
    elif game_state == "dying":
        current_time = pygame.time.get_ticks()
        elapsed = current_time - death_animation_start_time
        # Pause for 1 second before starting death animation
        if elapsed >= 1000:
            if ball:
                ball.death_update(ground)
        draw_play_screen()
        if elapsed >= 3000:
            game_state = "gameover"
    elif game_state == "gameover":
        draw_game_over()

    clock.tick(FPS)

pygame.quit()
sys.exit()
