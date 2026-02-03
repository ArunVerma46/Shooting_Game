from ursina import *
import random
import math

app = Ursina()

# ---------------- CAMERA ----------------
camera.orthographic = True
camera.fov = 20
Sky()

# ---------------- GAME STATE ----------------
game_over = False
boss_spawned = False
difficulty_timer = 0
invincible = False
invincible_timer = 0
score = 0
high_score = 0

# ---------------- POWER-UPS ----------------
powerups = []
active_powerup = None
powerup_timer = 0
powerup_cooldown = 0  
rapid_fire_active = False
shield_active = False
double_damage_active = False

# ---------------- SOUND EFFECTS ----------------
try:
    shoot_sound = Audio('assets\\shoot', autoplay=False, loop=False)
    explosion_sound = Audio('assets\\explosion', autoplay=False, loop=False)
    hit_sound = Audio('assets\\hit', autoplay=False, loop=False)
    boss_hit_sound = Audio('assets\\boss_hit', autoplay=False, loop=False)
    sounds_loaded = True
except:
    print("⚠️ Sound files not found! Game will run without sounds.")
    sounds_loaded = False

def play_sound(sound_name):
    """Safely play sound if it exists"""
    if not sounds_loaded:
        return
    
    try:
        if sound_name == 'shoot':
            shoot_sound.play()
        elif sound_name == 'explosion':
            explosion_sound.play()
        elif sound_name == 'hit':
            hit_sound.play()
        elif sound_name == 'boss_hit':
            boss_hit_sound.play()
    except:
        pass

# ---------------- PLAYER ----------------
player_health = 100
shoot_cooldown = 0.25
last_shot = 0
bullet_damage = 10  # Base damage

me = Animation(
    'assets\\player',
    collider='box',
    x=-14,
    y=0
)

# ---------------- HEALTH BAR ----------------
health_bg = Entity(
    model='quad',
    color=color.dark_gray,
    scale=(6, .4),
    x=-12,
    y=8,
    z=-1
)

health_bar = Entity(
    model='quad',
    color=color.red,
    scale=(6, .4),
    x=-12,
    y=8,
    z=-2
)

def update_health_bar():
    health_bar.scale_x = max(0.01, 6 * (player_health / 100))

# ---------------- BOSS HEALTH BAR ----------------
boss_health_bg = Entity(
    model='quad',
    color=color.dark_gray,
    scale=(8, .5),
    x=0,
    y=-8,
    z=-1,
    enabled=False
)

boss_health_bar = Entity(
    model='quad',
    color=color.orange,
    scale=(8, .5),
    x=0,
    y=-8,
    z=-2,
    enabled=False
)

boss_name_text = Text(
    text='BOSS',
    position=(0, -0.35),
    scale=2,
    color=color.red,
    enabled=False,
    origin=(0, 0)
)

def update_boss_health_bar():
    boss_health_bar.scale_x = max(0.01, 8 * (boss_health / 350))

# ---------------- SCORE DISPLAY ----------------
score_text = Text(
    text='Score: 0',
    position=(-0.85, 0.45),
    scale=2,
    color=color.white
)

high_score_text = Text(
    text='High Score: 0',
    position=(-0.85, 0.42),
    scale=1.5,
    color=color.yellow
)

# Power-up status text
powerup_status_text = Text(
    text='',
    position=(0.4, 0.45),
    scale=1.8,
    color=color.cyan,
    origin=(0, 0)
)

def update_score(points):
    global score, high_score
    score += points
    score_text.text = f'Score: {score}'
    
    if score > high_score:
        high_score = score
        high_score_text.text = f'High Score: {high_score}'

# ---------------- BACKGROUND ----------------
Entity(
    model='quad',
    texture='assets\\bg',
    scale=36,
    z=1
)

# ---------------- EXPLOSION ----------------
boom = Animation('assets\\boom', scale=3, enabled=False)

# ---------------- ENEMIES ----------------
fly_template = Entity(
    model='cube',
    texture='assets\\fly',
    collider='box',
    scale=3,
    enabled=False
)

flies = []
enemy_bullets = []
enemy_base_speed = 4

# ---------------- BOSS ----------------
boss = None
boss_health = 350
boss_max_health = 350
boss_bullets = []

# ---------------- PLAYER BULLETS ----------------
bullets = []

# ---------------- UI ----------------
game_over_text = Text(
    "GAME OVER",
    scale=3,
    y=0.2,
    enabled=False
)

final_score_text = Text(
    "",
    scale=2,
    y=0.1,
    enabled=False
)

