# Ray Nelson and Tyler BoddySpargo with the help of Josh Davis
# 5/20/2012
# CS111 Spring Term 2012
# Carleton Colege



import sys, pygame, random, math, time
from pygame.locals import *
from pygame._view import *


config = {
    'start_zombies': 1,
    'max_zombie_speed':  3.5,
    'min_zombie_speed':  1.0,
    'default_zombie_speed':  2.0,
    'default_player_speed':  5,
    'bullet_speed': 15,
    'zombie_wander_coefficient':  2.0,
    'zombie_start_health':  1,
    'last_zombie':  None,
    'difficulty_coefficient':  1,
    'hit':  False,
    'last_hit':  None,
    'won': False,
    'lost': False,
    'paused': False
}


class Zombie(object):

    def __init__(self, imageU, width, height, surface):
        self.image = imageU
        self.original = imageU
        self.width = width
        self.height = height
        self.surface = surface
        self.life = config['zombie_start_health']
        self.image_dir = 0
        self.wentOffScreen = None
        self.last_hurt = None
        self.setPosition(0.0, 0.0)
        self.setSpeed(config['default_zombie_speed'])
        self.setDirection(random.uniform(0, 2.0 * math.pi))
        self.setImageDirection()

    def getPosition(self):
        return self.xy

    def setPosition(self, x, y):
        x = max(0, min(self.surface.get_width(), x))
        y = max(0, min(self.surface.get_height(), y))
        self.xy = [x, y]

    def loseLife(self):
        if self.life > 0:
            self.life-=1

    def getSpeed(self):
        return self.speed

    def setSpeed(self, speed):
        self.speed = speed

    def getDirection(self):
        return self.dir

    def setDirection(self, direction):
        if config['zombie_wander_coefficient']:
            direction += random.uniform(-math.pi/2.0*(config['zombie_wander_coefficient']/50.0), math.pi/2.0*(config['zombie_wander_coefficient']/50.0))
        if direction < 0:
            direction += math.pi * 2.0
            #print(direction*180/math.pi)
        else:
            direction = direction % (math.pi*2)
        self.dir = direction
        self.setImageDirection()

    def setImageDirection(self):
        direct = 270 - math.trunc(self.dir*(180/math.pi))
        if math.fabs(direct - self.image_dir) > 5:
            self.image_dir = direct
            self.image = pygame.transform.rotate(self.original, direct)


    def getVelocity(self):
        v0 = self.speed * math.cos(self.dir)
        v1 = self.speed * math.sin(self.dir)
        return [v0, v1]

    def setVelocity(self, v):
        self.dir = math.atan2(v[1], v[0])
        self.speed = math.sqrt(v[0]**2 + v[1]**2)

    def draw(self):
        rect = pygame.Rect(self.xy[0] - self.width / 2.0, self.xy[1] - self.height / 2.0, self.width, self.height)
        self.surface.blit(self.image, rect)

    def panicButton(self, player, xyPlayer):
        #calculates new position based on old position and direction
        xy = self.getPosition()
        dist = (xyPlayer[0] - xy[0])**2 + (xyPlayer[1] - xy[1])**2
        if dist < 96**2:
            dir = self.getDirection()
            opdir = random.uniform(((dir + math.pi) % 2.0 * math.pi) - math.pi / 2.0, ((dir + math.pi) % 2.0 * math.pi) + math.pi / 2.0)
            self.setDirection(opdir)
            spd = 100
            xymod = [math.cos(opdir) * spd, math.sin(opdir) * spd]
            xy[0] += xymod[0]
            xy[1] += xymod[1]
            self.setPosition(xy[0], xy[1])

    def killed(self, xyDart):
        xy = self.getPosition()
        dist = (xyDart[0] - xy[0])**2 + (xyDart[1] - xy[1])**2
        # If zombie was "hit" by dart, return True, otherwise, return False
        if dist < (self.width*0.75)**2:
            self.loseLife()

        return self.life<=0


    def updatePositionVelocity(self, target):
        # Update the position based on the old velocity.
        v = self.getVelocity()
        xy = self.getPosition()
        xy[0] += v[0]
        xy[1] += v[1]
        self.setPosition(xy[0], xy[1])
        xyTarget = target.getPosition()
        # Compute the distance to the target.
        dist = (xyTarget[0] - xy[0])**2 + (xyTarget[1] - xy[1])**2

        if dist < 96**2:
            if dist <= (self.width*0.8)**2:
                if not self.last_hurt or time.clock() - self.last_hurt > 0.5:
                    target.changeLife(-5)
                    self.last_hurt = time.clock()
                    if not config['last_hit'] or time.clock() - config['last_hit'] > 0.5:
                        config['last_hit'] = time.clock()
                    config['hit'] = True
            # The target is near here; aim toward it.
            self.setDirection(math.atan2(xyTarget[1] - xy[1], xyTarget[0] - xy[0]))
        else:
            direct = self.getDirection()
            # when you reach edge of map, head off in a complimentary direction
            if (not self.wentOffScreen) or (self.wentOffScreen+1) < time.clock():
                if xy[0]+self.width/2.0 > self.surface.get_width() or xy[0] < 0:
                    if direct < math.pi:
                        direct=math.pi-direct
                    else:
                        direct= 0-(direct-math.pi)
                    self.wentOffScreen = time.clock()
                elif xy[1]+self.height/2.0 > self.surface.get_height() or xy[1] < 0:
                    direct-=direct*2.0
                    self.wentOffScreen = time.clock()
            self.setDirection(direct)
            self.setImageDirection()



