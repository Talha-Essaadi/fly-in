import pygame

# 1. Initialize pygame
pygame.init()

# 2. Create a window
info = pygame.display.Info()
width = info.current_w
height = info.current_h
# width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("My Pygame Program")

# 3. Set up a clock for frame rate
clock = pygame.time.Clock()
print("info:", info)
# 4. Main loop
running = True
while running:
    # a. Handle events (keyboard, mouse, quit)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # b. Update game state (move objects, handle collisions)
    
    # c. Draw everything
    screen.fill((0, 0, 0))  # Fill the screen with black
    pygame.draw.circle(screen, (255, 0, 0), (400, 300), 150)  # Example circle
    
    # d. Update the display
    pygame.display.flip()
    
    # e. Tick the clock (frame rate)
    clock.tick(60)

# 5. Quit pygame
pygame.quit()