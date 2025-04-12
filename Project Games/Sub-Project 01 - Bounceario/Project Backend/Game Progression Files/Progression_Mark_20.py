import pygame
import sys
import random
import math

# -------------------- Audio Initialization --------------------
pygame.mixer.pre_init(44100, -16, 2, 512)  # Optional: pre-initialization for latency
pygame.mixer.init()
# Reserve channels for different categories (background music uses pygame.mixer.music)
jump_channel = pygame.mixer.Channel(1)
coin_channel = pygame.mixer.Channel(2)
mush_collect_channel = pygame.mixer.Channel(3)
gun_collect_channel = pygame.mixer.Channel(4)
fire_channel = pygame.mixer.Channel(5)
death_channel = pygame.mixer.Channel(6)
gameover_channel = pygame.mixer.Channel(7)

# Load sound effects (all files located in the 'audios' folder)
shortjump_sound = pygame.mixer.Sound("audios/shortjump.mp3")
longjump_sound = pygame.mixer.Sound("audios/longjump.mp3")
coincollect_sound = pygame.mixer.Sound("audios/coincollect.mp3")
mushpowercollect_sound = pygame.mixer.Sound("audios/mushpowercollect.mp3")
gunpowerup_sound = pygame.mixer.Sound("audios/gunpowerup.mp3")
fireball_sound = pygame.mixer.Sound("audios/fireball.mp3")
death_sound = pygame.mixer.Sound("audios/death.mp3")
gameover_sound = pygame.mixer.Sound("audios/gameover.mp3")

# Background music filenames
MAIN_BG_MUSIC = "audios/mainbg.mp3"
MUSH_BG_MUSIC = "audios/mushpowerbg.mp3"

# Functions to play and switch background music with fade effects (2 sec fade)
def play_background_music(track, fade_in=2000):
    pygame.mixer.music.load(track)
    pygame.mixer.music.play(-1, fade_ms=fade_in)

def switch_background_music(new_track, fade_out=2000, fade_in=2000):
    pygame.mixer.music.fadeout(fade_out)
    pygame.mixer.music.load(new_track)
    pygame.mixer.music.play(-1, fade_ms=fade_in)
# -------------------- End Audio Initialization --------------------

pygame.init()

# -------------------- Display Setup --------------------
infoObject = pygame.display.Info()
screen_width = infoObject.current_w
screen_height = infoObject.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("Retro Fusion")
clock = pygame.time.Clock()
FPS = 60
# -------------------- End Display Setup --------------------

# -------------------- Asset Loading --------------------
spider_image = pygame.image.load("assets/spider.png").convert_alpha()
coin_image = pygame.image.load("assets/coin.png").convert_alpha()
ball_image_orig = pygame.image.load("assets/ball.png").convert_alpha()
mushroom_image = pygame.image.load("assets/mushroom.png").convert_alpha()  # For invincibility pickup
gun_image = pygame.image.load("assets/gun.png").convert_alpha()            # For gun pickup
bullet_image_orig = pygame.image.load("assets/bullet.png").convert_alpha()
bullet_image_orig = pygame.transform.scale(bullet_image_orig, (10, 5))
# -------------------- End Asset Loading --------------------

# Colors and Font
BACKGROUND_COLOR = (20, 20, 20)
GROUND_COLOR = (255, 255, 255)
BALL_COLOR = (255, 0, 0)
TEXT_COLOR = (200, 200, 200)
score_font = pygame.font.SysFont("Bahnschrift Semibold", 38, bold=True)

# -------------------- Game Parameters --------------------
GRAVITY = 0.5
BASE_JUMP_VELOCITY = -10
HORIZONTAL_SPEED = 5

BALL_RADIUS = 20
MAX_BOUNCE_MULTIPLIER = 5  # Determines jump "level": bounce multiplier ≤ 2 => shortjump; ≥ 3 => longjump

TOLERANCE = 10

camera_x = 0
CAMERA_OFFSET = 0.5

