_SPEED_MULTIPLIER = 10


class _Physics(object):
    def __init__(self, sprite, can_move, stable, x_speed, y_speed,
                 obeys_gravity, bounciness, mass, friction):
        """

        Examples of objects with the different parameters:

            Blocks that can be knocked over (the default):
                can_move = True
                stable = False
                obeys_gravity = True
            Jumping platformer character:
                can_move = True
                stable = True (doesn't fall over)
                obeys_gravity = True
            Moving platform:
                can_move = True
                stable = True
                obeys_gravity = False
            Stationary platform:
                can_move = False
                (others don't matter)
        """
        self.sprite = sprite
        self._can_move = can_move
        self._stable = stable
        self._x_speed = x_speed * _SPEED_MULTIPLIER
        self._y_speed = y_speed * _SPEED_MULTIPLIER
        self._obeys_gravity = obeys_gravity
        self._bounciness = bounciness
        self._mass = mass
        self._friction = friction

        self._make_pymunk()

    def _make_pymunk(self):
        mass = self.mass if self.can_move else 0

        # non-moving line shapes are platforms and it's easier to take care of them less-generically
        if not self.can_move and isinstance(self.sprite, line):
            self._pymunk_body = _physics_space.static_body.copy()
            self._pymunk_shape = _pymunk.Segment(
                self._pymunk_body, (self.sprite.x, self.sprite.y),
                (self.sprite.x1, self.sprite.y1), self.sprite.thickness)
        else:
            if self.stable:
                moment = _pymunk.inf
            elif isinstance(self.sprite, Circle):
                moment = _pymunk.moment_for_circle(mass, 0, self.sprite.radius,
                                                   (0, 0))
            elif isinstance(self.sprite, line):
                moment = _pymunk.moment_for_box(
                    mass, (self.sprite.length, self.sprite.thickness))
            else:
                moment = _pymunk.moment_for_box(
                    mass, (self.sprite.width, self.sprite.height))

            if self.can_move and not self.stable:
                body_type = _pymunk.Body.DYNAMIC
            elif self.can_move and self.stable:
                if self.obeys_gravity or _physics_space.gravity == 0:
                    body_type = _pymunk.Body.DYNAMIC
                else:
                    body_type = _pymunk.Body.KINEMATIC
            else:
                body_type = _pymunk.Body.STATIC
            self._pymunk_body = _pymunk.Body(mass, moment, body_type=body_type)

            if isinstance(self.sprite, line):
                self._pymunk_body.position = self.sprite.x + (
                    self.sprite.x1 - self.sprite.x) / 2, self.sprite.y + (
                        self.sprite.y1 - self.sprite.y) / 2
            else:
                self._pymunk_body.position = self.sprite.x, self.sprite.y

            self._pymunk_body.angle = _math.radians(self.sprite.angle)

            if self.can_move:
                self._pymunk_body.velocity = (self._x_speed, self._y_speed)

            if not self.obeys_gravity:
                self._pymunk_body.velocity_func = lambda body, gravity, damping, dt: None

            if isinstance(self.sprite, Circle):
                self._pymunk_shape = _pymunk.Circle(self._pymunk_body,
                                                    self.sprite.radius, (0, 0))
            elif isinstance(self.sprite, line):
                self._pymunk_shape = _pymunk.Segment(
                    self._pymunk_body, (self.sprite.x, self.sprite.y),
                    (self.sprite.x1, self.sprite.y1), self.sprite.thickness)
            else:
                self._pymunk_shape = _pymunk.Poly.create_box(
                    self._pymunk_body, (self.sprite.width, self.sprite.height))

        self._pymunk_shape.elasticity = _clamp(self.bounciness, 0, .99)
        self._pymunk_shape.friction = self._friction
        _physics_space.add(self._pymunk_body, self._pymunk_shape)

    def clone(self, sprite):
        # TODO: finish filling out params
        return self.__class__(
            sprite=sprite,
            can_move=self.can_move,
            x_speed=self.x_speed,
            y_speed=self.y_speed,
            obeys_gravity=self.obeys_gravity)

    def pause(self):
        self._remove()

    def unpause(self):
        if not self._pymunk_body and not self._pymunk_shape:
            _physics_space.add(self._pymunk_body, self._pymunk_shape)

    def _remove(self):
        if self._pymunk_body:
            _physics_space.remove(self._pymunk_body)
        if self._pymunk_shape:
            _physics_space.remove(self._pymunk_shape)

    @property
    def can_move(self):
        return self._can_move

    @can_move.setter
    def can_move(self, _can_move):
        prev_can_move = self._can_move
        self._can_move = _can_move
        if prev_can_move != _can_move:
            self._remove()
            self._make_pymunk()

    @property
    def x_speed(self):
        return self._x_speed / _SPEED_MULTIPLIER

    @x_speed.setter
    def x_speed(self, _x_speed):
        self._x_speed = _x_speed * _SPEED_MULTIPLIER
        self._pymunk_body.velocity = self._x_speed, self._pymunk_body.velocity[1]

    @property
    def y_speed(self):
        return self._y_speed / _SPEED_MULTIPLIER

    @y_speed.setter
    def y_speed(self, _y_speed):
        self._y_speed = _y_speed * _SPEED_MULTIPLIER
        self._pymunk_body.velocity = self._pymunk_body.velocity[0], self._y_speed

    @property
    def bounciness(self):
        return self._bounciness

    @bounciness.setter
    def bounciness(self, _bounciness):
        self._bounciness = _bounciness
        self._pymunk_shape.elasticity = _clamp(self._bounciness, 0, .99)

    @property
    def stable(self):
        return self._stable

    @stable.setter
    def stable(self, _stable):
        prev_stable = self._stable
        self._stable = _stable
        if self._stable != prev_stable:
            self._remove()
            self._make_pymunk()

    @property
    def mass(self):
        return self._mass

    @mass.setter
    def mass(self, _mass):
        self._mass = _mass
        self._pymunk_body.mass = _mass

    @property
    def obeys_gravity(self):
        return self._obeys_gravity

    @obeys_gravity.setter
    def obeys_gravity(self, _obeys_gravity):
        self._obeys_gravity = _obeys_gravity
        if _obeys_gravity:
            self._pymunk_body.velocity_func = _pymunk.Body.update_velocity
        else:
            self._pymunk_body.velocity_func = lambda body, gravity, damping, dt: None


