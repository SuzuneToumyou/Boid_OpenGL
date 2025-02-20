#!/usr/bin/python3
# coding: utf-8

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import random

# 定数の定義
SIZE = 600  # 正方体のサイズ
NUM_BOIDS = 100  # Boidsの数を減らす
MAX_SPEED = 4
MAX_FORCE = 0.1
RESET_TIME = 300000  # 初期状態に戻る時間（ミリ秒）

# Pygameの初期化
pygame.init()
screen = pygame.display.set_mode((SIZE, SIZE), DOUBLEBUF | OPENGL)
pygame.display.set_caption("3D Boids with OpenGL")
clock = pygame.time.Clock()

gluPerspective(45, (SIZE / SIZE), 0.1, 3000.0)
camera_distance = 1500  # カメラの初期距離

# カメラの回転角度
camera_angle_x = 0
camera_angle_y = 0

class Boid:
    def __init__(self):
        self.position = pygame.Vector3(random.uniform(-SIZE/2, SIZE/2), random.uniform(-SIZE/2, SIZE/2), random.uniform(-SIZE/2, SIZE/2))
        self.velocity = pygame.Vector3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))
        self.acceleration = pygame.Vector3(0, 0, 0)

    def update(self):
        self.velocity += self.acceleration
        if self.velocity.length() > MAX_SPEED:
            self.velocity.scale_to_length(MAX_SPEED)
        self.position += self.velocity
        self.acceleration *= 0

    def apply_force(self, force):
        self.acceleration += force

    def edges(self):
        margin = 3  # 壁からの距離のマージン
        turn_factor = 1  # 反発力の強さ

        if self.position.x > SIZE/2 - margin:
            self.velocity.x -= turn_factor
        elif self.position.x < -SIZE/2 + margin:
            self.velocity.x += turn_factor
        if self.position.y > SIZE/2 - margin:
            self.velocity.y -= turn_factor
        elif self.position.y < -SIZE/2 + margin:
            self.velocity.y += turn_factor
        if self.position.z > SIZE/2 - margin:
            self.velocity.z -= turn_factor
        elif self.position.z < -SIZE/2 + margin:
            self.velocity.z += turn_factor

    def align(self, boids):
        perception_radius = 50
        steering = pygame.Vector3(0, 0, 0)
        total = 0
        for boid in boids:
            if boid != self and self.position.distance_to(boid.position) < perception_radius:
                steering += boid.velocity
                total += 1
        if total > 0:
            steering /= total
            steering.scale_to_length(MAX_SPEED)
            steering -= self.velocity
            if steering.length() > MAX_FORCE:
                steering.scale_to_length(MAX_FORCE)
        return steering

    def cohesion(self, boids):
        perception_radius = 50
        steering = pygame.Vector3(0, 0, 0)
        total = 0
        for boid in boids:
            if boid != self and self.position.distance_to(boid.position) < perception_radius:
                steering += boid.position
                total += 1
        if total > 0:
            steering /= total
            steering -= self.position
            steering.scale_to_length(MAX_SPEED)
            steering -= self.velocity
            if steering.length() > MAX_FORCE:
                steering.scale_to_length(MAX_FORCE)
        return steering

    def separation(self, boids):
        perception_radius = 25
        steering = pygame.Vector3(0, 0, 0)
        total = 0
        for boid in boids:
            distance = self.position.distance_to(boid.position)
            if boid != self and distance < perception_radius:
                diff = self.position - boid.position
                diff /= distance
                steering += diff
                total += 1
        if total > 0:
            steering /= total
            if steering.length() > MAX_SPEED:
                steering.scale_to_length(MAX_SPEED)
            steering -= self.velocity
            if steering.length() > MAX_FORCE:
                steering.scale_to_length(MAX_FORCE)
        return steering

    def flock(self, boids):
        alignment = self.align(boids)
        cohesion = self.cohesion(boids)
        separation = self.separation(boids)

        alignment *= 1.0
        cohesion *= 1.0
        separation *= 1.5

        self.apply_force(alignment)
        self.apply_force(cohesion)
        self.apply_force(separation)

    def show(self):
        glPushMatrix()
        glTranslatef(self.position.x, self.position.y, self.position.z)
        glColor3f(1.0, 0.0, 1.0)  # マゼンタ色
        quadric = gluNewQuadric()
        gluSphere(quadric, 4, 16, 16)  # 球体のサイズを設定し、詳細度を減らす
        gluDeleteQuadric(quadric)
        glPopMatrix()

