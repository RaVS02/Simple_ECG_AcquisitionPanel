import os
from huggingface_hub import snapshot_download

# Tworzymy folder na wagi, jeśli nie istnieje
os.makedirs("models/weights", exist_ok=True)
print("Pobieranie wag z HuggingFace...")
snapshot_download(
    repo_id="KenshiroTM/ecg_weights",
    repo_type="model",
    token="HF_TOKEN",
    local_dir="models/weights",
    allow_patterns="*.pth"
)
print("Pobieranie zakończone!")