# Attributes: Image, Position, Displacement, width, height, Surface
# Behaviors: get(Position), set(Position), Keyaction, draw,
class Player():

    def __init__(self, imageU, panicU, width, height, surface, start):
        self.image = imageU
        self.transimage = imageU
        self.original = imageU
        self.panic = panicU
        self.width = width
        self.height = height
        self.start = start
        self.score = 0
        self.life = 50
        self.lives = 1
        self.bullets = 10
        self.last_heal = time.clock()
        self.last_bullet = time.clock()
        self.last_powerup = time.clock()
        self.surface = surface
        self.setPosition(surface.get_width() / 2.0, surface.get_height() / 2.0)
        self.direction = 0


    def getPosition(self):
        return self.xy

    def changeLife(self, value):
        if self.life + value > 0:
            if self.score + value >=0:
                self.score += value
            if self.life + value >= 50:
                self.changeLives(1)
                self.life = self.life+value-50
            else:
                self.life += value
        else:
            self.setPosition(self.surface.get_width() / 2.0, self.surface.get_height() / 2.0)
            self.changeLives(-1)
            self.life = 50

    def changeLives(self, value):
        if self.lives + value >= 0 and self.lives + value <= 3:
            self.lives += value;
        elif self.lives + value < 0:
            #what to do when player loses.
            self.life = 0
            config['lost'] = True

    def setPosition(self, x, y):
        x = max(0, min(self.surface.get_width(), x))
        y = max(0, min(self.surface.get_height(), y))
        self.xy = [x, y]

    def panicButton(self, panicU, sndp):
        pygame.mixer.Sound.play(sndp)
        self.image = pygame.transform.rotate(self.panic, 360-self.direction)
        self.transimage=self.panic

    def keyAction(self, x, y, keys):
        #Speed of Player in number of pixels traveled per keystroke. User can alter this to move more or less quickly
        spd = config['default_player_speed']

        #Moves player if keys w, a, s, or d were pressed, does nothing if other keys were pressed
        if isPressed(keys, [pygame.K_w, pygame.K_UP]):
            if isPressed(keys, [pygame.K_a, pygame.K_LEFT]):
                self.direction = 315
                self.setPosition(x - spd*math.cos(self.direction/(180/math.pi)), y + spd*math.sin(self.direction/(180/math.pi)))
            elif isPressed(keys, [pygame.K_d, pygame.K_RIGHT]):
                self.direction = 45
                self.setPosition(x + spd*math.cos(self.direction/(180/math.pi)), y - spd*math.sin(self.direction/(180/math.pi)))
            else:
                self.direction = 0
                self.setPosition(x, y - spd)
        elif isPressed(keys, [pygame.K_s, pygame.K_DOWN]):
            if isPressed(keys, [pygame.K_a, pygame.K_LEFT]):
                self.direction = 225
                self.setPosition(x + spd*math.cos(self.direction/(180/math.pi)), y - spd*math.sin(self.direction/(180/math.pi)))
            elif isPressed(keys, [pygame.K_d, pygame.K_RIGHT]):
                self.direction = 135
                self.setPosition(x - spd*math.cos(self.direction/(180/math.pi)), y + spd*math.sin(self.direction/(180/math.pi)))
            else:
                self.direction = 180
                self.setPosition(x, y + spd)
        elif isPressed(keys, [pygame.K_a, pygame.K_LEFT]):
            self.setPosition(x - spd, y)
            self.direction = 270
        elif isPressed(keys, [pygame.K_d, pygame.K_RIGHT]):
            self.setPosition(x + spd, y)
            self.direction = 90
        self.image = pygame.transform.rotate(self.transimage, 360-self.direction)

    def draw(self):
        now = time.clock()
        if self.last_bullet and now - self.last_bullet > 5/config['difficulty_coefficient']:
            self.last_bullet = now
            self.bullets+=1*int(math.ceil(config['difficulty_coefficient']))
        if self.last_heal and now - self.last_heal > 5:
            self.changeLife(1)
            self.last_heal = now
        rect = pygame.Rect(self.xy[0] - self.width / 2.0, self.xy[1] - self.height / 2.0, self.width, self.height)
        self.surface.blit(self.image, rect)
        self.drawHUD()

    def drawHUD(self):
        elapsed = 5*60 - (time.clock() - self.start)
        lifestr = ""
        for o in range(self.life):
            lifestr+="|"
        livesstr = "Lives: "+str(self.lives)
        timestr = "Time: "+(str(int(elapsed/60)) if elapsed/60 > 0 else "0")+":"+(str(int(elapsed%60)) if len(str(int(elapsed%60))) > 1 else "0"+str(int(elapsed%60)))
        scorestr = str(self.score)+" pts"
        bulletsstr = "Bullets: "+str(self.bullets)
        timefont = pygame.font.SysFont("arial",16).render(timestr, 1, (255,255,255))
        scorefont = pygame.font.SysFont("arial",16).render(scorestr, 1, (255,255,255))
        lifefont = pygame.font.SysFont("arial",16).render(lifestr, 1, (255,50,50))
        livesfont= pygame.font.SysFont("arial",16).render(livesstr, 1, (255,255,255))
        bulletsfont = pygame.font.SysFont("arial",16).render(bulletsstr, 1, (255,255,255))
        bulletsrect = bulletsfont.get_rect()
        timerect = timefont.get_rect()
        scorerect = scorefont.get_rect()
        scorerect.centerx = self.surface.get_rect().width-scorerect.width/2
        timerect.centery += scorerect.height
        timerect.centerx = self.surface.get_rect().width-timerect.width/2
        liferect = lifefont.get_rect()
        livesrect = livesfont.get_rect()
        livesrect.centery += liferect.height
        bulletsrect.centerx = livesrect.width+bulletsrect.centerx+10
        bulletsrect.centery = livesrect.centery

        self.surface.blit(scorefont, scorerect)
        self.surface.blit(timefont, timerect)
        self.surface.blit(lifefont, liferect)
        self.surface.blit(livesfont, livesrect)
        self.surface.blit(bulletsfont, bulletsrect)

