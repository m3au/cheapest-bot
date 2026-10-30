"""Selection logic for Cheapest Bot. Pure functions, stdlib only."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = ("short", "long", "code")
DEFAULT_INPUT_K = {"short": 20, "code": 50, "long": 200}
HAIKU_5X_ABOVE_K = 100  # Claude Haiku 5.5 bills 5x once a request has more than 100k input tokens


def load_models(path=os.path.join(HERE, "data", "models.json")):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _find(data, name):
    for m in data["models"]:
        if m["name"] == name:
            return m
    raise KeyError(name)


def _pick(data, name, reason, launch_params=None, extra_notes=()):
    m = _find(data, name)
    notes = list(extra_notes)
    if m.get("notes") and "Hidden by default" in m["notes"]:
        notes.append("Hidden by default in Cursor: enable it in the model settings first.")
    out = {
        "model": m["name"],
        "model_id": m["id"],
        "provider": m["provider"],
        "billing": m["billing"],
        "price_per_m": {"input": m["input_per_m"], "output": m["output_per_m"]},
        "launch": {"model": m["id"] or m["name"], "model_params": launch_params or {}},
        "reason": reason,
        "notes": notes,
        "checked": m["checked"],
        "source": m["source"],
        "always": [
            "Name the model on every launch. Unset or Auto falls back to the default model.",
            "Never pick a -fast variant unless you mean to pay for it.",
        ],
    }
    if launch_params and launch_params.get("fast") is False:
        out["launch_sdk"] = {"id": m["id"], "params": [{"id": "fast", "value": "false"}]}
    if m["id"] is None:
        out["notes"].append("Exact model id not recorded yet; pick it by name in Cursor's model list.")
    return out


def cheapest(task="short", max_input_k=None, billing="any", data=None):
    """Return the recommended model and launch params, or raise ValueError."""
    if task not in TASKS:
        raise ValueError("task must be one of: " + ", ".join(TASKS))
    if billing not in ("any", "allowance"):
        raise ValueError("billing must be 'any' or 'allowance'")
    if max_input_k is None:
        max_input_k = DEFAULT_INPUT_K[task]
    if not isinstance(max_input_k, int) or isinstance(max_input_k, bool) or not 0 <= max_input_k <= 10000:
        raise ValueError("max_input_k must be an integer from 0 to 10000")
    data = data or load_models()
    big = max_input_k > HAIKU_5X_ABOVE_K

    if billing == "allowance":
        return _pick(data, "Composer 2.5",
                     "Allowance-only: Composer 2.5 standard is Cursor's cheapest priced allowance model "
                     "($0.50 in / $2.50 out). Without fast=false it bills the Fast variant at $3 / $15.",
                     {"fast": False})
    if not big:
        why = ("Cheapest credit model with decent quality: $0.10 in / $0.50 out, CursorBench 4.0 42.3% "
               "at about $0.32 per task. Stays cheap only up to 100k input tokens per request.")
        if task == "code":
            return _pick(data, "Claude Haiku 5.5", why,
                         extra_notes=["Use High effort. Escalate to a bigger model only if it fails the same task once."])
        return _pick(data, "Claude Haiku 5.5", why)
    if task == "code":
        return _pick(data, "DeepSeek V4.1 Flash 1017",
                     "Over 100k input Haiku 5.5 bills 5x. DeepSeek V4.1 Flash ($0.30 / $1.20) scores 46.3% on "
                     "CursorBench 4.0 at about $0.80 per task.",
                     extra_notes=["Slow: uses many tokens and steps per task."])
    return _pick(data, "GLM 5.3 Flash",
                 "Over 100k input Haiku 5.5 bills 5x. GLM 5.3 Flash is the cheapest credit model listed "
                 "($0.15 in / $0.50 out).")
