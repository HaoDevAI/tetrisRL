import sys

import pygame

from src.utils.display import *
from src.env.env import TetrisEnv
from src.agents.agent import TetrisAgent


DROP_EVENT = pygame.USEREVENT + 1
AGENT_ACTION_EVENT = pygame.USEREVENT

def main():
    """
    Main game loop.
    """
    pygame.init()
    screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Tetris: Human vs AI")
    clock = pygame.time.Clock()

    running = True
    player_name = ""
    print(INITIAL_WIDTH, INITIAL_HEIGHT)
    print(scale_factor)
    while running:
        dt = clock.tick(ui_config["fps"])
        if not player_name:
            player_name = enter_name(screen, font)

        mode = choose_mode(screen, font)
        mode = mode.lower()

        env_human = TetrisEnv(env_params["rows"],
                              env_params["cols"],
                              env_params["piece_generator"],
                              env_params["random_seed"],
                              mode_weights[mode]["level"])
        env_agent = TetrisEnv(env_params["rows"],
                              env_params["cols"],
                              env_params["piece_generator"],
                              env_params["random_seed"],
                              mode_weights[mode]["level"])

        agent = TetrisAgent(
            env_agent,
            mode_weights[mode]["weights"],
            mode_weights[mode]["strategy"])

        AGENT_ACTION_DELAY = mode_weights[mode]["delay"]

        pygame.time.set_timer(AGENT_ACTION_EVENT, AGENT_ACTION_DELAY)

        agent_actions = []
        game_active = True

        while game_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_active = False
                    running = False
                elif event.type == AGENT_ACTION_EVENT:
                    if not agent_actions:
                        best_move = agent.get_best_move()
                        if best_move is not None:
                            actions = []
                            for _ in range(best_move["rotations"]):
                                actions.append(("rotate", True))
                            dx = best_move["x"] - env_agent.current_piece.x
                            if dx > 0:
                                for _ in range(dx):
                                    actions.append(("move", 1))
                            elif dx < 0:
                                for _ in range(-dx):
                                    actions.append(("move", -1))
                            actions.append(("drop", None))
                            agent_actions = actions
                    else:
                        action, value = agent_actions.pop(0)
                        if action == "rotate":
                            env_agent.rotate_piece(clockwise=value)
                        elif action == "move":
                            env_agent.move_piece(value, 0)
                        elif action == "drop":
                            env_agent.hard_drop()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        env_human.move_piece(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        env_human.move_piece(1, 0)
                    elif event.key == pygame.K_DOWN:
                        env_human.move_piece(0, 1)
                    elif event.key == pygame.K_SPACE:
                        env_human.hard_drop()
                    elif event.key == pygame.K_UP:
                        env_human.rotate_piece(clockwise=True)
                    elif event.key == pygame.K_c:
                        env_human.swap_piece()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if pause_button_rect.collidepoint(event.pos):
                        pygame.time.set_timer(AGENT_ACTION_EVENT, 0)
                        check = draw_pause_menu(screen, font)
                        if check == "resume":
                            screen.fill(ui_config["background_color"])
                            pygame.time.set_timer(AGENT_ACTION_EVENT, AGENT_ACTION_DELAY)
                        elif check == "restart":
                            play_again = True
                            game_active = False
                        elif check == "quit":
                            play_again = False
                            game_active = False

            env_human.update(dt)
            env_agent.update(dt)

            screen.fill(ui_config["background_color"])
            draw_grid(0, screen, env_human.grid.board)
            draw_grid(1, screen, env_agent.grid.board)
            ghost_piece_human = env_human.get_ghost_piece()
            draw_ghost_piece(0, screen, ghost_piece_human)
            ghost_piece_agent = env_agent.get_ghost_piece()
            draw_ghost_piece(1, screen, ghost_piece_agent)
            draw_piece(0, screen, env_human.current_piece.get_cells(), env_human.current_piece.color)
            draw_piece(1, screen, env_agent.current_piece.get_cells(), env_agent.current_piece.color)
            pause_button_rect = draw_panel(0, screen, env_human, font, mode)
            draw_panel(1, screen, env_agent, font, mode)


            if env_human.game_over:
                draw_game_over(0, screen, font)
                if env_human.score < env_agent.score:
                    env_agent.game_over = True
                    play_again = check_play_again(screen, font, winner="agent")
                    if play_again:
                        game_active = False
                        check = "restart"
                    else:
                        game_active = False
                        running = False
            elif env_agent.game_over:
                draw_game_over(1, screen, font)
                if env_agent.score < env_human.score:
                    env_human.game_over = True
                    play_again = check_play_again(screen, font, winner="player")
                    if play_again:
                        game_active = False
                        check = "restart"
                    else:
                        game_active = False
                        running = False
            elif env_human.game_over and env_agent.game_over:
                if env_human.score > env_agent.score:
                    play_again = check_play_again(screen, font, winner="player")
                elif env_human.score < env_agent.score:
                    play_again = check_play_again(screen, font, winner="agent")
                if play_again:
                    game_active = False
                    check = "restart"
            if not game_active:
                save_score(player_name, env_human.score)

                # Option to play again with different name
                if play_again == True and check != "quit":
                    # Ask if player wants to change name
                    change_name = ask_change_name(screen, font)
                    if change_name:
                        player_name = ""  # Reset name
                else:
                    running = False
            pygame.display.flip()
            clock.tick(ui_config["fps"])
    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()