class Dart():
    def __init__(self, imageV, pdir, pPos, surface):
        self.image = imageV
        self.original = imageV
        self.surface = surface
        self.width = imageV.get_width()
        self.height = imageV.get_height()
        self.setPosition(pPos[0], pPos[1])
        self.setSpeed(config['bullet_speed'])
        self.setDirection(pdir)

    def getPosition(self):
        return self.xy

    def setPosition(self, x, y):
        self.xy = [x, y]

    def getSpeed(self):
        return self.speed

    def setSpeed(self, speed):
        self.speed = speed

    def getDirection(self):
        return self.dir

    def setDirection(self, pdir):
        self.dir = pdir*(math.pi/180)-(math.pi/2)
        self.image = pygame.transform.rotate(self.original, pdir)

    def getVelocity(self):
        v0 = self.speed * math.cos(self.dir)
        v1 = self.speed * math.sin(self.dir)
        return [v0, v1]

    def setVelocity(self, v):
        self.dir = math.atan2(v[1], v[0])
        self.speed = math.sqrt(v[0]**2 + v[1]**2)

    def draw(self):
        rect = pygame.Rect(self.xy[0] - self.width / 2.0, self.xy[1] - self.height / 2.0, self.width, self.height)
        self.surface.blit(self.image, rect)

    def updatePositionVelocity(self):
        # Update the position based on the old velocity.
        v = self.getVelocity()
        xy = self.getPosition()
        xy[0] += v[0]
        xy[1] += v[1]
        self.setPosition(xy[0], xy[1])