OBSTACLE_SIZE = 50  # Base size for obstacles
OBSTACLE_HOVER_OFFSET = 10
SAFE_PADDING = 20
MAX_COIN_ATTEMPTS = 10

# Global distance thresholds for powerups (in pixels)
MUSHROOM_DISTANCE_THRESHOLD = 10000  # Spawn mushroom every 10,000 pixels
GUN_DISTANCE_THRESHOLD = 8000        # Spawn gun every 8,000 pixels
last_mushroom_spawn_x = 0
last_gun_spawn_x = 0

# Other Globals
bullets = []
gameover_start_time = None  # For disabling input during game-over

# -------------------- Background Music Control --------------------
def start_playing_background():
    play_background_music(MAIN_BG_MUSIC, fade_in=2000)
# -------------------- End Background Music Control --------------------

# -------------------- Ground Manager --------------------
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
# -------------------- End Ground Manager --------------------

# -------------------- Floating Platforms --------------------
class FloatingPlatform:
    def __init__(self, x, y, width, height=10):
        self.x = x
        self.y = y  # Top of platform
        self.width = width
        self.height = height
        self.coin_spawned = False
        self.last_pickup_time = 0  # (Not used now for powerups)
        self.has_powerup = False   # True if a powerup is already attached
        self.obstacle_destroyed = False
        self.powerup_type = None   # "mushroom" or "gun"

    def draw(self, surface, camera_x):
        sx = self.x - camera_x
        pygame.draw.rect(surface, GROUND_COLOR, (sx, self.y, self.width, self.height))

floating_platforms = []

def update_floating_platforms(camera_x):
    global floating_platforms
    floating_platforms = [p for p in floating_platforms if p.x + p.width > camera_x - 100]
    if not floating_platforms:
        last_x = 0
    else:
        last_x = max(p.x + p.width for p in floating_platforms)
    while last_x < camera_x + screen_width + 500:
        width = random.randint(80, 200)
        new_x = last_x + random.randint(50, 200)
        ground_y = ground.get_ground_height(new_x)
        max_plat_y = max(50, ground_y - 50)
        new_y = random.randint(50, int(max_plat_y))
        floating_platforms.append(FloatingPlatform(new_x, new_y, width))
        last_x = new_x + width
# -------------------- End Floating Platforms --------------------

# -------------------- Obstacles, Mushrooms & Guns --------------------
class Obstacle:
    def __init__(self, x, y, angle, on_platform=False):
        self.x = x
        self.y = y
        self.width = OBSTACLE_SIZE
        self.height = OBSTACLE_SIZE
        self.on_platform = on_platform
        self.angle = angle  # In radians
        self.dying = False
        self.death_velocity = 0
        self.shot = False

    def update(self):
        if self.dying:
            self.death_velocity += GRAVITY
            self.y += self.death_velocity

    def draw(self, surface, camera_x):
        sx = self.x - camera_x
        scaled_img = pygame.transform.scale(spider_image, (OBSTACLE_SIZE, OBSTACLE_SIZE))
        rotated_img = pygame.transform.rotate(scaled_img, -math.degrees(self.angle))
        rect = rotated_img.get_rect()
        rect.midbottom = (sx + OBSTACLE_SIZE/2, self.y + OBSTACLE_SIZE)
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
        self.angle = angle

    def draw(self, surface, camera_x):
        sx = self.x - camera_x
        scaled_img = pygame.transform.scale(mushroom_image, (OBSTACLE_SIZE, OBSTACLE_SIZE))
        rotated_img = pygame.transform.rotate(scaled_img, -math.degrees(self.angle))
        rect = rotated_img.get_rect()
        rect.midbottom = (sx + OBSTACLE_SIZE/2, self.y + OBSTACLE_SIZE)
        surface.blit(rotated_img, rect)

    def get_mask(self):
        scaled_img = pygame.transform.scale(mushroom_image, (OBSTACLE_SIZE, OBSTACLE_SIZE))
        rotated_img = pygame.transform.rotate(scaled_img, -math.degrees(self.angle))
        return pygame.mask.from_surface(rotated_img)

