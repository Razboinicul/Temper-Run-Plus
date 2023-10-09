import pygame as pg
import sys
import pygame_gui as gui
from engine import *
import packing
high_score = 0

def main():
    global PAUSED, new_game, high_score
    high_score = packing.load()
    is_running = True
    """This is the Game's main function"""
    pg.init()
    pg.display.set_caption('Temper Run Plus')
    window_surface = pg.display.set_mode((800, 600))
    
    #window_surface.fill(pg.Color('#87CEEB'))
    manager = gui.UIManager((800, 600))
    clock = pg.time.Clock()
    
    bg = pg.image.load("bg.png").convert_alpha()
    #bg = None
    pg.font.init() # you have to call this at the start, 
                   # if you want to use this module.
    TitleFont = pg.font.SysFont('Arial', 80)
    VerFont = pg.font.SysFont('Calibri', 40)
    TitleText = TitleFont.render('Temper Run', False, (255, 255, 255))
    VerText = VerFont.render('2.0.0 alpha', False, (255, 255, 255))
    
    
    play_button = gui.elements.UIButton(relative_rect=pg.Rect((290, 160), (250, 50)),
                                             text='Play',
                                             manager=manager)

    GG_button = gui.elements.UIButton(relative_rect=pg.Rect((288, 350), (125, 50)),
                                             text='GG',
                                             manager=manager)

    About_button = gui.elements.UIButton(relative_rect=pg.Rect((290, 210), (250, 50)),
                                             text='About',
                                             manager=manager)
    
    Exit_button = gui.elements.UIButton(relative_rect=pg.Rect((418, 350), (125, 50)),
                                             text='Exit',
                                             manager=manager)

    
    #stopping this game just set this to false
    game_active = False
    paused = False
    while is_running:
        time_delta = clock.tick(30)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                is_running = False
            if event.type == pg.USEREVENT:
                if event.user_type == gui.UI_BUTTON_PRESSED:
                    if event.ui_element == play_button:
                        game = Game()
                        game_active = True
                        SCORE = 0
                        print('OK')
                if event.type == pg.KEYDOWN:
                    if event.user_type == gui.UI_BUTTON_PRESSED:
                        if event.ui_element == About_button:
                            print("About")
                            about()
                    if event.user_type == gui.UI_BUTTON_PRESSED:
                        if event.ui_element == GG_button:
                            print('GG!')
                    if event.user_type == gui.UI_BUTTON_PRESSED:
                        if event.ui_element == Exit_button:
                            is_running = False   
                    
            manager.process_events(event)
        manager.update(time_delta)


        if game_active and not game.game_over:
            #if game ongoing update it
            #resume_button.hide()
            #resume_button.disable()
            play_button.disable()
            About_button.disable()
            GG_button.disable()
            Exit_button.disable()
            play_button.hide()
            About_button.hide()
            GG_button.hide()
            Exit_button.hide()
            game.update(window_surface)
            if PAUSED:
                paused()
                PAUSED = False
            score = game.update(window_surface)
            ScoreText = VerFont.render(f'Score: {score}', False, (255, 255, 255))
            window_surface.blit(ScoreText,(0, 0))
        else:
            play_button.enable()
            About_button.enable()
            GG_button.enable()
            Exit_button.enable()
            play_button.show()
            About_button.show()
            GG_button.show()
            Exit_button.show()
            
            window_surface.blit(bg, (0, 0))
            window_surface.blit(TitleText,(235, 25))
            window_surface.blit(VerText,(5, 561))
        
        manager.draw_ui(window_surface)
        pg.display.update()
    
    sys.exit()
        

if __name__ == '__main__':
    main()