def isPressed(a, b):
    for i in b:
        if a[i]:
            return True
    return False

# Lets (i.e. forces) the player to evade some number, n, of zombies.
# The player is controlled through the W, A, S, D keys.
# Input: n number of zombies.
# Output: None.
def zombiesGame():
    # Starting Timing
    start = time.clock()
    config['last_zombie'] = time.clock()
    last_bullet = time.clock()
    # Initialize PyGame and the drawing surface.
    pygame.init()
    pngs = pygame.image.get_extended()
    icon = pygame.image.load("data/icon."+("png" if pngs else "bmp"))
    pygame.display.set_icon(icon)

    width = 512
    height = 512
    surface = pygame.display.set_mode([width, height])
    #Begins to play background music and queues the next songs to play
    pygame.mixer.music.load("data/ZombieJamboree.ogg")
    pygame.mixer.music.play(-1)
    # Loads  and plays panic sound
    sndp = pygame.mixer.Sound("data/panicSound.ogg")
    # Loads and plays dart sound
    snd = pygame.mixer.Sound("data/dartSound.ogg")
    # Initialize the player, zombie, and dart sprites.

    humanU = pygame.image.load("data/Human."+("png" if pngs else "bmp"))
    zombieU = pygame.image.load("data/Zombie."+("png" if pngs else "bmp"))
    dartV = pygame.image.load("data/Dart."+("png" if pngs else "bmp"))
    panicU = pygame.image.load("data/Panic."+("png" if pngs else "bmp"))
    p = Player(humanU, panicU, 32, 32, surface, start)
    z = []
    for x in range(config['start_zombies']):
        a = Zombie(zombieU, 32, 32, surface)
        z += [a]
        z[x].setPosition(random.uniform(1, width), random.uniform(1, height))
        z[x].setSpeed(random.uniform(0, 3.0))
    d = []
    pygame.key.set_repeat(50,50);
    while True:

        # Handle the user quitting or pressing a key.
        keys = pygame.key.get_pressed()
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_ESCAPE]:
                    sys.exit()
                if keys[pygame.K_p]:
                    if not config['paused']:
                        pygame.mixer.music.pause()
                        config['paused'] = True
                    else:
                        pygame.mixer.music.unpause()
                        config['paused'] = False
                if keys[pygame.K_n] and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
                    start = time.clock()
                    p = Player(humanU, panicU, 32, 32, surface, start)
                    z = []
                    config['difficulty_coefficient'] = 1
                    config['min_zombie_speed'] = 1
                    config['max_zombie_speed'] = 3
                    for x in range(config['start_zombies']):
                        a = Zombie(zombieU, 32, 32, surface)
                        z += [a]
                        z[x].setPosition(random.uniform(1, width), random.uniform(1, height))
                        z[x].setSpeed(random.uniform(0, 3.0))
                    d = []
                    config['won'] = False
                    config['lost'] = False
        if config['won'] and config['lost']:
            continue
        # Every 5 secs, create a new zombie.
        now = time.clock()
        elapsed = now - start

        if not p.last_powerup or now - p.last_powerup > 3:
            p.transimage = p.original
        if config['difficulty_coefficient'] < int(elapsed/30)+1:
            p.score+=100
            config['difficulty_coefficient']+=0.5
            config['zombie_start_health']+=config['difficulty_coefficient']
            config['min_zombie_speed']+=0.05*config['difficulty_coefficient']
            config['max_zombie_speed']+=0.05*config['difficulty_coefficient']
        if now - config['last_zombie'] >= 5/config['difficulty_coefficient']:
            a = Zombie(zombieU, 32, 32, surface)
            a.setPosition(random.uniform(1, width), random.uniform(1, height))
            a.setSpeed(random.uniform(config['min_zombie_speed'], config['max_zombie_speed']))
            z.append(a)
            config['last_zombie'] = time.clock()
        if elapsed >5*60:
            config['won'] = True

        xyPlayer = p.getPosition()
        # If panic button was pressed, execute the respective methods for Player and Zombie
        if keys[pygame.K_q] or keys[pygame.K_LSHIFT] or keys[pygame.K_n]:
            if now - p.last_powerup > 3:
                p.panicButton(panicU, sndp)
                for x in z:
                    x.panicButton(p, xyPlayer)
                p.last_powerup = time.clock()
        # create a dart if the "`" was pressed.
        if p.bullets > 0  and last_bullet + 0.1 < now and (keys[pygame.K_BACKQUOTE] or keys[pygame.K_m] or keys[pygame.K_SPACE]):
            last_bullet = now
            p.bullets-=1
            pygame.mixer.Sound.play(snd)
            da = Dart(dartV, p.direction, p.getPosition(), surface)
            d.append(da)
        # Move the player.
        p.keyAction(p.getPosition()[0], p.getPosition()[1], keys)
        # Move the Dart
        for x in d:
            x.updatePositionVelocity()
            if x.getPosition()[0] > surface.get_width() or x.getPosition()[1] > surface.get_height():
                d.remove(x)

        # Move the zombies and update their velocities.
        for x in z:
            x.updatePositionVelocity(p)
            #If there are darts in the game, check if a zombie was hit by any of them.
            for i in d:
                xyDart = i.getPosition()
                #if a zombie was hit, remove it from the zombie list, also remove the dart from the dart list.
                if x.killed(xyDart):
                    p.score+=25
                    d.remove(i)
                    z.remove(x)
                    break
        # Draw.
        if config['last_hit'] and time.clock() - config['last_hit'] > 0.02:
                    config['hit'] = False
        if config['hit']:
            surface.fill([200, 0, 0])
        else:
            surface.fill([0, 0, 0])
        for x in d:
            x.draw()
        for x in z:
            x.draw()
        p.draw()
        if config['won'] or config['lost'] and not (config['won'] and config['lost']):
            if config['lost']:
                headerstr = "Game Over"
                detailstr = "You were devoured with a side of fries!"
            else:
                headerstr = "You won"
                detailstr = "You held out long enough to be rescued!"
            optionsstr = "Press SHIFT and 'N' together to start a new game. Press ESC to quit."
            header = pygame.font.SysFont("arial",40).render(headerstr, 1, (255, 255,255))
            detail = pygame.font.SysFont("arial",20).render(detailstr, 1, (255, 255, 255))
            options = pygame.font.SysFont("arial",13).render(optionsstr, 1, (255, 255, 255))
            detailrect = detail.get_rect()
            headerrect = header.get_rect()
            optionsrect = options.get_rect()
            headerrect.centerx = surface.get_width()/2
            headerrect.centery = surface.get_height()/2
            detailrect.centerx = surface.get_width()/2
            detailrect.centery = surface.get_height()/2+headerrect.height/2
            optionsrect.centerx = surface.get_width()/2
            optionsrect.centery = surface.get_width() - optionsrect.height/2
            surface.blit(options, optionsrect)
            surface.blit(header, headerrect)
            surface.blit(detail, detailrect)
            config['won'] = True
            config['lost'] = True
        pygame.display.flip()

if __name__ == "__main__":
    zombiesGame()