restart_btn = Button(
    text='RESTART',
    scale=(0.2, 0.1),
    y=-0.2,
    enabled=False
)

# ---------------- POWER-UP FUNCTIONS ----------------
def spawn_powerup(x, y):
    """Spawn a random power-up"""
    powerup_type = random.choice(['rapid_fire', 'shield', 'health', 'double_damage'])
    
    # Use actual textures from assets
    textures = {
        'rapid_fire': 'assets\\rapid_fire',
        'shield': 'assets\\shield',
        'health': 'assets\\Health',
        'double_damage': 'assets\\Double_damage'
    }
    
    powerup = Entity(
        model='cube',
        texture=textures[powerup_type],
        scale=2,
        x=x,
        y=y,
        collider='box'
    )
    powerup.type = powerup_type
    powerup.rotation_speed = 100
    powerups.append(powerup)

def activate_powerup(powerup_type):
    """Activate a power-up"""
    global active_powerup, powerup_timer, rapid_fire_active
    global shield_active, double_damage_active, player_health, shoot_cooldown
    global powerup_cooldown
    
    # Check if there's already an active power-up
    if powerup_cooldown > 0:
        print("⏳ Wait before using another power-up!")
        return False
    
    if powerup_type == 'rapid_fire':
        rapid_fire_active = True
        shoot_cooldown = 0.1
        powerup_timer = 8
        powerup_cooldown = 2  # 2 second cooldown after it ends
        powerup_status_text.text = '⚡ RAPID FIRE!'
        powerup_status_text.color = color.cyan
        print("⚡ RAPID FIRE activated!")
        
    elif powerup_type == 'shield':
        shield_active = True
        powerup_timer = 10
        powerup_cooldown = 2
        me.color = color.blue
        powerup_status_text.text = '🛡️ SHIELD!'
        powerup_status_text.color = color.blue
        print("🛡️ SHIELD activated!")
        
    elif powerup_type == 'health':
        player_health = min(100, player_health + 50)
        update_health_bar()
        powerup_status_text.text = '❤️ +50 HEALTH!'
        powerup_status_text.color = color.green
        invoke(setattr, powerup_status_text, 'text', '', delay=2)
        print("❤️ HEALTH restored!")
        return True  # Health doesn't need cooldown
        
    elif powerup_type == 'double_damage':
        double_damage_active = True
        powerup_timer = 10
        powerup_cooldown = 2
        powerup_status_text.text = '💥 DOUBLE DAMAGE!'
        powerup_status_text.color = color.red
        print("💥 DOUBLE DAMAGE activated!")
    
    active_powerup = powerup_type
    return True

# ---------------- RESTART ----------------
def restart_game():
    global player_health, game_over, boss_spawned
    global boss_health, difficulty_timer, boss
    global flies, bullets, enemy_bullets, boss_bullets
    global invincible, invincible_timer, score
    global powerups, active_powerup, powerup_timer
    global rapid_fire_active, shield_active, double_damage_active
    global shoot_cooldown, powerup_cooldown

    game_over = False
    boss_spawned = False
    difficulty_timer = 0
    boss_health = boss_max_health
    player_health = 100
    invincible = False
    invincible_timer = 0
    score = 0
    score_text.text = 'Score: 0'
    
    # Reset power-ups
    rapid_fire_active = False
    shield_active = False
    double_damage_active = False
    active_powerup = None
    powerup_timer = 0
    powerup_cooldown = 0  # NEW: Reset cooldown
    shoot_cooldown = 0.25
    powerup_status_text.text = ''
    
    update_health_bar()

    me.enabled = True
    me.position = (-14, 0, 0)
    me.color = color.white

    for obj in flies + bullets + enemy_bullets + boss_bullets + powerups:
        destroy(obj)

    flies.clear()
    bullets.clear()
    enemy_bullets.clear()
    boss_bullets.clear()
    powerups.clear()

    if boss:
        destroy(boss)
        boss = None

    # Hide boss health bar
    boss_health_bg.enabled = False
    boss_health_bar.enabled = False
    boss_name_text.enabled = False

    game_over_text.enabled = False
    final_score_text.enabled = False
    restart_btn.enabled = False
    
    # Restart enemy spawning
    spawn_enemy()

restart_btn.on_click = restart_game

# ---------------- SPAWN ENEMY ----------------
def spawn_enemy():
    if game_over:
        return

    enemy = duplicate(
        fly_template,
        enabled=True,
        x=22,
        y=random.uniform(-7, 7)
    )
    enemy.speed = enemy_base_speed + random.uniform(1, 3)
    enemy.timer = random.uniform(0, 3)
    flies.append(enemy)

    delay = max(0.4, 1 - difficulty_timer * 0.03)
    invoke(spawn_enemy, delay=delay)

