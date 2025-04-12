import pygame
import sys

# Initialize Pygame
pygame.init()

# Get display info to set the window to the current screen size (full-screen window with borders)
infoObject = pygame.display.Info()
screen_width = infoObject.current_w
screen_height = infoObject.current_h

# Create a resizable window with standard Windows controls
screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("Retro Fusion")

# Frame rate settings
clock = pygame.time.Clock()
FPS = 60

# Retro-themed colors
BACKGROUND_COLOR = (20, 20, 20)  # Dark, retro style background
TEXT_COLOR = (200, 200, 200)       # Light gray for text

# Set up font (using a simple system font for a retro look)
font = pygame.font.SysFont('Arial', 48)

# Game state variable
game_state = "start"  # "start" for intro screen, later will change to "playing"

def draw_start_screen():
    """Display the start screen with instructions."""
    screen.fill(BACKGROUND_COLOR)
    text = font.render("Press Space to Start", True, TEXT_COLOR)
    text_rect = text.get_rect(center=(screen_width // 2, screen_height // 2))
    screen.blit(text, text_rect)
    pygame.display.flip()

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        # Quit event
        if event.type == pygame.QUIT:
            running = False
        # Update screen dimensions on window resize
        elif event.type == pygame.VIDEORESIZE:
            screen_width, screen_height = event.size
            screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
        # Key press events
        elif event.type == pygame.KEYDOWN:
            if game_state == "start" and event.key == pygame.K_SPACE:
                # Start the game when Spacebar is pressed
                game_state = "playing"
                # Later on, this will trigger your game initialization and logic
            # Key mappings for future use:
            # Up Arrow (pygame.K_UP) will be for Jump
            # Left Arrow (pygame.K_LEFT) will move the ball left
            # Right Arrow (pygame.K_RIGHT) will move the ball right

    # Render based on game state
    if game_state == "start":
        draw_start_screen()
    elif game_state == "playing":
        # Placeholder for game play: clear the screen and display a message
        screen.fill(BACKGROUND_COLOR)
        text = font.render("Game Started", True, TEXT_COLOR)
        text_rect = text.get_rect(center=(screen_width // 2, screen_height // 2))
        screen.blit(text, text_rect)
        pygame.display.flip()

    clock.tick(FPS)

pygame.quit()
sys.exit()
