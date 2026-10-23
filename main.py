import random
import math
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line
from kivy.properties import NumericProperty, BooleanProperty
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

Window.size = (450, 800)
class ParallaxBackground(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.update_bg, pos=self.update_bg)
        
        self.offset_x = 0
        self.offset_y = 0

        self.bg_back = Image(source='bg_back.jpg', fit_mode='fill')
        self.add_widget(self.bg_back)

        self.bg_front = Image(source='bg_front.png', fit_mode='fill')
        self.add_widget(self.bg_front)

    def update_bg(self, *args):
        extra_size = 40
        w = self.width + extra_size
        h = self.height + extra_size

        self.bg_back.size = (w, h)
        self.bg_back.pos = (self.x - extra_size/2 + self.offset_x * 0.2, self.y - extra_size/2 + self.offset_y * 0.2)

        self.bg_front.size = (w, h)
        self.bg_front.pos = (self.x - extra_size/2 + self.offset_x * 0.6, self.y - extra_size/2 + self.offset_y * 0.6)

    def set_parallax_offset(self, touch_x, touch_y):
        center_x = self.width / 2
        center_y = self.height / 2
        
        self.offset_x = (touch_x - center_x) * 0.15
        self.offset_y = (touch_y - center_y) * 0.15
        self.update_bg()


class GameObject(Image):
    def __init__(self, is_bomb=False, **kwargs):
        if is_bomb:
            img_source = 'bomb.png'
        else:
            img_source = random.choice(['apple.png', 'banana.png', 'watermelon.png'])

        super().__init__(source=img_source, fit_mode='contain', **kwargs)
        
        self.is_bomb = is_bomb
        
        self.size = (280, 280)
        self.size_hint = (None, None)
        self.radius = 140
        self.sliced = False

        self.x = random.randint(30, int(Window.width - 300))
        self.y = -150
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(28, 38)
        self.gravity = -0.65

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity

    def is_sliced_by(self, p1, p2):
        if self.sliced:
            return False

        cx = self.x + self.width / 2
        cy = self.y + self.height / 2

        x1, y1 = p1
        x2, y2 = p2
        dx, dy = x2 - x1, y2 - y1

        if dx == 0 and dy == 0:
            return False

        t = max(0, min(1, ((cx - x1) * dx + (cy - y1) * dy) / (dx * dx + dy * dy)))
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        dist = math.hypot(cx - closest_x, cy - closest_y)
        return dist < self.radius


class GameScreen(MDScreen):
    score = NumericProperty(0)
    lives = NumericProperty(3)
    game_over = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.objects = []
        self.touch_points = []
        
        Clock.schedule_interval(self.game_loop, 1 / 60)
        Clock.schedule_interval(self.spawn_object, 1.5)

    def spawn_object(self, dt):
        if self.game_over:
            return

        is_bomb = random.random() < 0.22
        obj = GameObject(is_bomb=is_bomb)
        self.objects.append(obj)
        self.add_widget(obj)

    def game_loop(self, dt):
        if self.game_over:
            return

        for obj in self.objects[:]:
            obj.update()
            if obj.y < -200:
                if not obj.is_bomb and not obj.sliced:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.end_game()
                
                self.remove_widget(obj)
                self.objects.remove(obj)

    def on_touch_down(self, touch):
        if self.game_over:
            return super().on_touch_down(touch)

        self.touch_points = [(touch.x, touch.y)]
        self.update_parallax(touch.x, touch.y)
        return True

    def on_touch_move(self, touch):
        if self.game_over:
            return super().on_touch_move(touch)

        p1 = (touch.x, touch.y)
        if self.touch_points:
            p2 = self.touch_points[-1]
            
            with self.canvas.after:
                Color(0.9, 0.9, 1.0, 0.8)
                line = Line(points=[p2[0], p2[1], p1[0], p1[1]], width=4)
                Clock.schedule_once(lambda dt: self.canvas.after.remove(line), 0.08)

            for obj in self.objects[:]:
                if obj.is_sliced_by(p2, p1):
                    obj.sliced = True
                    if obj.is_bomb:
                        self.end_game()
                    else:
                        self.score += 10
                        self.remove_widget(obj)
                        self.objects.remove(obj)

        self.touch_points.append(p1)
        if len(self.touch_points) > 6:
            self.touch_points.pop(0)

        self.update_parallax(touch.x, touch.y)
        return True

    def update_parallax(self, x, y):
        if hasattr(self.ids, 'parallax_bg'):
            self.ids.parallax_bg.set_parallax_offset(x, y)

    def end_game(self):
        self.game_over = True

    def restart_game(self):
        for obj in self.objects:
            self.remove_widget(obj)
        self.objects.clear()
        
        self.score = 0
        self.lives = 3
        self.game_over = False


class FruitNinjaApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        return GameScreen()


if __name__ == '__main__':
    FruitNinjaApp().run()