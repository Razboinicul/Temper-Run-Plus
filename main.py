import pygame as pg
import sys
import pygame_gui as gui
from engine import *

menu = None

def main():
    global PAUSED, menu
    is_running = True
    """This is the Game's main function"""
    if menu != None:
        menu = None
    pg.init()
    pg.display.set_caption('Temper Run')
    window_surface = pg.display.set_mode((800, 600))
    
    window_surface.fill(pg.Color('#87CEEB'))
    manager = gui.UIManager((800, 600))
    clock = pg.time.Clock()

    pg.font.init() # you have to call this at the start, 
                   # if you want to use this module.
    TitleFont = pg.font.SysFont('Arial', 80)
    VerFont = pg.font.SysFont('Calibri', 40)
    TitleText = TitleFont.render('Temper Run', False, (0, 0, 0))
    VerText = VerFont.render('2.0.0 alpha', False, (0, 0, 0))
    
    
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

    # only 1 game object is needed!
    game = Game()

    
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
                        game_active = True
                        print('OK')
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_p:
                        pause()
                        window_surface.fill(pg.Color('#87CEEB'))
                        resume_button.show()
                if event.user_type == gui.UI_BUTTON_PRESSED:
                    if event.ui_element == About_button:
                        print('Coming Soon')
                if event.user_type == gui.UI_BUTTON_PRESSED:
                    if event.ui_element == GG_button:
                        print('GG!')
                if event.user_type == gui.UI_BUTTON_PRESSED:
                    if event.ui_element == Exit_button:
                        is_running = False   
                
            manager.process_events(event)
        manager.update(time_delta)


        if game_active:
            #if game ongoing update it
            if PAUSED:
                paused()
                PAUSED = False
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
        else:
            window_surface.blit(TitleText,(235, 25))
            window_surface.blit(VerText,(5, 561))
        
        manager.draw_ui(window_surface)
        pg.display.update()
    
    sys.exit()
        

if __name__ == '__main__':
    menu()