spawn_enemy()

# ---------------- DAMAGE PLAYER ----------------
def damage_player(amount):
    global player_health, invincible, invincible_timer, shield_active
    
    if invincible:
        return
    
    # Shield blocks damage
    if shield_active:
        print("🛡️ Shield blocked damage!")
        return
    
    player_health -= amount
    update_health_bar()
    
    # Play hit sound
    play_sound('hit')
    
    # Set invincibility
    invincible = True
    invincible_timer = 0.5
    if not shield_active:
        me.color = color.red
    
    print(f"Player hit! Health: {player_health}")
    
    if player_health <= 0:
        end_game()

# ---------------- GAME UPDATE ----------------
def update():
    global player_health, game_over, boss_spawned
    global boss_health, difficulty_timer, last_shot, boss
    global invincible, invincible_timer, powerup_timer
    global rapid_fire_active, shield_active, double_damage_active
    global shoot_cooldown, powerup_cooldown  # ADDED: powerup_cooldown

    if game_over:
        return

    difficulty_timer += time.dt
    speed_boost = difficulty_timer * 0.35

    # Handle invincibility
    if invincible:
        invincible_timer -= time.dt
        me.visible = int(invincible_timer * 10) % 2 == 0
        
        if invincible_timer <= 0:
            invincible = False
            if shield_active:
                me.color = color.blue
            else:
                me.color = color.white
            me.visible = True

    # Handle power-up timers
    if powerup_timer > 0:
        powerup_timer -= time.dt
        
        if powerup_timer <= 0:
            if rapid_fire_active:
                rapid_fire_active = False
                shoot_cooldown = 0.25
                print("⚡ Rapid fire ended")
            
            if shield_active:
                shield_active = False
                me.color = color.white
                print("🛡️ Shield ended")
            
            if double_damage_active:
                double_damage_active = False
                print("💥 Double damage ended")
            
            powerup_status_text.text = ''
    
    # Handle power-up cooldown
    if powerup_cooldown > 0:
        powerup_cooldown -= time.dt

    # ---- PLAYER MOVEMENT ----
    me.y += (held_keys['w'] - held_keys['s']) * 6 * time.dt
    me.y = clamp(me.y, -8, 8)
    me.rotation_z = -20 if held_keys['w'] else 20 if held_keys['s'] else 0

    # ---- PLAYER SHOOT ----
    if held_keys['enter'] and time.time() - last_shot > shoot_cooldown:
        last_shot = time.time()
        
        # Play shoot sound
        play_sound('shoot')
        
        bullet = Entity(
            model='cube',
            texture='assets\\Bullet',
            collider='box',
            scale=0.5,
            x=me.x + 2,
            y=me.y
        )
        bullet.speed = 18
        bullet.damage = 10 * (2 if double_damage_active else 1)
        bullets.append(bullet)

    # ---- PLAYER BULLETS ----
    for bullet in bullets[:]:
        bullet.x += bullet.speed * time.dt
        if bullet.x > 30:
            destroy(bullet)
            bullets.remove(bullet)

    # ---- POWER-UPS ----
    for powerup in powerups[:]:
        powerup.rotation_y += powerup.rotation_speed * time.dt
        powerup.x -= 2 * time.dt
        
        if powerup.x < -30:
            destroy(powerup)
            powerups.remove(powerup)
            continue
        
        if powerup.intersects(me).hit:
            if activate_powerup(powerup.type):  # Only destroy if activated
                destroy(powerup)
                powerups.remove(powerup)

    # ---- ENEMIES ----
    for fly in flies[:]:
        fly.timer += time.dt
        fly.x -= (fly.speed + speed_boost) * time.dt
        fly.y += math.sin(fly.timer * 4) * time.dt * 3

        # Enemy shooting
        if random.random() < 0.006:
            eb = Entity(
                model='cube',
                texture='assets\\black_fire', 
                scale=2,
                x=fly.x,
                y=fly.y,
                collider='box'
            )
            eb.speed = 12
            enemy_bullets.append(eb)

        # Hit player
        if fly.intersects(me).hit:
            damage_player(25)
            destroy(fly)
            flies.remove(fly)
            continue

        # Bullet hit enemy
        hit = False
        for bullet in bullets[:]:
            if bullet.intersects(fly).hit:
                boom.position = fly.position
                boom.enabled = True
                invoke(setattr, boom, 'enabled', False, delay=0.2)

                # Play explosion sound
                play_sound('explosion')
                
                update_score(10)
                
                # Chance to drop power-up - REDUCED to make it rare
                if random.random() < 0.08:  # CHANGED: 8% chance (was 15%)
                    spawn_powerup(fly.x, fly.y)

                destroy(bullet)
                destroy(fly)

                if bullet in bullets:
                    bullets.remove(bullet)
                if fly in flies:
                    flies.remove(fly)
                hit = True
                break
        
        if hit:
            continue

    # ---- ENEMY BULLETS ----
    for eb in enemy_bullets[:]:
        eb.x -= eb.speed * time.dt
        if eb.x < -30:
            destroy(eb)
            enemy_bullets.remove(eb)
            continue

        if eb.intersects(me).hit:
            damage_player(15)
            destroy(eb)
            enemy_bullets.remove(eb)

    # ---- BOSS SPAWN (10 SECONDS) ----
    if not boss_spawned and difficulty_timer > 10:
        spawn_boss()
        update_score(50)

    # ---- BOSS LOGIC ----
    if boss is not None and boss.enabled:
        # Boss moves slowly towards player
        boss.x -= 0.8 * time.dt
        boss.y += (me.y - boss.y) * time.dt * 1.2

        # Boss shooting
        if random.random() < 0.02:
            bb = Entity(
                model='cube',
                texture='assets\\Purple_flames',
                scale=2.2,
                x=boss.x - 2,
                y=boss.y,
                collider='box'
            )
            bb.speed = 15
            boss_bullets.append(bb)

        # Check bullet hits on boss
        for bullet in bullets[:]:
            if bullet.enabled and boss.enabled and bullet.intersects(boss).hit:
                damage = bullet.damage if hasattr(bullet, 'damage') else 10
                boss_health -= damage
                update_boss_health_bar()
                
                # Play boss hit sound
                play_sound('boss_hit')
                
                update_score(2)
                
                # Destroy bullet
                destroy(bullet)
                if bullet in bullets:
                    bullets.remove(bullet)

                # Check if boss is defeated
                if boss_health <= 0:
                    # Play big explosion sound
                    play_sound('explosion')
                    
                    # Big explosion effect
                    boom.position = boss.position
                    boom.scale = 8
                    boom.enabled = True
                    invoke(setattr, boom, 'enabled', False, delay=0.3)
                    invoke(setattr, boom, 'scale', 3, delay=0.3)
                    
                    update_score(200)
                    
                    # Hide boss health bar
                    boss_health_bg.enabled = False
                    boss_health_bar.enabled = False
                    boss_name_text.enabled = False
                    
                    destroy(boss)
                    boss = None
                    print("💥 BOSS DEFEATED! 💥")
                    break

    # ---- BOSS BULLETS ----
    for bb in boss_bullets[:]:
        bb.x -= bb.speed * time.dt
        if bb.x < -30:
            destroy(bb)
            boss_bullets.remove(bb)
            continue
            
        if bb.intersects(me).hit:
            damage_player(20)
            destroy(bb)
            boss_bullets.remove(bb)