class Gun:
    def __init__(self, x, y, angle, on_platform=False):
        self.x = x
        self.y = y
        self.width = 50   # Adjusted gun image size
        self.height = 35  
        self.on_platform = on_platform
        self.angle = angle

    def draw(self, surface, camera_x):
        sx = self.x - camera_x
        scaled_img = pygame.transform.scale(gun_image, (self.width, self.height))
        rotated_img = pygame.transform.rotate(scaled_img, -math.degrees(self.angle))
        rect = rotated_img.get_rect()
        rect.midbottom = (sx + self.width/2, self.y + OBSTACLE_SIZE)
        surface.blit(rotated_img, rect)

    def get_mask(self):
        scaled_img = pygame.transform.scale(gun_image, (self.width, self.height))
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
        if random.random() < 0.0425:
            ground_obstacles.append(Obstacle(new_x, new_y, angle, on_platform=False))
        last_x = new_x + OBSTACLE_SIZE

def update_platform_obstacles(camera_x):
    global platform_obstacles
    platform_obstacles = [o for o in platform_obstacles if o.x + OBSTACLE_SIZE > camera_x - 100]
    # Standard obstacle spawn on platforms with a small chance:
    for p in floating_platforms:
        if p.width < 150 or p.has_powerup or p.obstacle_destroyed:
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
            obs_x = random.randint(p.x + margin, p.x + p.width - margin - OBSTACLE_SIZE)
            obs_y = p.y - OBSTACLE_SIZE
            platform_obstacles.append(Obstacle(obs_x, obs_y, 0, on_platform=True))
    # Distance-based powerup spawns:
    if ball:
        spawn_mushroom_powerup()
        spawn_gun_powerup()

def spawn_mushroom_powerup():
    global last_mushroom_spawn_x, platform_obstacles
    if ball is None:
        return
    if ball.x - last_mushroom_spawn_x >= MUSHROOM_DISTANCE_THRESHOLD:
        candidate = None
        sorted_platforms = sorted(floating_platforms, key=lambda p: p.x)
        for p in sorted_platforms:
            if p.x > last_mushroom_spawn_x and p.width >= 150 and (not p.has_powerup) and (not p.obstacle_destroyed):
                free = True
                for o in platform_obstacles:
                    if o.on_platform:
                        center_x = o.x + OBSTACLE_SIZE/2
                        if center_x >= p.x and center_x <= p.x + p.width and abs((o.y + OBSTACLE_SIZE) - p.y) < 5:
                            free = False
                            break
                if free:
                    candidate = p
                    break
        if candidate is not None:
            margin = 10
            mush_x = random.randint(candidate.x + margin, candidate.x + candidate.width - margin - OBSTACLE_SIZE)
            mush_y = candidate.y - OBSTACLE_SIZE
            platform_obstacles.append(Mushroom(mush_x, mush_y, 0, on_platform=True))
            candidate.has_powerup = True
            candidate.powerup_type = "mushroom"
            last_mushroom_spawn_x = candidate.x
            # Play mushroom collection sound and switch bg music immediately
            mush_collect_channel.play(mushpowercollect_sound)
            switch_background_music(MUSH_BG_MUSIC, fade_out=2000, fade_in=2000)

