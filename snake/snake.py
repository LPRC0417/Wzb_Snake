def main_loop(snake_speed, snake, snake_direction, fruits, last_fruit_time, game_over, score, clock):
    running = True
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over:
                reset_game(snake, snake_direction, fruits, last_fruit_time, game_over, score)
            elif event.key == pygame.K_SPACE:
                paused = not paused
    
    # 手势识别
    ret, frame = cap.read()
    if ret:
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        
        # 绘制手势骨架
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    
    # 清屏和绘制界面
    screen.fill(BLACK)
    pygame.draw.rect(screen, WHITE, main_rect, 1)
    pygame.draw.rect(screen, WHITE, side_rect, 1)
    
    if not game_over and not paused:
        # 根据速度调整移动间隔 (速度1=600ms, 速度5=100ms)
        move_interval = max(100, 600 - (snake_speed-1)*125)
        if current_time - last_move_time >= move_interval:  # 精确时间控制
            last_move_time = current_time
            # 移动蛇
            head = snake[0].copy()
            if snake_direction == "LEFT":
                head[0] -= snake_block
            elif snake_direction == "RIGHT":
                head[0] += snake_block
            elif snake_direction == "UP":
                head[1] -= snake_block
            elif snake_direction == "DOWN":
                head[1] += snake_block
            
            # 记录蛇头轨迹
            snake_trail.append(head.copy())
            if len(snake_trail) > MAX_TRAIL_LENGTH:
                snake_trail.pop(0)
            
            # 检查碰撞
            # 放宽边界条件，允许蛇头稍微超出边界
            if (head[0] < -snake_block or head[0] >= MAIN_WIDTH + snake_block or
                head[1] < -snake_block or head[1] >= SCREEN_HEIGHT + snake_block or
                head in snake[1:]):
                game_over = True
                loser_sound.play()
            
            snake.insert(0, head)
            
            # 检查是否吃到果实
            for fruit in fruits[:]:
                if head == fruit:
                    fruits.remove(fruit)
                    score += 1  # 吃到果实分数加1
                    # 添加吃到果实的粒子效果
                    for _ in range(20):
                        particle_pos = [head[0] + random.randint(-10, 10), 
                                      head[1] + random.randint(-10, 10)]
                        particle_color = (random.randint(200, 255), 
                                        random.randint(0, 100), 
                                        random.randint(0, 100))
                        pygame.draw.circle(screen, particle_color, 
                                         (particle_pos[0], particle_pos[1]), 
                                         random.randint(2, 4))
                    pygame.display.update()
                    pygame.time.delay(50)  # 短暂显示粒子效果
                    break  # 吃到果实后不移除蛇尾，使蛇变长
            else:
                snake.pop()  # 没吃到果实才移除蛇尾
            
            # 20秒刷新果实
            if current_time - last_fruit_time >= fruit_interval:
                generate_fruits()
    
    # 绘制游戏元素
    # 绘制蛇的拖尾效果
    for i, pos in enumerate(snake_trail):
        alpha = int(255 * (i/MAX_TRAIL_LENGTH))  # 渐隐效果
        trail_color = (0, 200, 0, alpha)
        trail_surface = pygame.Surface((snake_block, snake_block), pygame.SRCALPHA)
        pygame.draw.rect(trail_surface, trail_color, 
                        [0, 0, snake_block, snake_block], border_radius=3)
        screen.blit(trail_surface, [pos[0], pos[1]])
    
    draw_snake()
    draw_fruits()
    
    # 显示分数和状态
    # ... (省略了显示分数和状态的代码)
    
    # 更新屏幕
    pygame.display.update()
    clock.tick(FPS)  # 保持60FPS的稳定帧率

import pygame
import random
import sys
import cv2
import mediapipe as mp

