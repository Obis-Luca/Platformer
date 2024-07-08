from Entities import *

pygame.init()


# editing grid
def draw_grid():
    for line in range(0, 20):
        pygame.draw.line(screen, (255, 255, 255), (0, line * tile_size_height), (screen_width, line * tile_size_height))
        pygame.draw.line(screen, (255, 255, 255), (line * tile_size_width, 0), (line * tile_size_width, screen_height))


run = True
while run:
    clock.tick(FPS)
    screen.blit(bg_img, (0, 0))
    if mainMenu:
        if startBtn.draw():
            mainMenu = False
        if exitBtn.draw():
            run = False
    else:
        if gameOver == 0:
            blobGroup.update()

        world.draw()
        blobGroup.draw(screen)
        lavaGroup.draw(screen)
        exitGroup.draw(screen)
        gameOver = player.update(gameOver)
        # draw_grid()

        if gameOver == -1:
            if rstButton.draw():
                gameOver = 0
                player.__init__(100, screen_height - 130)

        if gameOver == 1:
            display_message("You won!")
            if rstButton.draw():
                gameOver = 0
                player.__init__(100, screen_height - 130)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()