class _Gravity(object):
    # TODO: make this default to vertical if horizontal is 0?
    vertical = -100 * _SPEED_MULTIPLIER
    horizontal = 0

gravity = _Gravity()
_physics_space = _pymunk.Space()
_physics_space.sleep_time_threshold = 0.5 
_physics_space.idle_speed_threshold = 0 # pymunk estimates good threshold based on gravity
_physics_space.gravity = gravity.horizontal, gravity.vertical

_NUM_SIMULATION_STEPS = 3
def _simulate_physics():
    # more steps means more accurate simulation, but more processing time
    for _ in range(_NUM_SIMULATION_STEPS):
        # the smaller the simulation step, the more accurate the simulation
        _physics_space.step(1/(60.0*_NUM_SIMULATION_STEPS))

def set_gravity(vertical=-100, horizontal=None):
    global gravity
    gravity.vertical = vertical*_SPEED_MULTIPLIER
    if horizontal != None:
        gravity.horizontal = horizontal*_SPEED_MULTIPLIER

    _physics_space.gravity = gravity.horizontal, gravity.vertical

_walls = []

def _create_walls():
    def _create_wall(a, b):
        segment = _pymunk.Segment(_physics_space.static_body, a, b, 0.0)
        segment.elasticity = 1.0
        segment.friction = .1
        _physics_space.add(segment)
        return segment

    _walls.append(_create_wall([screen.left, screen.top], [screen.right, screen.top])) # top
    _walls.append(_create_wall([screen.left, screen.bottom], [screen.right, screen.bottom])) # bottom
    _walls.append(_create_wall([screen.left, screen.bottom], [screen.left, screen.top])) # left
    _walls.append(_create_wall([screen.right, screen.bottom], [screen.right, screen.top])) # right

def _remove_walls():
    _physics_space.remove(_walls)
    _walls.clear()

_create_walls()