def draw_box():
    glBegin(GL_LINES)
    glColor3f(0.0, 1.0, 1.0)  # 水色
    # Front face
    glVertex3f(-SIZE/2, -SIZE/2, -SIZE/2)
    glVertex3f(SIZE/2, -SIZE/2, -SIZE/2)
    glVertex3f(SIZE/2, -SIZE/2, -SIZE/2)
    glVertex3f(SIZE/2, SIZE/2, -SIZE/2)
    glVertex3f(SIZE/2, SIZE/2, -SIZE/2)
    glVertex3f(-SIZE/2, SIZE/2, -SIZE/2)
    glVertex3f(-SIZE/2, SIZE/2, -SIZE/2)
    glVertex3f(-SIZE/2, -SIZE/2, -SIZE/2)
    # Back face
    glVertex3f(-SIZE/2, -SIZE/2, SIZE/2)
    glVertex3f(SIZE/2, -SIZE/2, SIZE/2)
    glVertex3f(SIZE/2, -SIZE/2, SIZE/2)
    glVertex3f(SIZE/2, SIZE/2, SIZE/2)
    glVertex3f(SIZE/2, SIZE/2, SIZE/2)
    glVertex3f(-SIZE/2, SIZE/2, SIZE/2)
    glVertex3f(-SIZE/2, SIZE/2, SIZE/2)
    glVertex3f(-SIZE/2, -SIZE/2, SIZE/2)
    # Connecting edges
    glVertex3f(-SIZE/2, -SIZE/2, -SIZE/2)
    glVertex3f(-SIZE/2, -SIZE/2, SIZE/2)
    glVertex3f(SIZE/2, -SIZE/2, -SIZE/2)
    glVertex3f(SIZE/2, -SIZE/2, SIZE/2)
    glVertex3f(SIZE/2, SIZE/2, -SIZE/2)
    glVertex3f(SIZE/2, SIZE/2, SIZE/2)
    glVertex3f(-SIZE/2, SIZE/2, -SIZE/2)
    glVertex3f(-SIZE/2, SIZE/2, SIZE/2)
    glEnd()

def reset_boids():
    global boids
    boids = [Boid() for _ in range(NUM_BOIDS)]

# Boidsのリストを作成
boids = [Boid() for _ in range(NUM_BOIDS)]

# タイマーの設定
pygame.time.set_timer(USEREVENT, RESET_TIME)

# メインループ
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == USEREVENT:
            reset_boids()  # 初期状態に戻す
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                camera_angle_y -= 5
            elif event.key == pygame.K_RIGHT:
                camera_angle_y += 5
            elif event.key == pygame.K_UP:
                camera_angle_x -= 5
            elif event.key == pygame.K_DOWN:
                camera_angle_x += 5
            elif event.key == pygame.K_a:
                camera_distance -= 50  # Aキーでカメラが近づく
            elif event.key == pygame.K_z:
                camera_distance += 50  # Zキーでカメラが遠ざかる

    glClearColor(0.0, 0.0, 0.0, 0.0)  # 背景を黒に設定
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # カメラの回転を適用
    glLoadIdentity()
    gluPerspective(45, (SIZE / SIZE), 0.1, 3000.0)
    glTranslatef(0.0, 0.0, -camera_distance)  # カメラの距離を調整
    glRotatef(camera_angle_x, 1, 0, 0)
    glRotatef(camera_angle_y, 0, 1, 0)

    draw_box()

    for boid in boids:
        boid.edges()
        boid.flock(boids)
        boid.update()
        boid.show()

    pygame.display.flip()
    clock.tick(30)  # フレームレートを30FPSに設定して負荷を軽減

pygame.quit()