# 初始化pygame
pygame.init()
# 初始化混音器
pygame.mixer.init()
# 加载音效
try:
    background_music = pygame.mixer.Sound("background.mp3")
    choose_sound = pygame.mixer.Sound("choose.mp3") 
    loser_sound = pygame.mixer.Sound("loser.mp3")
    background_music.set_volume(0.5)  # 降低背景音乐音量
except:
    print("警告：未能加载全部音效文件")

# 初始化MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# 初始化摄像头
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# 屏幕设置
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
MAIN_WIDTH = 800
SIDE_WIDTH = 400

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# 创建屏幕
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("贪吃蛇游戏")

# 窗口创建成功后开始播放背景音乐
try:
    if 'background_music' in globals():
        background_music.play(loops=-1)
except:
    print("警告：背景音乐播放失败")

# 游戏区域划分
main_rect = pygame.Rect(0, 0, MAIN_WIDTH, SCREEN_HEIGHT)
side_rect = pygame.Rect(MAIN_WIDTH, 0, SIDE_WIDTH, SCREEN_HEIGHT)

# 贪吃蛇设置
snake_block = 20
global snake_speed
snake_speed = 1  # 每秒移动1格
snake = [[MAIN_WIDTH//2, SCREEN_HEIGHT//2]]
snake_trail = []  # 存储蛇的移动轨迹
MAX_TRAIL_LENGTH = 10  # 最大轨迹长度
snake_direction = "RIGHT"

# 果实设置
fruits = []
last_fruit_time = 0
fruit_interval = 20000  # 20秒刷新一次

# 游戏状态
game_over = False
paused = False  # 暂停状态
score = 0  # 初始化分数
clock = pygame.time.Clock()
FPS = 60  # 设置目标帧率
last_move_time = 0  # 记录上次移动时间

def draw_snake():
    for i, pos in enumerate(snake):
        # 蛇头使用不同颜色
        if i == 0:
            # 头部基础颜色
            base_color = (0, 255, 0)
            # 添加高光效果
            highlight = pygame.Surface((snake_block, snake_block), pygame.SRCALPHA)
            highlight.fill((0, 0, 0, 0))  # 确保透明背景
            pygame.draw.rect(highlight, (255, 255, 255, 50), 
                            [0, 0, snake_block, snake_block//3], border_radius=5)
            
            # 绘制蛇头
            pygame.draw.rect(screen, base_color, 
                           [pos[0], pos[1], snake_block, snake_block], border_radius=5)
            screen.blit(highlight, [pos[0], pos[1]])
            
            # 根据移动方向调整眼睛位置
            eye_offset_x = snake_block // 3
            eye_offset_y = snake_block // 3
            
            if snake_direction == "RIGHT":
                left_eye = (pos[0] + snake_block - eye_offset_x, pos[1] + eye_offset_y)
                right_eye = (pos[0] + snake_block - eye_offset_x, pos[1] + snake_block - eye_offset_y)
                pupil_offset = 1  # 瞳孔偏移量
            elif snake_direction == "LEFT":
                left_eye = (pos[0] + eye_offset_x, pos[1] + eye_offset_y)
                right_eye = (pos[0] + eye_offset_x, pos[1] + snake_block - eye_offset_y)
                pupil_offset = -1
            elif snake_direction == "UP":
                left_eye = (pos[0] + eye_offset_x, pos[1] + eye_offset_y)
                right_eye = (pos[0] + snake_block - eye_offset_x, pos[1] + eye_offset_y)
                pupil_offset = -1
            else:  # DOWN
                left_eye = (pos[0] + eye_offset_x, pos[1] + snake_block - eye_offset_y)
                right_eye = (pos[0] + snake_block - eye_offset_x, pos[1] + snake_block - eye_offset_y)
                pupil_offset = 1
            
            # 添加眼睛和瞳孔
            pygame.draw.circle(screen, (255, 255, 255), left_eye, 4)
            pygame.draw.circle(screen, (255, 255, 255), right_eye, 4)
            pygame.draw.circle(screen, (0, 0, 0), 
                             (left_eye[0] + pupil_offset, left_eye[1]), 2)
            pygame.draw.circle(screen, (0, 0, 0), 
                             (right_eye[0] + pupil_offset, right_eye[1]), 2)
        else:
            # 蛇身使用更丰富的渐变效果
            base_shade = max(100, 255 - i*5)
            dark_shade = max(50, base_shade - 30)
            light_shade = min(255, base_shade + 30)
            
            # 绘制渐变效果
            pygame.draw.rect(screen, (0, dark_shade, 0), 
                           [pos[0], pos[1], snake_block, snake_block], border_radius=3)
            
            # 添加高光
            highlight = pygame.Surface((snake_block, snake_block//3), pygame.SRCALPHA)
            highlight.fill((0, 0, 0, 0))  # 确保透明背景
            pygame.draw.rect(highlight, (light_shade, 255, light_shade, 30), 
                           [0, 0, snake_block, snake_block//3], border_radius=3)
            screen.blit(highlight, [pos[0], pos[1]])
            
            # 添加鳞片纹理
            for y in range(0, snake_block, 3):
                shade = min(255, max(0, base_shade+20))  # 确保颜色值在0-255范围内
                pygame.draw.line(screen, (0, shade, 0), 
                               (pos[0]+2, pos[1]+y), 
                               (pos[0]+snake_block-2, pos[1]+y), 1)

def generate_fruits():
    global fruits, last_fruit_time
    fruits = []
    for _ in range(4):  # 生成4个果实
        while True:
            x = random.randrange(20, MAIN_WIDTH - 40, snake_block)
            y = random.randrange(20, SCREEN_HEIGHT - 40, snake_block)
            # 确保果实不靠近边缘
            if (20 < x < MAIN_WIDTH - 40 and 
                20 < y < SCREEN_HEIGHT - 40):
                break
        fruits.append([x, y])
    last_fruit_time = pygame.time.get_ticks()

def draw_fruits():
    fruit_images = [
        pygame.Surface((snake_block, snake_block), pygame.SRCALPHA),
        pygame.Surface((snake_block, snake_block), pygame.SRCALPHA)
    ]
    # 创建不同水果图案
    pygame.draw.circle(fruit_images[0], (255, 0, 0), 
                      (snake_block//2, snake_block//2), snake_block//2)  # 红苹果
    pygame.draw.circle(fruit_images[1], (255, 165, 0), 
                      (snake_block//2, snake_block//2), snake_block//2)  # 橙子
    
    for i, fruit in enumerate(fruits):
        # 循环使用不同水果图案
        screen.blit(fruit_images[i % len(fruit_images)], 
                  [fruit[0], fruit[1], snake_block, snake_block])

def show_game_over():
    font = pygame.font.SysFont(None, 55)
    text = font.render("Game Over", True, RED)
    screen.blit(text, [MAIN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 50])
    
    # 显示最终分数
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, [MAIN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 80])
    
    # 重新开始按钮
    pygame.draw.rect(screen, GREEN, 
                    [MAIN_WIDTH//2 - 75, SCREEN_HEIGHT//2 + 20, 150, 50])
    restart_text = font.render("Restart", True, BLACK)
    screen.blit(restart_text, [MAIN_WIDTH//2 - 60, SCREEN_HEIGHT//2 + 30])

def show_pause_menu():
    global font_normal  # 声明为全局变量
    
    # 创建半透明背景
    s = pygame.Surface((MAIN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    s.fill((0, 0, 0, 180))  # 半透明黑色
    screen.blit(s, (0, 0))
    
    font_large = pygame.font.SysFont(None, 72)
    font_normal = pygame.font.SysFont(None, 48)  # 确保在所有函数中都能访问
    
    # 暂停标题
    title = font_large.render("Game Pause", True, WHITE)
    screen.blit(title, [MAIN_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//4])
    
    # 速度调节区域 (将变量定义移到函数开始)
    global minus_rect, plus_rect, speed_rect
    
    speed_rect = pygame.Rect(MAIN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 60, 200, 50)
    minus_rect = pygame.Rect(speed_rect.left - 40, speed_rect.top, 40, 50)
    plus_rect = pygame.Rect(speed_rect.right, speed_rect.top, 40, 50)
    
    # 减号按钮
    pygame.draw.rect(screen, (200, 200, 200), minus_rect, border_radius=5)
    pygame.draw.rect(screen, (150, 150, 150), minus_rect, 2, border_radius=5)
    minus_text = font_normal.render("-", True, BLACK)
    screen.blit(minus_text, [minus_rect.centerx - minus_text.get_width()//2, 
                           minus_rect.centery - minus_text.get_height()//2])
    
    # 速度显示
    pygame.draw.rect(screen, (240, 240, 240), speed_rect, border_radius=5)
    pygame.draw.rect(screen, (200, 200, 200), speed_rect, 2, border_radius=5)
    speed_text = font_normal.render(f"Speed: {snake_speed}", True, BLACK)
    screen.blit(speed_text, [speed_rect.centerx - speed_text.get_width()//2, 
                           speed_rect.centery - speed_text.get_height()//2])
    
    # 加号按钮
    pygame.draw.rect(screen, (200, 200, 200), plus_rect, border_radius=5)
    pygame.draw.rect(screen, (150, 150, 150), plus_rect, 2, border_radius=5)
    plus_text = font_normal.render("+", True, BLACK)
    screen.blit(plus_text, [plus_rect.centerx - plus_text.get_width()//2, 
                          plus_rect.centery - plus_text.get_height()//2])
    
    # 继续游戏按钮
    pygame.draw.rect(screen, GREEN, [MAIN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 20, 200, 50])
    resume_text = font_normal.render("Continue", True, BLACK)
    screen.blit(resume_text, [MAIN_WIDTH//2 - resume_text.get_width()//2, SCREEN_HEIGHT//2 + 35])
    
    # 退出游戏按钮
    pygame.draw.rect(screen, RED, [MAIN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 100, 200, 50])
    quit_text = font_normal.render("Quit", True, BLACK)
    screen.blit(quit_text, [MAIN_WIDTH//2 - quit_text.get_width()//2, SCREEN_HEIGHT//2 + 115])

def reset_game():
    global snake, snake_direction, fruits, last_fruit_time, game_over, score
    snake = [[MAIN_WIDTH//2, SCREEN_HEIGHT//2]]
    snake_direction = "RIGHT"
    fruits = []
    last_fruit_time = pygame.time.get_ticks()
    game_over = False
    score = 0  # 重置分数
    generate_fruits()

# 初始生成果实
generate_fruits()

def show_start_menu():
    global font_normal  # 声明为全局变量
    
    # 创建渐变背景
    for i in range(SCREEN_HEIGHT):
        # 计算渐变颜色 (从深绿到黑)
        color = (0, max(0, 80 - int(i/SCREEN_HEIGHT*80)), 0)
        pygame.draw.line(screen, color, (0, i), (SCREEN_WIDTH, i))
    
    # 显示带阴影的大标题
    font_title = pygame.font.Font(None, 120)
    
    # 阴影效果
    shadow = font_title.render("SNAKE", True, (50, 50, 50))
    screen.blit(shadow, [SCREEN_WIDTH//2 - shadow.get_width()//2 + 5, SCREEN_HEIGHT//4 + 5])
    
    # 主标题
    title = font_title.render("SNAKE", True, (100, 255, 100))
    screen.blit(title, [SCREEN_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//4])
    
    # 获取鼠标位置
    mouse_pos = pygame.mouse.get_pos()
    
    # 开始按钮 (带悬停效果)
    start_button = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 200, 50)
    start_hover = start_button.collidepoint(mouse_pos)
    button_color = (100, 255, 100) if start_hover else (0, 200, 0)
    pygame.draw.rect(screen, button_color, start_button, border_radius=10)
    pygame.draw.rect(screen, (150, 255, 150), start_button, 3, border_radius=10)
    
    font_button = pygame.font.Font(None, 48)
    start_text = font_button.render("Start", True, (20, 20, 20))
    screen.blit(start_text, [SCREEN_WIDTH//2 - start_text.get_width()//2, SCREEN_HEIGHT//2 + 10])
    
    # 退出按钮 (带悬停效果)
    quit_button = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 80, 200, 50)
    quit_hover = quit_button.collidepoint(mouse_pos)
    button_color = (255, 100, 100) if quit_hover else (200, 0, 0)
    pygame.draw.rect(screen, button_color, quit_button, border_radius=10)
    pygame.draw.rect(screen, (255, 150, 150), quit_button, 3, border_radius=10)
    
    quit_text = font_button.render("Quit", True, (20, 20, 20))
    screen.blit(quit_text, [SCREEN_WIDTH//2 - quit_text.get_width()//2, SCREEN_HEIGHT//2 + 90])
    
    pygame.display.update()
    return start_button, quit_button  # 返回按钮区域用于点击检测

# 游戏主循环
running = True
in_start_menu = True
while running:
    current_time = pygame.time.get_ticks()
    
    if in_start_menu:
        start_button, quit_button = show_start_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                cap.release()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                # 检查是否点击了开始按钮
                if start_button.collidepoint(mouse_pos):
                    choose_sound.play()
                    in_start_menu = False
                    reset_game()
                # 检查是否点击了退出按钮
                elif quit_button.collidepoint(mouse_pos):
                    choose_sound.play()
                    running = False
                    cap.release()
        continue
    
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            cap.release()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over:  # 按R键重新开始
                choose_sound.play()
                reset_game()
            elif event.key == pygame.K_SPACE:  # 空格键暂停/继续
                choose_sound.play()
                paused = not paused
                
        # 处理暂停菜单点击
        if paused and event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            # 检查是否点击了继续按钮
            if (MAIN_WIDTH//2 - 100 <= mouse_pos[0] <= MAIN_WIDTH//2 + 100 and
                SCREEN_HEIGHT//2 + 20 <= mouse_pos[1] <= SCREEN_HEIGHT//2 + 70):
                paused = False
            # 检查是否点击了减号按钮
            elif minus_rect.collidepoint(mouse_pos):
                choose_sound.play()
                snake_speed = max(1, snake_speed - 1)  # 最小速度为1
                choose_sound.play()
                # 显示速度变化提示
                speed_change_text = font_normal.render(f"Speed set to {snake_speed}", True, WHITE)
                screen.blit(speed_change_text, [MAIN_WIDTH//2 - speed_change_text.get_width()//2, 
                                              SCREEN_HEIGHT//2 + 150])
                pygame.display.update()
                pygame.time.delay(300)  # 短暂显示提示
            # 检查是否点击了加号按钮
            elif plus_rect.collidepoint(mouse_pos):
                snake_speed = min(5, snake_speed + 1)  # 最大速度为5
                choose_sound.play()
                # 显示速度变化提示
                speed_change_text = font_normal.render(f"Speed set to {snake_speed}", True, WHITE)
                screen.blit(speed_change_text, [MAIN_WIDTH//2 - speed_change_text.get_width()//2, 
                                              SCREEN_HEIGHT//2 + 150])
                pygame.display.update()
                pygame.time.delay(300)  # 短暂显示提示
            # 检查是否点击了退出按钮
            elif (MAIN_WIDTH//2 - 100 <= mouse_pos[0] <= MAIN_WIDTH//2 + 100 and
                  SCREEN_HEIGHT//2 + 100 <= mouse_pos[1] <= SCREEN_HEIGHT//2 + 150):
                running = False
    
    # 手势识别
    ret, frame = cap.read()
    if ret:
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        
        # 绘制手势骨架
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # 获取关键点坐标
                wrist = hand_landmarks.landmark[0]
                thumb_tip = hand_landmarks.landmark[4]
                index_tip = hand_landmarks.landmark[8]
                middle_tip = hand_landmarks.landmark[12]
                ring_tip = hand_landmarks.landmark[16]
                pinky_tip = hand_landmarks.landmark[20]
                index_mcp = hand_landmarks.landmark[5]
                
                # 计算方向向量
                dx = index_tip.x - index_mcp.x
                dy = index_tip.y - index_mcp.y
                
                # 确定方向
                if not game_over:
                    if abs(dx) > abs(dy):
                        if dx > 0.1 and snake_direction != "LEFT":
                            snake_direction = "RIGHT"
                        elif dx < -0.1 and snake_direction != "RIGHT":
                            snake_direction = "LEFT"
                    else:
                        if dy > 0.1 and snake_direction != "UP":  # 修正方向判断
                            snake_direction = "DOWN"
                        elif dy < -0.1 and snake_direction != "DOWN":
                            snake_direction = "UP"
                
                # 显示识别方向
                direction_text = ""
                if abs(dx) > abs(dy):
                    direction_text = "RIGHT" if dx > 0 else "LEFT"
                else:
                    direction_text = "DOWN" if dy > 0 else "UP"
                cv2.putText(frame, f"Direction: {direction_text}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 255, 0), 2)
    
    # 清屏
    screen.fill(BLACK)
    
    # 绘制界面分割
    pygame.draw.rect(screen, WHITE, main_rect, 1)
    pygame.draw.rect(screen, WHITE, side_rect, 1)
    
    if not game_over and not paused:  # 游戏未结束且未暂停时才移动
        # 根据速度调整移动间隔 (速度1=600ms, 速度5=100ms)
        move_interval = max(100, 600 - (snake_speed-1)*125)
        if current_time - last_move_time >= move_interval:  # 精确时间控制
            last_move_time = current_time
            # 移动蛇
            head = snake[0].copy()
            if snake_direction == "LEFT":
                head[0] -= snake_block
            elif snake_direction == "RIGHT":
                head[0] += snake_block
            elif snake_direction == "UP":
                head[1] -= snake_block
            elif snake_direction == "DOWN":
                head[1] += snake_block
            
            # 检查碰撞
            # 放宽边界条件，允许蛇头稍微超出边界
            if (head[0] < -snake_block or head[0] >= MAIN_WIDTH + snake_block or
                head[1] < -snake_block or head[1] >= SCREEN_HEIGHT + snake_block or
                head in snake[1:]):
                game_over = True
            
            snake.insert(0, head)
            
            # 检查是否吃到果实
            for fruit in fruits[:]:
                if head == fruit:
                    fruits.remove(fruit)
                    score += 1  # 吃到果实分数加1
                    break  # 吃到果实后不移除蛇尾，使蛇变长
            else:
                snake.pop()  # 没吃到果实才移除蛇尾
            
            # 20秒刷新果实
            if current_time - last_fruit_time >= fruit_interval:
                generate_fruits()
    
    # 绘制游戏元素
    draw_snake()
    draw_fruits()
    
    # 在左上角显示当前分数
    font = pygame.font.SysFont(None, 36)
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, [20, 20])
    
    if game_over:
        show_game_over()
    elif paused:
        show_pause_menu()
    
    # 在右侧显示摄像头画面和方向
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (SIDE_WIDTH, SCREEN_HEIGHT//2))
        frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        screen.blit(frame, (MAIN_WIDTH, 0))
        
        # 在右侧下方显示当前方向
        if results.multi_hand_landmarks:
            font = pygame.font.SysFont(None, 48)
            direction_surface = font.render(f"Direction: {direction_text}", True, GREEN)
            screen.blit(direction_surface, (MAIN_WIDTH + 20, SCREEN_HEIGHT//2 + 20))
    
    pygame.display.update()
    clock.tick(60)

pygame.quit()
cap.release()
sys.exit()
