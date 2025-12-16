import pygame
import sys
import os
import random
import math

# --- 1. 定数定義 ---
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
FPS = 60

# 色定義 (画像がない場合の代用)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# 敵の種類
ENEMY_TYPE_NORMAL = 0
ENEMY_TYPE_WAVY = 1
ENEMY_TYPE_SHOOTER = 2

# --- 2. 必須設定 (講義資料 P.8, P.10) ---
# 実行環境によるパスのずれを防ぐため、作業ディレクトリをこのファイルのある場所に変更
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Player(pygame.sprite.Sprite):
    """自機クラス"""
    def __init__(self):
        super().__init__()
        # 本来は pygame.image.load("player.png") などを使う
        self.image = pygame.Surface((30, 30))
        self.image.fill(BLUE)  # 自機は青い四角
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)
        self.speed = 5
        self.shoot_delay = 0
        self.last_shot_time = 0

    def update(self):
        # キー入力処理
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed

    def shoot(self):
        """弾を発射するメソッド"""
        # 連射制限
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > 100:  # 100msごとに発射
            bullet = Bullet(self.rect.centerx, self.rect.top, -10, is_player_bullet=True)
            all_sprites.add(bullet)
            player_bullets.add(bullet)
            self.last_shot_time = now


class Enemy(pygame.sprite.Sprite):
    """敵クラス（3種類の挙動）"""
    def __init__(self, enemy_type):
        super().__init__()
        self.enemy_type = enemy_type
        self.image = pygame.Surface((30, 30))
        
        # タイプによって色を変える
        if self.enemy_type == ENEMY_TYPE_NORMAL:
            self.image.fill(RED)
            self.speed_y = 3
        elif self.enemy_type == ENEMY_TYPE_WAVY:
            self.image.fill(GREEN)
            self.speed_y = 2
            self.t = 0  # サイン波用の時間変数
        elif self.enemy_type == ENEMY_TYPE_SHOOTER:
            self.image.fill(YELLOW)
            self.speed_y = 1
            self.shoot_timer = 0

        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = -50 # 画面外から出現

    def update(self):
        # 共通：下に移動
        self.rect.y += self.speed_y

        # タイプ別の動き
        if self.enemy_type == ENEMY_TYPE_WAVY:
            # 蛇行運転 (サイン波)
            self.t += 0.1
            self.rect.x += math.sin(self.t) * 5

        elif self.enemy_type == ENEMY_TYPE_SHOOTER:
            # 定期的に弾を撃つ
            self.shoot_timer += 1
            if self.shoot_timer > 120:  # 約2秒ごとに発射
                self.shoot_at_player()
                self.shoot_timer = 0

        # 画面外に出たら消える
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def shoot_at_player(self):
        """自機に向かって弾を撃つ"""
        # 自機の位置を取得（簡易的にplayer変数を参照）
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        angle = math.atan2(dy, dx)
        speed = 5
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        
        bullet = Bullet(self.rect.centerx, self.rect.centery, vy, vx, is_player_bullet=False)
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)


class Bullet(pygame.sprite.Sprite):
    """弾クラス（自機・敵共用）"""
    def __init__(self, x, y, vy, vx=0, is_player_bullet=True):
        super().__init__()
        size = 10 if is_player_bullet else 8
        self.image = pygame.Surface((size, size))
        color = WHITE if is_player_bullet else RED
        
        # 丸い弾を描画
        pygame.draw.circle(self.image, color, (size//2, size//2), size//2)
        # 背景を透明にする処理（黒を透過）
        self.image.set_colorkey(BLACK) 
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.vy = vy
        self.vx = vx

    def update(self):
        self.rect.y += self.vy
        self.rect.x += self.vx
        # 画面外に出たら消える
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or \
           self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.kill()


# --- 3. ゲームの初期化 ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Touhou Style Shooter Base")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36) # デフォルトフォント

# スプライトグループの作成
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()

# プレイヤーの生成
player = Player()
all_sprites.add(player)

# ゲームの状態管理
GAME_STATE_TITLE = 0
GAME_STATE_PLAYING = 1
GAME_STATE_GAMEOVER = 2
current_state = GAME_STATE_TITLE

score = 0

# --- 4. ゲームループ ---
running = True
while running:
    # 1. イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if current_state == GAME_STATE_TITLE:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                # ゲーム開始（リセット）
                all_sprites.empty()
                enemies.empty()
                player_bullets.empty()
                enemy_bullets.empty()
                player = Player()
                all_sprites.add(player)
                score = 0
                current_state = GAME_STATE_PLAYING

        elif current_state == GAME_STATE_PLAYING:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_z:
                # Zキーで発射（東方風操作）
                pass # 押しっぱなしは下のキー状態取得で処理

        elif current_state == GAME_STATE_GAMEOVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                current_state = GAME_STATE_TITLE

    # 2. 更新処理 & 描画処理
    screen.fill(BLACK) # 背景は黒

    if current_state == GAME_STATE_TITLE:
        title_text = font.render("Touhou Style Shooter", True, WHITE)
        start_text = font.render("Press SPACE to Start", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 - 50))
        screen.blit(start_text, (SCREEN_WIDTH//2 - 130, SCREEN_HEIGHT//2 + 10))

    elif current_state == GAME_STATE_PLAYING:
        # プレイヤーの操作（押しっぱなし対応）
        keys = pygame.key.get_pressed()
        if keys[pygame.K_z]:
            player.shoot()

        # 敵の出現（ランダム）
        if random.random() < 0.02: # 2%の確率で毎フレーム出現
            t_type = random.choice([ENEMY_TYPE_NORMAL, ENEMY_TYPE_NORMAL, ENEMY_TYPE_WAVY, ENEMY_TYPE_SHOOTER])
            enemy = Enemy(t_type)
            all_sprites.add(enemy)
            enemies.add(enemy)

        # 全スプライトの更新
        all_sprites.update()

        # 衝突判定 1: プレイヤーの弾 -> 敵
        hits = pygame.sprite.groupcollide(enemies, player_bullets, True, True)
        for hit in hits:
            score += 10
            # ここに爆発エフェクトなどを追加可能

        # 衝突判定 2: 敵 または 敵の弾 -> プレイヤー (被弾処理)
        # 敵本体との衝突
        if pygame.sprite.spritecollide(player, enemies, False):
            current_state = GAME_STATE_GAMEOVER
        # 敵の弾との衝突
        if pygame.sprite.spritecollide(player, enemy_bullets, False):
            current_state = GAME_STATE_GAMEOVER

        # 描画
        all_sprites.draw(screen)
        
        # スコア表示
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

    elif current_state == GAME_STATE_GAMEOVER:
        over_text = font.render("GAME OVER", True, RED)
        score_res_text = font.render(f"Final Score: {score}", True, WHITE)
        retry_text = font.render("Press R to Retry", True, WHITE)
        screen.blit(over_text, (SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2 - 50))
        screen.blit(score_res_text, (SCREEN_WIDTH//2 - 90, SCREEN_HEIGHT//2))
        screen.blit(retry_text, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 50))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()