def spawn_gun_powerup():
    global last_gun_spawn_x, platform_obstacles
    if ball is None:
        return
    if ball.x - last_gun_spawn_x >= GUN_DISTANCE_THRESHOLD:
        candidate = None
        sorted_platforms = sorted(floating_platforms, key=lambda p: p.x)
        for p in sorted_platforms:
            if p.x > last_gun_spawn_x and p.width >= 150 and (not p.has_powerup) and (not p.obstacle_destroyed):
                free = True
                for o in platform_obstacles:
                    if o.on_platform:
                        center_x = o.x + OBSTACLE_SIZE/2
                        if center_x >= p.x and center_x <= p.x + p.width and abs((o.y + OBSTACLE_SIZE) - p.y) < 5:
                            free = False
                            break
                if free:
                    candidate = p
                    break
        if candidate is not None:
            margin = 10
            gun_x = random.randint(candidate.x + margin, candidate.x + candidate.width - margin - OBSTACLE_SIZE)
            gun_y = candidate.y - OBSTACLE_SIZE
            platform_obstacles.append(Gun(gun_x, gun_y, 0, on_platform=True))
            candidate.has_powerup = True
            candidate.powerup_type = "gun"
            last_gun_spawn_x = candidate.x
            gun_collect_channel.play(gunpowerup_sound)
# -------------------- End Obstacles, Mushrooms & Guns --------------------

# -------------------- Moving Obstacles --------------------
class MovingObstacle(Obstacle):
    def __init__(self, x, y, angle, speed):
        super().__init__(x, y, angle, on_platform=False)
        self.speed = speed

    def update(self):
        if self.dying:
            self.death_velocity += GRAVITY
            self.y += self.death_velocity
        else:
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
# -------------------- End Moving Obstacles --------------------

# -------------------- Coins & Scoring --------------------
class Coin:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
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
        obs_center = (obs.x + OBSTACLE_SIZE/2, obs.y + OBSTACLE_SIZE/2)
        min_distance = coin.radius + OBSTACLE_SIZE/2 + safe_padding
        if math.hypot(coin_center[0]-obs_center[0], coin_center[1]-obs_center[1]) < min_distance:
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
# -------------------- End Coins & Scoring --------------------

score = 0

