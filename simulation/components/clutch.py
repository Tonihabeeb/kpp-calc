from dataclasses import dataclass


@dataclass
class ClutchState:
    c: float  # Coupling coefficient (0-1)
    state: str  # 'DISENGAGED' | 'SLIP' | 'ENGAGED'
    timer: float  # Internal timer for slip dwell


class OverrunningClutch:
    def __init__(self, tau_eng=200, slip_time=0.2, w_min=5, w_max=40):
        self.tau_eng = tau_eng
        self.slip_time = slip_time
        self.w_min = w_min
        self.w_max = w_max
        self.state = ClutchState(c=0.0, state="DISENGAGED", timer=0.0)

    def update(self, tau_net, omega, dt):
        # FSM logic for clutch engagement
        if self.state.state == "DISENGAGED":
            if tau_net >= self.tau_eng and omega >= self.w_min:
                self.state.state = "SLIP"
                self.state.timer = self.slip_time
                self.state.c = 0.0
        elif self.state.state == "SLIP":
            self.state.timer -= dt
            self.state.c = min(1.0, 1.0 - self.state.timer / self.slip_time)
            if self.state.timer <= 0:
                self.state.state = "ENGAGED"
                self.state.c = 1.0
        elif self.state.state == "ENGAGED":
            if tau_net < 0 or omega < self.w_min or omega > self.w_max:
                self.state.state = "DISENGAGED"
                self.state.c = 0.0
        return self.state.c