# ---------------- BOSS SPAWN ----------------
def spawn_boss():
    global boss, boss_spawned, boss_health

    boss_spawned = True
    boss_health = boss_max_health
    
    boss = Entity(
        model='cube',
        texture='assets\\boss',
        scale=7,
        collider='box',
        x=18,
        y=0
    )
    
    # Show boss health bar
    boss_health_bg.enabled = True
    boss_health_bar.enabled = True
    boss_name_text.enabled = True
    update_boss_health_bar()
    
    # Spawn LIMITED power-ups for boss fight - REDUCED from 3 to 2
    for i in range(2):  # CHANGED: Only 2 power-ups (was 3)
        spawn_powerup(random.uniform(15, 20), random.uniform(-6, 6))
    
    print("🔥 BOSS SPAWNED! 🔥")
    print("💡 2 Power-ups spawned to help you!")

# ---------------- GAME OVER ----------------
def end_game():
    global game_over
    game_over = True
    me.enabled = False
    game_over_text.enabled = True
    final_score_text.text = f"Final Score: {score}"
    final_score_text.enabled = True
    restart_btn.enabled = True
    
    # Hide boss health bar if visible
    boss_health_bg.enabled = False
    boss_health_bar.enabled = False
    boss_name_text.enabled = False

# ---------------- INPUT ----------------
def input(key):
    if key == 'q':
        quit()


app.run()
