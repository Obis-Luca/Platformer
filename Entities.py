import pygame.sprite

from data import *


class World:
    def __init__(self, data):
        self.tileList = []

        dirtImg = pygame.image.load('images/dirtTile.png')
        grassImg = pygame.image.load('images/grassTile.png')

        for rowCount, row in enumerate(data):
            for colCount, tile in enumerate(row):
                if tile == 1:
                    img = pygame.transform.scale(dirtImg, (tile_size_width, tile_size_height))
                    img_rect = img.get_rect()
                    img_rect.x = colCount * tile_size_width
                    img_rect.y = rowCount * tile_size_height
                    tile = (img, img_rect)
                    self.tileList.append(tile)
                elif tile == 2:
                    img = pygame.transform.scale(grassImg, (tile_size_width, tile_size_height))
                    img_rect = img.get_rect()
                    img_rect.x = colCount * tile_size_width
                    img_rect.y = rowCount * tile_size_height
                    tile = (img, img_rect)
                    self.tileList.append(tile)
                elif tile == 3:
                    blob = Enemy(colCount * tile_size_width, rowCount * tile_size_height + 6)
                    blobGroup.add(blob)
                elif tile == 6:
                    lava = Lava(colCount * tile_size_width, rowCount * tile_size_height + (tile_size_height // 2))
                    lavaGroup.add(lava)

    def draw(self):
        for tile_img, tile_rect in self.tileList:
            screen.blit(tile_img, tile_rect)


class Player:
    def __init__(self, x, y):
        # store player moving images into 2 lists
        # right stores the normal images and left one stores them flipped to the left side
        self.rightImages = []
        self.leftImages = []
        for num in range(1, 5):
            img = pygame.image.load(f'images/guy{num}.png')
            img = pygame.transform.scale(img, (40, 80))
            self.rightImages.append(img)
            self.leftImages.append(pygame.transform.flip(img, True, False))

        # rectangle variables
        self.deadImage = pygame.image.load('images/ghost.png')
        self.image = self.rightImages[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.rectWidth = self.rect.width
        self.rectHeight = self.rect.height
        # jumping variables
        self.vel_y = 0
        self.onGround = True
        # moving variables
        self.index = 0
        self.counter = 0
        self.direction = 1

    def update(self, game_over):
        dx = 0
        dy = 0
        walkCooldown = 5

        if game_over == 0:
            # get key pressed
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE] and self.onGround:
                self.vel_y = -15
                self.onGround = False
            if key[pygame.K_LEFT]:
                dx -= 6
                self.counter += 1
                self.direction = -1
            if key[pygame.K_RIGHT]:
                dx += 6
                self.counter += 1
                self.direction = 1
            # if left/right not pressed make the player stand still
            if not key[pygame.K_LEFT] and not key[pygame.K_RIGHT]:
                self.index = 0
                self.counter = 0
                if self.direction == 1:
                    self.image = self.rightImages[self.index]
                else:
                    self.image = self.leftImages[self.index]

            # if counter is 5 change current player image
            if walkCooldown == self.counter:
                self.index += 1
                self.counter = 0
                if self.index == len(self.rightImages):
                    self.index = 0
                # see in which direction
                if self.direction == 1:
                    self.image = self.rightImages[self.index]
                else:
                    self.image = self.leftImages[self.index]

            # add gravity
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            # check for collision
            for tile in world.tileList:
                # check collision on x-axis
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.rectWidth, self.rectHeight):
                    dx = 0
                # check for collision on y-axis
                elif tile[1].colliderect(self.rect.x, self.rect.y + dy, self.rectWidth, self.rectHeight):
                    # check if player hit his head by jumping
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    # check if player has fallen
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.onGround = True

            # collision with enemies
            if pygame.sprite.spritecollide(self, lavaGroup, False) or pygame.sprite.spritecollide(self, blobGroup,
                                                                                                  False):
                game_over = 1

            # update player coordinates
            self.rect.x += dx
            self.rect.y += dy
        elif game_over == 1:
            self.image = self.deadImage
            if self.rect.y > 200:
                self.rect.y -= 5

        # draw player onto the screen
        screen.blit(self.image, self.rect)
        return game_over


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('images/blob.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direction = 1
        self.moveCounter = 0

    def update(self):
        self.rect.x += self.direction
        self.moveCounter += 1
        if abs(self.moveCounter) > 50:
            self.direction *= -1
            self.moveCounter *= -1


class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('images/lava.png')
        self.image = pygame.transform.scale(img, (tile_size_width, tile_size_height // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Button:
    def __init__(self, x, y, img):
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False

        # get clicked mouse positions
        pos = pygame.mouse.get_pos()

        # check mouseover and clicked conditions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        # draw button
        screen.blit(self.image, self.rect)

        return action


blobGroup = pygame.sprite.Group()
lavaGroup = pygame.sprite.Group()
world = World(world_data)
player = Player(100, screen_height - 130)

# buttons
rstButton = Button(screen_width // 2 - 100, screen_height // 2 + 100, restartButtonImage)
startBtn = Button(screen_width // 2 - 300, screen_height // 2, startButtonImage)
exitBtn = Button(screen_width // 2 + 100, screen_height // 2, exitButtonImage)
