"""Persist / restore fitted governance components so the service boots fast."""
import os, pickle, json

def save_artifacts(artifacts_dir, gate, guard, meta=None):
    os.makedirs(artifacts_dir, exist_ok=True)
    with open(os.path.join(artifacts_dir, "gate.pkl"), "wb") as f:
        pickle.dump(gate, f)
    with open(os.path.join(artifacts_dir, "guard.pkl"), "wb") as f:
        pickle.dump(guard, f)
    with open(os.path.join(artifacts_dir, "manifest.json"), "w") as f:
        json.dump(meta or {}, f, indent=2, default=str)

def load_artifacts(artifacts_dir):
    with open(os.path.join(artifacts_dir, "gate.pkl"), "rb") as f:
        gate = pickle.load(f)
    with open(os.path.join(artifacts_dir, "guard.pkl"), "rb") as f:
        guard = pickle.load(f)
    meta = {}
    mp = os.path.join(artifacts_dir, "manifest.json")
    if os.path.exists(mp):
        meta = json.load(open(mp))
    return gate, guard, meta