# -------------------- Bullet Class --------------------
class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.speed = 10
        self.angle = angle  # In radians
        self.image = bullet_image_orig.copy()
        if angle != 0:
            self.image = pygame.transform.rotate(self.image, -math.degrees(angle))
        self.rect = self.image.get_rect(center=(x, y))
    def update(self):
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)
        self.rect.center = (self.x, self.y)
    def draw(self, surface, camera_x):
        sx = self.x - camera_x
        surface.blit(self.image, (sx - self.rect.width//2, self.y - self.rect.height//2))
    def get_mask(self):
        return pygame.mask.from_surface(self.image)
# -------------------- End Bullet Class --------------------

# -------------------- Ball Class --------------------
class Ball:
    def __init__(self, x, y):
        self.x = x  # Center
        self.y = y  # Center
        self.prev_y = y
        self.radius = BALL_RADIUS
        self.velocity_y = 0
        self.bounce_multiplier = 1
        self.was_on_surface = True
        self.key_was_pressed = False
        self.rotation_angle = 0  # Degrees
        self.invincible = False
        self.invincible_end_time = 0
        self.gun_power = False
        self.gun_power_end_time = 0

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
        # Rotate based on key presses
        if keys[pygame.K_RIGHT]:
            self.rotation_angle -= 5
        elif keys[pygame.K_LEFT]:
            self.rotation_angle += 5

        # Check if gun power expired
        if self.gun_power and pygame.time.get_ticks() > self.gun_power_end_time:
            self.gun_power = False

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
            blocked = False
            if on_surface:
                for p in platforms:
                    if p.x > self.x and p.x < self.x + eff_speed:
                        if (current_ground_height - p.y) < (2 * self.radius):
                            self.x = p.x - self.radius
                            blocked = True
                            break
            if not blocked:
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
                # Play jump sound based on bounce multiplier:
                if self.bounce_multiplier <= 2:
                    jump_channel.play(shortjump_sound)
                else:
                    jump_channel.play(longjump_sound)
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
# -------------------- End Ball Class --------------------

ball = None
game_state = "start"  # Possible states: "start", "playing", "dying", "gameover"
death_animation_start_time = None

# -------------------- Collision Functions --------------------
def mask_collision(entity, obj):
    mask1 = entity.get_mask()
    mask2 = obj.get_mask()
    if hasattr(entity, "radius"):
        offset_x = int(obj.x - (entity.x - entity.radius))
        offset_y = int(obj.y - (entity.y - entity.radius))
    else:
        offset_x = int(obj.x - (entity.x - entity.rect.width//2))
        offset_y = int(obj.y - (entity.y - entity.rect.height//2))
    return mask1.overlap(mask2, (offset_x, offset_y)) is not None

def check_obstacle_collisions(ball):
    global platform_obstacles, ground_obstacles, moving_obstacles
    non_pickups = []
    mushrooms = []
    guns = []
    for o in platform_obstacles:
        if isinstance(o, Mushroom):
            mushrooms.append(o)
        elif isinstance(o, Gun):
            guns.append(o)
        else:
            non_pickups.append(o)
    all_obs = ground_obstacles + moving_obstacles + non_pickups
    collision_detected = False
    for obs in all_obs:
        if mask_collision(ball, obs):
            if not obs.dying:
                obs.dying = True
                obs.death_velocity = -12  # death impulse
            if obs.on_platform:
                for p in floating_platforms:
                    if p.x <= obs.x <= p.x + p.width and abs((obs.y + OBSTACLE_SIZE) - p.y) < 10:
                        p.obstacle_destroyed = True
            if not ball.invincible and not obs.shot:
                collision_detected = True
    for mush in mushrooms[:]:
        if mask_collision(ball, mush):
            current_time = pygame.time.get_ticks()
            if ball.invincible:
                ball.invincible_end_time += 20000
            else:
                ball.invincible = True
                ball.invincible_end_time = current_time + 20000
            try:
                platform_obstacles.remove(mush)
            except ValueError:
                pass
                for p in floating_platforms:
                    if p.x <= mush.x <= p.x + p.width and abs(p.y - (mush.y + OBSTACLE_SIZE)) < 10:
                        p.last_pickup_time = current_time
    for gun in guns[:]:
        if mask_collision(ball, gun):
            current_time = pygame.time.get_ticks()
            if ball.gun_power:
                ball.gun_power_end_time += 60000
            else:
                ball.gun_power = True
                ball.gun_power_end_time = current_time + 60000
            try:
                platform_obstacles.remove(gun)
            except ValueError:
                pass
            for p in floating_platforms:
                if p.x <= gun.x <= p.x + p.width and abs(p.y - (gun.y + OBSTACLE_SIZE)) < 10:
                    p.last_pickup_time = current_time
    return collision_detected

def coin_collision(ball, coin):
    dx = ball.x - coin.x
    dy = ball.y - coin.y
    return (dx*dx + dy*dy) <= (ball.radius + coin.radius)**2

def check_coin_collisions(ball):
    global ground_coins, platform_coins, score
    collected = 0
    for coin in ground_coins[:]:
        if coin_collision(ball, coin):
            ground_coins.remove(coin)
            collected += 20
            coin_channel.play(coincollect_sound)
    for coin in platform_coins[:]:
        if coin_collision(ball, coin):
            platform_coins.remove(coin)
            collected += 20
            coin_channel.play(coincollect_sound)
    return collected
# -------------------- End Collision Functions --------------------

# -------------------- Screen Drawing Functions --------------------
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
    score_text = score_font.render(f"Score: {score}", True, (0,0,255))
    screen.blit(score_text, (20,20))
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
    for bullet in bullets:
        bullet.draw(screen, camera_x)
    if ball:
        ball.draw(screen, camera_x)
    score_text = score_font.render(f"Score: {score}", True, (0,0,255))
    screen.blit(score_text, (20,20))
    
    y_offset = 20
    if ball and ball.invincible:
        remaining_inv = (ball.invincible_end_time - pygame.time.get_ticks()) / 1000
        if remaining_inv < 0:
            ball.invincible = False
            switch_background_music(MAIN_BG_MUSIC, fade_out=2000, fade_in=2000)
        else:
            inv_text = score_font.render(f"Invincible: {int(remaining_inv)} seconds", True, (255,255,0))
            screen.blit(inv_text, (screen_width - 300, y_offset))
            y_offset += 40
    if ball and ball.gun_power:
        remaining_gun = (ball.gun_power_end_time - pygame.time.get_ticks()) / 1000
        if remaining_gun < 0:
            ball.gun_power = False
        else:
            gun_text = score_font.render(f"Gun Power: {int(remaining_gun)} seconds", True, (0,255,0))
            screen.blit(gun_text, (screen_width - 300, y_offset))
    pygame.display.flip()
# -------------------- End Screen Drawing --------------------

# -------------------- Early Powerup Spawn --------------------
def spawn_early_powerups():
    global last_mushroom_spawn_x, last_gun_spawn_x
    mushroom_spawned = False
    gun_spawned = False
    for p in floating_platforms:
        if p.x < 1000 and not p.has_powerup:
            if not mushroom_spawned:
                mush_x = random.randint(p.x+10, p.x + p.width - 10 - OBSTACLE_SIZE)
                mush_y = p.y - OBSTACLE_SIZE
                platform_obstacles.append(Mushroom(mush_x, mush_y, 0, on_platform=True))
                p.has_powerup = True
                p.powerup_type = "mushroom"
                last_mushroom_spawn_x = p.x
                mushroom_spawned = True
                mush_collect_channel.play(mushpowercollect_sound)
                switch_background_music(MUSH_BG_MUSIC, fade_out=2000, fade_in=2000)
            elif not gun_spawned:
                gun_x = random.randint(p.x+10, p.x + p.width - 10 - OBSTACLE_SIZE)
                gun_y = p.y - OBSTACLE_SIZE
                platform_obstacles.append(Gun(gun_x, gun_y, 0, on_platform=True))
                p.has_powerup = True
                p.powerup_type = "gun"
                last_gun_spawn_x = p.x
                gun_spawned = True
                gun_collect_channel.play(gunpowerup_sound)
        if mushroom_spawned and gun_spawned:
            break
# -------------------- End Early Powerup Spawn --------------------

# -------------------- Initial Updates --------------------
update_floating_platforms(camera_x)
update_ground_obstacles(camera_x)
update_platform_obstacles(camera_x)
update_coins(camera_x)
update_moving_obstacles(camera_x)
# -------------------- End Initial Updates --------------------

# -------------------- Main Background Music Start --------------------
# It will be started when the game state changes to "playing"
# -------------------- End Background Music Start --------------------

# -------------------- Main Game Loop --------------------
running = True
while running:
    keys = pygame.key.get_pressed()
    current_time = pygame.time.get_ticks()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            screen_width, screen_height = event.size
            screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
            ground_min_y = int(screen_height * 0.7)
            ground_max_y = screen_height - 50
        elif event.type == pygame.KEYDOWN:
            # During game-over, disable input for 4 seconds
            if game_state == "gameover" and current_time < gameover_start_time + 4000:
                continue
            if game_state in ("start", "gameover") and event.key == pygame.K_SPACE:
                game_state = "playing"
                init_ground = ground.get_ground_height(100)
                ball = Ball(100, init_ground - BALL_RADIUS)
                ground_obstacles = []
                platform_obstacles = []
                moving_obstacles = []
                ground_coins = []
                platform_coins = []
                bullets.clear()
                floating_platforms = []
                update_floating_platforms(0)
                spawn_early_powerups()  # Force early powerups within first 1000 pixels
                last_ground_coin_x = 0
                last_moving_obstacle_x = 0
                camera_x = 0
                score = 0
                start_playing_background()
            elif game_state == "gameover" and event.key == pygame.K_r:
                game_state = "playing"
                init_ground = ground.get_ground_height(100)
                ball = Ball(100, init_ground - BALL_RADIUS)
                ground_obstacles = []
                platform_obstacles = []
                moving_obstacles = []
                ground_coins = []
                platform_coins = []
                bullets.clear()
                floating_platforms = []
                update_floating_platforms(0)
                spawn_early_powerups()
                last_ground_coin_x = 0
                last_moving_obstacle_x = 0
                camera_x = 0
                score = 0
                start_playing_background()
            elif game_state == "playing" and event.key == pygame.K_f:
                if ball and ball.gun_power:
                    if ball.is_on_surface(ground, floating_platforms):
                        sample_dx = 5
                        gh1 = ground.get_ground_height(ball.x)
                        gh2 = ground.get_ground_height(ball.x + sample_dx)
                        bullet_angle = math.atan2(gh2 - gh1, sample_dx)
                    else:
                        bullet_angle = 0
                    new_bullet = Bullet(ball.x, ball.y, bullet_angle)
                    bullets.append(new_bullet)
                    fire_channel.play(fireball_sound)
    if game_state == "start":
        draw_start_screen()
    elif game_state == "playing":
        if ball:
            ball.update(keys, ground, floating_platforms)
            score += check_coin_collisions(ball)
            if ball and check_obstacle_collisions(ball):
                pygame.mixer.music.stop()  # Stop bg music immediately
                death_channel.play(death_sound)
                game_state = "dying"
                death_animation_start_time = pygame.time.get_ticks()
                ball.velocity_y = -12
        ground.generate_points_until(camera_x + screen_width + 500)
        update_floating_platforms(camera_x)
        update_ground_obstacles(camera_x)
        update_platform_obstacles(camera_x)
        update_coins(camera_x)
        update_moving_obstacles(camera_x)
        for obs in ground_obstacles:
            obs.update()
        for obs in platform_obstacles:
            if not isinstance(obs, (Mushroom, Gun)):
                obs.update()
        ground_obstacles = [obs for obs in ground_obstacles if not (obs.dying and obs.y > screen_height + 50)]
        platform_obstacles = [obs for obs in platform_obstacles if (isinstance(obs, (Mushroom, Gun)) or not (obs.dying and obs.y > screen_height + 50))]
        moving_obstacles = [obs for obs in moving_obstacles if not (obs.dying and obs.y > screen_height + 50)]
        for m in moving_obstacles:
            m.update()
        for bullet in bullets[:]:
            bullet.update()
            if bullet.x - camera_x > screen_width:
                bullets.remove(bullet)
                continue
            hit = False
            for obs in ground_obstacles + moving_obstacles + [o for o in platform_obstacles if not isinstance(o, (Mushroom, Gun))]:
                if mask_collision(bullet, obs):
                    if not obs.dying:
                        obs.dying = True
                        obs.death_velocity = -10  # Bullet impact impulse
                        obs.shot = True
                        if obs.on_platform:
                            for p in floating_platforms:
                                if p.x <= obs.x <= p.x + p.width and abs((obs.y+OBSTACLE_SIZE)-p.y) < 10:
                                    p.obstacle_destroyed = True
                    if bullet in bullets:
                        bullets.remove(bullet)
                    hit = True
                    break
            if hit:
                continue
        if ball and (ball.x - camera_x > screen_width * CAMERA_OFFSET):
            camera_x = ball.x - screen_width * CAMERA_OFFSET
        draw_play_screen()
    elif game_state == "dying":
        current_time = pygame.time.get_ticks()
        elapsed = current_time - death_animation_start_time
        if elapsed >= 1000:
            if ball:
                ball.death_update(ground)
        draw_play_screen()
        if elapsed >= 3000:
            game_state = "gameover"
            gameover_start_time = pygame.time.get_ticks()  # Disable input for 4 sec
            gameover_channel.play(gameover_sound)
    elif game_state == "gameover":
        draw_game_over()
    clock.tick(FPS)
pygame.quit()
sys.exit()
