import argparse
import json
import math
import random
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List
import requests


@dataclass
class Appliance:
    name: str
    base_w: float
    var_w: float
    on_probability: float
    duty_cycle: float = 1.0
    state: bool = False
    phase: float = field(default_factory=lambda: random.random() * 2 * math.pi)

    def step(self, t: float, tod_factor: float) -> float:
        if random.random() < self.on_probability:
            self.state = not self.state

        if not self.state:
            return 0.0

        if self.duty_cycle < 1.0:
            cyc = (math.sin(t / 30.0 + self.phase) + 1) / 2
            if cyc > self.duty_cycle:
                return 0.0

        noise = random.uniform(-self.var_w, self.var_w)
        wave = math.sin(t / 10.0 + self.phase) * (self.var_w * 0.3)
        return max(0.0, (self.base_w + noise + wave) * tod_factor)


def time_of_day_factor() -> float:
    lt = time.localtime()
    hour = lt.tm_hour + lt.tm_min / 60.0
    if 18 <= hour <= 23:
        return 1.15
    if 0 <= hour <= 6:
        return 0.85
    return 1.0


def build_appliance_set():
    return [
        Appliance("FRIDGE", 90, 30, 0.02, duty_cycle=0.55, state=True),
        Appliance("ROUTER", 12, 2, 0.00, state=True),
        Appliance("LIGHTS", 80, 40, 0.05),
        Appliance("TV", 120, 30, 0.03),
        Appliance("AC", 900, 300, 0.02),
        Appliance("KETTLE", 1500, 100, 0.01),
        Appliance("WASHER", 500, 200, 0.008, duty_cycle=0.7),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--meters", nargs="+", required=True, help="多个 meter_id，如 METER001 METER002")
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--voltage", type=float, default=220.0)
    args = ap.parse_args()

    sess = requests.Session()

    # 为每一个 meter 准备独立设备 + 独立电量
    meter_devices = {m: build_appliance_set() for m in args.meters}
    meter_energy = {m: 0.0 for m in args.meters}

    print(f"[MULTI-SIM] Running meters: {args.meters}")

    while True:
        tod = time_of_day_factor()
        now = time.time()

        for meter_id, devices in meter_devices.items():
            total_w = 0
            data = {}

            for dev in devices:
                w = dev.step(now, tod)
                total_w += w
                data[dev.name] = {"power_w": round(w, 2), "on": w > 0}

            current_a = total_w / args.voltage
            meter_energy[meter_id] += total_w / 3600.0

            payload = {
                "meter_id": meter_id,
                "data": {
                    **data,
                    "_TOTAL": {
                        "power_w": round(total_w, 2),
                        "voltage_v": args.voltage,
                        "current_a": round(current_a, 3),
                        "energy_wh_total": round(meter_energy[meter_id], 3),
                        "energy_kwh_total": round(meter_energy[meter_id] / 1000.0, 6),
                    }
                }
            }

            try:
                resp = sess.post(args.endpoint, json=payload, timeout=3)
                if resp.status_code >= 400:
                    print(f"[{meter_id}] HTTP", resp.status_code, resp.text[:200])
                else:
                    print(f"[{meter_id}] total_w={payload['data']['_TOTAL']['power_w']}")
            except Exception as e:
                print(f"[{meter_id}] POST failed: {e}")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
