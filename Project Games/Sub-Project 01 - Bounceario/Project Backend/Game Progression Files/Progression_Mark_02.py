import pygame
import sys

# Initialize Pygame
pygame.init()

# Get display info for full screen window with typical OS window controls
infoObject = pygame.display.Info()
screen_width = infoObject.current_w
screen_height = infoObject.current_h

# Create a resizable window
screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("Retro Fusion")

# Frame rate settings
clock = pygame.time.Clock()
FPS = 60

# Retro-themed colors
BACKGROUND_COLOR = (20, 20, 20)    # Dark retro background
TEXT_COLOR = (200, 200, 200)         # Light retro text
GROUND_COLOR = (255, 255, 255)       # White ground for contrast
BALL_COLOR = (255, 0, 0)             # Red ball

# Set up font (using a system font for a retro look)
font = pygame.font.SysFont('Arial', 48)

# Physics parameters
GRAVITY = 0.5
JUMP_VELOCITY = -10
HORIZONTAL_SPEED = 5

# Ball parameters
BALL_RADIUS = 20

# Define the ground level (50 pixels from the bottom)
GROUND_Y = screen_height - 50

class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = BALL_RADIUS
        self.velocity_y = 0
    
    def update(self, keys):
        # Horizontal movement
        if keys[pygame.K_LEFT]:
            self.x -= HORIZONTAL_SPEED
        if keys[pygame.K_RIGHT]:
            self.x += HORIZONTAL_SPEED
        
        # Jump: allow jump only if the ball is on the ground
        if keys[pygame.K_UP] and self.on_ground():
            self.velocity_y = JUMP_VELOCITY
        
        # Apply gravity and update vertical position
        self.velocity_y += GRAVITY
        self.y += self.velocity_y
        
        # Collision with the ground
        if self.y + self.radius > GROUND_Y:
            self.y = GROUND_Y - self.radius
            self.velocity_y = 0
        
        # Prevent moving off-screen (left/right)
        if self.x - self.radius < 0:
            self.x = self.radius
        if self.x + self.radius > screen_width:
            self.x = screen_width - self.radius

    def on_ground(self):
        return self.y + self.radius >= GROUND_Y

    def draw(self, surface):
        pygame.draw.circle(surface, BALL_COLOR, (int(self.x), int(self.y)), self.radius)

# Game state variable and ball instance placeholder
game_state = "start"  # "start" for intro, "playing" for gameplay
ball = None  # The ball will be created once the game starts

def draw_start_screen():
    """Display the start screen with instructions."""
    screen.fill(BACKGROUND_COLOR)
    text = font.render("Press Space to Start", True, TEXT_COLOR)
    text_rect = text.get_rect(center=(screen_width // 2, screen_height // 2))
    screen.blit(text, text_rect)
    pygame.display.flip()

def draw_play_screen():
    """Render the game play screen with the ground and ball."""
    screen.fill(BACKGROUND_COLOR)
    # Draw the ground as a white rectangle at the bottom
    pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, screen_width, screen_height - GROUND_Y))
    # Draw the ball if it exists
    if ball:
        ball.draw(screen)
    pygame.display.flip()

# Main game loop
running = True
while running:
    keys = pygame.key.get_pressed()  # Get current key states
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            # Update screen size and ground level on window resize
            screen_width, screen_height = event.size
            screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
            GROUND_Y = screen_height - 50
        elif event.type == pygame.KEYDOWN:
            if game_state == "start" and event.key == pygame.K_SPACE:
                # Start the game when Space is pressed and initialize the ball
                game_state = "playing"
                ball = Ball(100, GROUND_Y - BALL_RADIUS)
    
    if game_state == "start":
        draw_start_screen()
    elif game_state == "playing":
        if ball:
            ball.update(keys)
        draw_play_screen()

    clock.tick(FPS)

pygame.quit()
sys.exit()
