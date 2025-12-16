import pygame
import sys
import os
import random
import math

# --- 1. 定数定義 ---
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
FPS = 60

# 色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)

# 敵タイプ
ENEMY_TYPE_NORMAL = 0
ENEMY_TYPE_WAVY = 1
ENEMY_TYPE_SHOOTER = 2

BOSS_APPEAR_INTERVAL = 150

# --- 2. 必須設定 ---
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- クラス定義 ---

class Bullet(pygame.sprite.Sprite):
    """弾クラス"""
    def __init__(self, x, y, vy, vx=0, is_player_bullet=True, color=WHITE):
        super().__init__()
        size = 10 if is_player_bullet else 8
        self.image = pygame.Surface((size, size))
        if is_player_bullet:
            self.image.fill(color)
        else:
            pygame.draw.circle(self.image, RED, (size//2, size//2), size//2)
            self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect(center=(x, y))
        self.vy = vy
        self.vx = vx

    def update(self):
        self.rect.y += self.vy
        self.rect.x += self.vx
        if (self.rect.bottom < -50 or self.rect.top > SCREEN_HEIGHT + 50 or
            self.rect.left < -50 or self.rect.right > SCREEN_WIDTH + 50):
            self.kill()


class Player(pygame.sprite.Sprite):
    """自機の親クラス"""
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
        self.speed = 5
        self.last_shot_time = 0
        self.shoot_interval = 80

    def update(self):
        keys = pygame.key.get_pressed()
        current_speed = self.speed / 2 if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else self.speed
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= current_speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += current_speed
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= current_speed
        if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += current_speed

    def shoot(self):
        pass


class PlayerBalance(Player):
    """Type A: バランス型（青）"""
    def __init__(self):
        super().__init__()
        self.image.fill(BLUE)
        self.speed = 5
        self.shoot_interval = 80

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > self.shoot_interval:
            for angle in [0, -15, 15]:
                rad = math.radians(angle)
                vx, vy = math.sin(rad)*10, -math.cos(rad)*10
                bullet = Bullet(self.rect.centerx, self.rect.top, vy, vx, True, CYAN)
                all_sprites.add(bullet)
                player_bullets.add(bullet)
            self.last_shot_time = now


class PlayerSpeed(Player):
    """Type B: 高速移動型（赤）"""
    def __init__(self):
        super().__init__()
        self.image.fill(RED)
        self.speed = 8
        self.shoot_interval = 80

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > self.shoot_interval:
            for angle in [0, -15, 15]:
                rad = math.radians(angle)
                vx, vy = math.sin(rad)*10, -math.cos(rad)*10
                bullet = Bullet(self.rect.centerx, self.rect.top, vy, vx, True, (255, 100, 100))
                all_sprites.add(bullet)
                player_bullets.add(bullet)
            self.last_shot_time = now


class PlayerSwitch(Player):
    """Type C: 射撃切替型（黄）"""
    def __init__(self):
        super().__init__()
        self.image.fill(YELLOW)
        self.speed = 5
        self.shoot_mode = 2  # 2WAYスタート
        self.last_toggle_time = 0

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > (80 if self.shoot_mode == 2 else 20):
            if self.shoot_mode == 2:
                angles = [-10, 10]
            else:
                angles = [0]
            for angle in angles:
                rad = math.radians(angle)
                vx, vy = math.sin(rad)*10, -math.cos(rad)*10
                bullet = Bullet(self.rect.centerx, self.rect.top, vy, vx, True, YELLOW)
                all_sprites.add(bullet)
                player_bullets.add(bullet)
            self.last_shot_time = now

    def toggle_mode(self):
        """射撃モードを切り替える"""
        now = pygame.time.get_ticks()
        if now - self.last_toggle_time > 300:
            self.shoot_mode = 1 if self.shoot_mode == 2 else 2
            self.last_toggle_time = now


class Enemy(pygame.sprite.Sprite):
    """ザコ敵"""
    def __init__(self, enemy_type):
        super().__init__()
        self.enemy_type = enemy_type
        self.image = pygame.Surface((30, 30))
        if enemy_type == ENEMY_TYPE_NORMAL:
            self.image.fill(RED)
            self.speed_y = 3
        elif enemy_type == ENEMY_TYPE_WAVY:
            self.image.fill(GREEN)
            self.speed_y = 2
            self.t = 0
        elif enemy_type == ENEMY_TYPE_SHOOTER:
            self.image.fill(YELLOW)
            self.speed_y = 1
            self.shoot_timer = 0
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = -50

    def update(self):
        self.rect.y += self.speed_y
        if self.enemy_type == ENEMY_TYPE_WAVY:
            self.t += 0.1
            self.rect.x += math.sin(self.t)*5
        elif self.enemy_type == ENEMY_TYPE_SHOOTER:
            self.shoot_timer += 1
            if self.shoot_timer > 120:
                self.shoot_at_player()
                self.shoot_timer = 0
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def shoot_at_player(self):
        if player:
            dx, dy = player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery
            angle = math.atan2(dy, dx)
            vx, vy = math.cos(angle)*5, math.sin(angle)*5
            bullet = Bullet(self.rect.centerx, self.rect.centery, vy, vx, False)
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)


class Boss(pygame.sprite.Sprite):
    """ボス"""
    def __init__(self, level=1):
        super().__init__()
        self.image = pygame.Surface((60, 60))
        self.image.fill(PURPLE)
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH//2, -100))
        self.max_hp = 100 * level
        self.hp = self.max_hp
        self.state = "entry"
        self.angle = 0
        self.timer = 0

    def update(self):
        if self.state == "entry":
            self.rect.y += 2
            if self.rect.y >= 100:
                self.state = "battle"
        elif self.state == "battle":
            self.timer += 1
            self.rect.x = (SCREEN_WIDTH//2) + math.sin(self.timer*0.05)*150
            if self.timer % 5 == 0:
                self.shoot_danmaku()

    def shoot_danmaku(self):
        self.angle += 12
        for i in range(0, 360, 90):
            theta = math.radians(self.angle + i)
            vx, vy = math.cos(theta)*4, math.sin(theta)*4
            bullet = Bullet(self.rect.centerx, self.rect.centery, vy, vx, False)
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)

# --- ゲーム初期化 ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("東方風シューティング")
clock = pygame.time.Clock()

try:
    font = pygame.font.SysFont("meiryo", 40)
    small_font = pygame.font.SysFont("meiryo", 24)
except:
    font = pygame.font.Font(None, 40)
    small_font = pygame.font.Font(None, 24)

all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
boss_group = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
player = None

score = 0
next_boss_score = BOSS_APPEAR_INTERVAL
boss_level = 1
is_boss_active = False
selected_char_idx = 0

GAME_STATE_TITLE = 0
GAME_STATE_SELECT = 1
GAME_STATE_PLAYING = 2
GAME_STATE_GAMEOVER = 3
current_state = GAME_STATE_TITLE

# --- メインループ ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # タイトル
        if current_state == GAME_STATE_TITLE:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    current_state = GAME_STATE_SELECT
                elif event.key == pygame.K_ESCAPE:
                    running = False

        # キャラ選択
        elif current_state == GAME_STATE_SELECT:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    selected_char_idx = (selected_char_idx - 1) % 3
                elif event.key == pygame.K_RIGHT:
                    selected_char_idx = (selected_char_idx + 1) % 3
                elif event.key in [pygame.K_SPACE, pygame.K_z]:
                    all_sprites.empty()
                    enemies.empty()
                    boss_group.empty()
                    player_bullets.empty()
                    enemy_bullets.empty()
                    # 選択キャラに応じてインスタンス生成
                    if selected_char_idx == 0:
                        player = PlayerBalance()
                    elif selected_char_idx == 1:
                        player = PlayerSpeed()
                    else:
                        player = PlayerSwitch()
                    all_sprites.add(player)
                    score = 0
                    next_boss_score = BOSS_APPEAR_INTERVAL
                    boss_level = 1
                    is_boss_active = False
                    current_state = GAME_STATE_PLAYING
                elif event.key == pygame.K_ESCAPE:
                    current_state = GAME_STATE_TITLE

        # ゲームオーバー
        elif current_state == GAME_STATE_GAMEOVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                current_state = GAME_STATE_TITLE

    # 更新処理
    if current_state == GAME_STATE_PLAYING and player:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_z]:
            player.shoot()
        if isinstance(player, PlayerSwitch) and keys[pygame.K_x]:
            player.toggle_mode()

        # 敵・ボス出現
        if not is_boss_active and score >= next_boss_score:
            is_boss_active = True
            boss = Boss(boss_level)
            all_sprites.add(boss)
            boss_group.add(boss)
            for e in enemies:
                score += 10
                e.kill()

        if not is_boss_active and random.random() < 0.03:
            t_type = random.choice([ENEMY_TYPE_NORMAL, ENEMY_TYPE_WAVY, ENEMY_TYPE_SHOOTER])
            enemy = Enemy(t_type)
            all_sprites.add(enemy)
            enemies.add(enemy)

        all_sprites.update()

        # 衝突判定
        hits = pygame.sprite.groupcollide(enemies, player_bullets, True, True)
        for _ in hits:
            score += 10

        if is_boss_active:
            boss_hits = pygame.sprite.groupcollide(boss_group, player_bullets, False, True)
            for boss_sprite, bullets in boss_hits.items():
                boss_sprite.hp -= len(bullets)
                score += len(bullets)
                if boss_sprite.hp <= 0:
                    score += 1000
                    boss_sprite.kill()
                    is_boss_active = False
                    boss_level += 1
                    next_boss_score = score + BOSS_APPEAR_INTERVAL

        if (pygame.sprite.spritecollide(player, enemies, False) or
            pygame.sprite.spritecollide(player, enemy_bullets, False) or
            pygame.sprite.spritecollide(player, boss_group, False)):
            current_state = GAME_STATE_GAMEOVER

    # --- 描画処理 ---
    screen.fill(BLACK)
    if current_state == GAME_STATE_TITLE:
        title = font.render("東方風シューティング", True, WHITE)
        start = font.render("スペースキーで次へ", True, YELLOW)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//2 - 60))
        screen.blit(start, (SCREEN_WIDTH//2 - start.get_width()//2, SCREEN_HEIGHT//2 + 20))
    elif current_state == GAME_STATE_SELECT:
        sel_title = font.render("キャラクター選択", True, WHITE)
        screen.blit(sel_title, (SCREEN_WIDTH//2 - sel_title.get_width()//2, 100))
        # Type A
        color_a = BLUE if selected_char_idx == 0 else (50,50,100)
        rect_a = pygame.Rect(SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//2 - 50, 100,100)
        pygame.draw.rect(screen, color_a, rect_a)
        screen.blit(small_font.render("Type A: バランス", True, WHITE), (SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//2 + 60))
        # Type B
        color_b = RED if selected_char_idx == 1 else (100,50,50)
        rect_b = pygame.Rect(SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2 - 50, 100,100)
        pygame.draw.rect(screen, color_b, rect_b)
        screen.blit(small_font.render("Type B: 高速", True, WHITE), (SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2 + 60))
        # Type C
        color_c = YELLOW if selected_char_idx == 2 else (100,100,50)
        rect_c = pygame.Rect(SCREEN_WIDTH//2 + 150, SCREEN_HEIGHT//2 - 50, 100,100)
        pygame.draw.rect(screen, color_c, rect_c)
        screen.blit(small_font.render("Type C: 切替型", True, WHITE), (SCREEN_WIDTH//2 + 150, SCREEN_HEIGHT//2 + 60))
        pygame.draw.rect(screen, YELLOW, [rect_a, rect_b, rect_c][selected_char_idx], 5)
    elif current_state == GAME_STATE_PLAYING:
        all_sprites.draw(screen)
        screen.blit(small_font.render(f"スコア: {score}", True, WHITE), (10, 10))
        if isinstance(player, PlayerSwitch):
            mode_text = small_font.render(f"Mode: {player.shoot_mode}WAY", True, YELLOW)
            screen.blit(mode_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 40))
        if is_boss_active:
            for b in boss_group:
                pygame.draw.rect(screen, RED, (100, 20, 400, 20))
                ratio = b.hp / b.max_hp
                pygame.draw.rect(screen, GREEN, (100, 20, 400 * ratio, 20))
                pygame.draw.rect(screen, WHITE, (100, 20, 400, 20), 2)
    elif current_state == GAME_STATE_GAMEOVER:
        over = font.render("ゲームオーバー", True, RED)
        retry = small_font.render("Rキーでタイトルへ", True, WHITE)
        screen.blit(over, (SCREEN_WIDTH//2 - over.get_width()//2, SCREEN_HEIGHT//2 - 50))
        screen.blit(retry, (SCREEN_WIDTH//2 - retry.get_width()//2, SCREEN_HEIGHT//2 + 20))
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()