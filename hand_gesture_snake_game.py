import asyncio
import platform
import pygame
import random
import numpy as np
import cv2
from mediapipe.python.solutions import hands
from mediapipe.python.solutions.drawing_utils import draw_landmarks

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
FPS = 15

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Snake class
class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = GRID_WIDTH // 2
        self.y = GRID_HEIGHT // 2
        self.direction = (1, 0)
        self.body = [(self.x, self.y)]
        self.length = 1
        self.color = RED

    def update(self):
        self.x += self.direction[0]
        self.y += self.direction[1]
        self.x %= GRID_WIDTH
        self.y %= GRID_HEIGHT
        self.body.insert(0, (self.x, self.y))
        if len(self.body) > self.length:
            self.body.pop()

    def grow(self):
        self.length += 1

    def get_color(self, score):
        if score >= 10:
            return PURPLE
        elif score >= 5:
            return YELLOW
        return RED

    def collides_with_self(self):
        return (self.x, self.y) in self.body[1:]

# Food class
class Food:
    def __init__(self):
        self.position = self.random_position()
        self.type = random.choice(['apple', 'banana', 'grape'])

    def random_position(self):
        return (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))

    def draw(self, screen):
        x, y = self.position
        color = RED if self.type == 'apple' else YELLOW if self.type == 'banana' else PURPLE
        pygame.draw.circle(screen, color, 
                          (x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2), 
                          GRID_SIZE // 2)

# Hand tracking class
class HandTracker:
    def __init__(self):
        self.hands = hands.Hands(max_num_hands=1, min_detection_confidence=0.5)
        self.cap = cv2.VideoCapture(0)

    def get_direction(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to capture video")
            return None
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)
        if results.multi_hand_landmarks:
            landmarks = results.multi_hand_landmarks[0]
            index_tip = landmarks.landmark[8]
            draw_landmarks(frame, landmarks, hands.HAND_CONNECTIONS)
            x_pixel, y_pixel = int(index_tip.x * frame.shape[1]), int(index_tip.y * frame.shape[0])
            cv2.circle(frame, (x_pixel, y_pixel), 10, (0, 255, 0), -1)
            cv2.imshow('Hand Tracking Debug', frame)
            cv2.waitKey(1)
            x, y = index_tip.x, index_tip.y
            if x < 0.3:
                return (-1, 0)
            elif x > 0.7:
                return (1, 0)
            elif y < 0.3:
                return (0, -1)
            elif y > 0.7:
                return (0, 1)
        return None

    def close(self):
        self.hands.close()
        self.cap.release()
        cv2.destroyAllWindows()

# Game setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hand-Gesture Controlled Snake Game")
clock = pygame.time.Clock()
snake = Snake()
food = Food()
tracker = HandTracker()
score = 0
font = pygame.font.SysFont('arial', 24)

def setup():
    global snake, food, score
    snake = Snake()
    food = Food()
    score = 0

async def main():
    global snake, food, score
    setup()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        ret, frame = tracker.cap.read()
        if not ret:
            print("Webcam capture failed")
            screen.fill(BLACK)
            error_text = font.render("Webcam not detected", True, WHITE)
            screen.blit(error_text, (WIDTH//2-100, HEIGHT//2))
            pygame.display.flip()
            await asyncio.sleep(1.0 / FPS)
            continue

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (WIDTH, HEIGHT))
        frame_surface = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
        screen.blit(frame_surface, (0, 0))

        new_direction = tracker.get_direction()
        if new_direction and new_direction != (-snake.direction[0], -snake.direction[1]):
            snake.direction = new_direction or snake.direction

        snake.update()
        snake.color = snake.get_color(score)

        if (snake.x, snake.y) == food.position:
            snake.grow()
            score += 1
            food = Food()

        if snake.collides_with_self():
            setup()

        for x, y in snake.body:
            pygame.draw.rect(screen, snake.color, 
                            (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE))
        food.draw(screen)
        score_text = font.render(f'Score: {score}', True, WHITE)
        screen.blit(score_text, (10, 10))
        pygame.display.flip()

        await asyncio.sleep(1.0 / FPS)

    tracker.close()
    pygame.quit()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())