import json
import itertools
import subprocess
import os

BASE_PATH = "C:\\Users\\Usuario\\Downloads\\crypto_bot"

with open(os.path.join(BASE_PATH, "config_strategies.json")) as f:
    config = json.load(f)

for exp in config["experiments"]:
    print(f"\n🧪 EJECUTANDO {exp['id']}")

    keys = list(exp["strategy"]["params"].keys())
    values = list(exp["strategy"]["params"].values())

    for combo in itertools.product(*values):
        params = dict(zip(keys, combo))

        strategy = {
            "name": exp["strategy"]["name"],
            "params": params
        }

        task = {
            "symbol": exp["symbol"],
            "intervals": exp["intervals"],
            "start": exp["start"],
            "end": exp["end"]
        }

        # Guardar archivos que usa tu bot
        with open(os.path.join(BASE_PATH, "strategy.json"), "w") as f:
            json.dump(strategy, f, indent=2)

        with open(os.path.join(BASE_PATH, "task.json"), "w") as f:
            json.dump(task, f, indent=2)

        print(f"▶️ Params: {params}")

        # Ejecutar tu bot SIN modificarlo
        subprocess.run(["python", "bot.py"], cwd=BASE_PATH)
