import pygame


class SpriteSheet:
    def __init__(self, file):
        self.sprite_sheet = pygame.image.load(file)
        self.sprite_sheet_rect = self.sprite_sheet.get_rect()

    def get_image(self, x, y, width, height):  # gets sprite  x,y width, height,
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.image = pygame.Surface.subsurface(self.sprite_sheet, (x, y, width, height))
        return self.image

    def get_images(self, sprites_in_row, sprites_in_column, sprite_amount, reverse_image = False, transform_image = False, transformx=0, transformy=0):  # returns with list of sprites
        x_change = int(self.sprite_sheet_rect.width // sprite_amount)
        y_change = int(self.sprite_sheet_rect.height // sprite_amount)
        sprite_list = []
        sprite_x_row = self.x
        sprite_y_column = self.y
        column_length = sprites_in_column
        self.sprite_sheet_sprites = sprites_in_row * sprites_in_column
        sprite_run_total = 0
        self.sprite_run = 0

        for sprite in range(self.sprite_sheet_sprites):  # iterates through the total amount of sprites
            if reverse_image and transform_image: # reverse and transforms image
                sprite_list.append(pygame.transform.flip(pygame.transform.scale(self.get_image(sprite_x_row, sprite_y_column, self.width,
                                                                         self.height), (transformx, transformy)),True,False))
            elif reverse_image:
                sprite_list.append(pygame.transform.flip(self.get_image(sprite_x_row, sprite_y_column, self.width,
                                                                        self.height), True,
                                                         False))  # strips an image from the given (x,y) cords and
            elif transform_image: # transforms image
                sprite_list.append(pygame.transform.scale(self.get_image(sprite_x_row, sprite_y_column, self.width,
                                                                         self.height), (transformx,transformy)))


                # width/height and reverses it
            else:

                sprite_list.append(self.get_image(sprite_x_row, sprite_y_column, self.width,
                                                   self.height))# strips an image from the given (x,y) cords and
            # width/height
            sprite_x_row += x_change  # the x axis is incremented by the distance between two sprites in x
            # axis
            if sprite >= column_length:  # is the iteration through total sprites is larger then  sprites in column
                column_length += sprites_in_column  # column length incremented by column so that func can
                # iterate through next column
                # than x axis is reset and y axis incremented by distance between two sprites in the y axis
                sprite_x_row = 0
                sprite_y_column += y_change
        self.sprite_list = sprite_list
        return sprite_list  # returns a list of sprites

    def animate_sprite(self, screen, x_cord, y_cord):
        if self.sprite_run >= self.sprite_sheet_sprites:
            self.sprite_run =0
        screen.blit(self.sprite_list[self.sprite_run], (x_cord, y_cord))


        self.sprite_run+=1



