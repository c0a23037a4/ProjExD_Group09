import math
import os
import random
import sys
import time
import pygame as pg

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Gravity(pg.sprite.Sprite):
    """
    重力場に関するクラス
    """
    def __init__(self, life: int):
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        self.image.fill((0, 0, 0, 128))  # 透明度128の黒い矩形
        self.rect = self.image.get_rect()
        self.life = life

    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def draw_charge_indicator(screen, is_charged):
    """
    チャージショットの状態を示す四角形を描画する
    引数:
        screen: 描画先の画面
        is_charged: チャージショットが完了しているかのフラグ（True/False）
    """
    color = (0, 255, 0) if is_charged else (255, 0, 0)  # 緑: 完了, 赤: 未完了
    pg.draw.rect(screen, color, (WIDTH - 80, HEIGHT - 80, 50, 50))  # 右下に四角形を描画


class ChargeBar:
    """
    チャージ量を表示するバーに関するクラス
    """
    def __init__(self):
        self.charge_time = 0  # チャージ時間
        self.max_charge = 50  # 最大チャージ時間
        self.bar_width = 300  # チャージバーの幅
        self.bar_height = 20  # チャージバーの高さ
        self.bar_pos = (WIDTH - 350, HEIGHT - 50)  # バーの位置

    def update(self, charging: bool, screen: pg.Surface):
        """
        チャージ時間の管理と描画
        引数:
            charging: チャージ中かどうかのフラグ（True/False）
            screen: 描画先の画面
        """
        if charging:
            self.charge_time += 1
            if self.charge_time > self.max_charge:
                self.charge_time = self.max_charge  # 最大値を超えない
        else:
            self.charge_time = 0  # チャージ解除でリセット

        # チャージバーの描画
        filled_width = (self.charge_time / self.max_charge) * self.bar_width
        pg.draw.rect(screen, (100, 100, 100), (*self.bar_pos, self.bar_width, self.bar_height))
        pg.draw.rect(screen, (255, 0, 0), (*self.bar_pos, filled_width, self.bar_height))


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    def __init__(self, num: int, xy: tuple[int, int]):
        super().__init__()
        img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        self.image = pg.transform.flip(img, True, False)
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in {
            pg.K_UP: (0, -1),
            pg.K_DOWN: (0, +1),
            pg.K_LEFT: (-1, 0),
            pg.K_RIGHT: (+1, 0),
        }.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed * sum_mv[0], self.speed * sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed * sum_mv[0], -self.speed * sum_mv[1])
        screen.blit(self.image, self.rect)


class Beam:
    """
    通常の弾とチャージショットに関するクラス
    """
    def __init__(self, bird: "Bird", max_charged: bool):
        self.beams = []  # 複数のビームを格納するリスト
        if max_charged:  # MAXチャージ時は5本のビームを生成
            for i in range(-2, 3):  # 5本のビームを上下に1pxずつずらす
                beam_img = pg.transform.scale(pg.image.load("fig/BEEM1.png"), (300, 75))
                beam_rct = beam_img.get_rect()
                beam_rct.centery = bird.rect.centery + i * 0.01 #ここいじったらビームの重なり方が代わるよ
                beam_rct.left = bird.rect.right
                self.beams.append({"img": beam_img, "rct": beam_rct, "vx": 20})
        else:  # 通常弾
            beam_img = pg.image.load("fig/beam.png")
            beam_rct = beam_img.get_rect()
            beam_rct.centery = bird.rect.centery
            beam_rct.left = bird.rect.right
            self.beams.append({"img": beam_img, "rct": beam_rct, "vx": 10})

    def update(self, screen: pg.Surface):
        """
        ビームの移動と描画
        """
        for beam in self.beams:
            if check_bound(beam["rct"]) == (True, True):
                beam["rct"].move_ip(beam["vx"], 0)
                screen.blit(beam["img"], beam["rct"])


class Score:
    """
    スコア表示に関するクラス
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0

    def update(self, screen: pg.Surface):
        score_img = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(score_img, (100, HEIGHT - 50))


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    flip_bg_img = pg.transform.flip(bg_img, True, False)
    score = Score()
    bird = Bird(3, (900, 400))
    charge_bar = ChargeBar()  # チャージバーのインスタンス
    beams = []
    clock = pg.time.Clock()
    tmr = 0
    charging = False

    bombs = pg.sprite.Group()
    emys = pg.sprite.Group()
    shields = pg.sprite.Group()  # 防御壁グループを追加

    clock = pg.time.Clock()
    gravity_group = pg.sprite.Group()  # Gravityインスタンスを管理するグループ

    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                charging = True
            if event.type == pg.KEYUP and event.key == pg.K_SPACE:
                charging = False
                max_charged = charge_bar.charge_time == charge_bar.max_charge #チャージ時間が足りるならBEEM1を発射する
                beams.append(Beam(bird, max_charged))

        X = tmr % 3200
        screen.blit(bg_img, [-X, 0])
        screen.blit(flip_bg_img, [-X + 1600, 0])
        screen.blit(bg_img, [-X + 3200, 0])
        screen.blit(flip_bg_img, [-X + 4800, 0])

        draw_charge_indicator(screen, charge_bar.charge_time == charge_bar.max_charge)
        charge_bar.update(charging, screen)
        bird.update(key_lst, screen)
        beams = [beam for beam in beams if beam.beams[0]["rct"].right > 0]
        for beam in beams:
            beam.update(screen)
        
        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ# こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        for bomb in pg.sprite.groupcollide(bombs, shields, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        # 重力場と爆弾、敵機の衝突判定
        for gravity in gravity_group:
            for bomb in pg.sprite.spritecollide(gravity, bombs, True):
                exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            for emy in pg.sprite.spritecollide(gravity, emys, True):
                exps.add(Explosion(emy, 100))  # 爆発エフェクト

        for bomb in pg.sprite.spritecollide(bird, bombs, True):
            if bomb.state == "inactive":
                continue
            if bird.state == "hyper":
                exps.add(Explosion(bomb, 50))
                score.value += 1  # 1点アップ
                continue
            else:
                bird.change_img(8, screen) # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return

        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
