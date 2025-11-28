#!/usr/bin/env -S uv run --quiet --script
# Copied from https://www.reddit.com/r/LocalLLaMA/comments/1p82u5k/local_videototext_pipeline_on_apple_silicon/
# /// script
# dependencies = [
#   "opencv-python",
#   "pillow",
#   "mlx-vlm",
#   "openai-whisper",
#   "torch"
# ]
# ///
# # Standard usage
# python video_rag.py video.mp4
#
# # Advanced (Custom prompt + Whisper Large)
# python video_rag.py meeting.mp4 --whisper-model large-v3 --prompt "Describe the charts on the slide."
import argparse
import gc
import os
import re
import time
from pathlib import Path

import cv2
import numpy as np

# Whisper
import whisper
from PIL import Image

# MLX / Qwen-VL
from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

# --------- CONFIG QWEN / MLX ---------
MODEL_PATH = "mlx-community/Qwen3-VL-2B-Instruct-4bit"
RESIZE_DIM = (384, 384)

PREFIXES_A_SUPPRIMER = [
    "cette image montre",
    "l'image montre",
    "sur cette image",
    "dans cette image",
    "voici",
    "c'est",
    "je vois",
    "je peux voir",
    "il y a",
    "on voit",
    "une vue de",
]


# --------- CHARGEMENT DES MODÈLES ---------


def load_qwen_model():
    print(f"⬇️ Chargement du modèle VLM : {MODEL_PATH}...")
    model, processor = load(MODEL_PATH, trust_remote_code=True)
    config = load_config(MODEL_PATH)
    print("✅ Qwen3-VL chargé.")
    return model, processor, config


def load_whisper_model(name: str):
    print(f"⬇️ Chargement du modèle Whisper : {name}...")
    model = whisper.load_model(name)
    print(f"✅ Whisper {name} chargé.")
    return model


# --------- UTILITAIRES TEXTE / TEMPS ---------


def clean_caption(raw_text: str) -> str:
    cleaned = raw_text.strip()
    if not cleaned:
        return ""

    lower_clean = cleaned.lower()

    # évite les réponses du genre "désolé..."
    if "désolé" in lower_clean or "sorry" in lower_clean:
        return ""

    for prefix in PREFIXES_A_SUPPRIMER:
        if lower_clean.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            lower_clean = cleaned.lower()

    cleaned = re.sub(
        r"^(que\s|qu'|:|,|\.|je vois)\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    # coupe à la première ponctuation forte depuis la fin
    m = re.search(r"[\.!?]", cleaned[::-1])
    if m:
        end_pos = len(cleaned) - m.start()
        cleaned = cleaned[:end_pos]

    cleaned = cleaned.strip()
    if not cleaned:
        return ""

    return cleaned[0].upper() + cleaned[1:]


def format_time_str(t_sec: float) -> str:
    minutes = int(t_sec // 60)
    seconds = int(t_sec % 60)
    return f"{minutes:02d}:{seconds:02d}"


# --------- FEATURES POUR SCÈNES ---------


def compute_frame_feature(frame_bgr) -> np.ndarray:
    """
    Crée une empreinte simple de l'image pour la détection de scènes.
    -> grayscale, resize 64x64, vector 0–1.
    """
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (64, 64))
    vec = small.astype("float32") / 255.0
    return vec.flatten()


# --------- PASS 1 : DÉTECTION DE SCÈNES (SANS QWEN) ---------


def detect_scenes(
    video_path: str, sample_fps: float = 1.0, scene_threshold: float = 0.20
):
    """
    Passe 1 : on parcourt la vidéo à sample_fps (ex: 1 image/s),
    on calcule un feature par frame, et on détecte les changements
    de scène selon un seuil de différence moyenne.

    Retourne :
    - scenes_raw : liste de dicts { "start_sec", "end_sec" }
    - duration_sec : durée approx de la vidéo
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Impossible d'ouvrir la vidéo : {video_path}")

    base_fps = cap.get(cv2.CAP_PROP_FPS)
    if base_fps <= 0:
        base_fps = 25.0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / base_fps if total_frames > 0 else 0

    frame_interval = max(1, int(round(base_fps / sample_fps)))

    print(f"[SCENES] FPS vidéo ≈ {base_fps:.2f}")
    print(f"[SCENES] Frames totales : {total_frames}")
    print(f"[SCENES] Durée approx : {duration_sec:.1f} s")
    print(
        f"[SCENES] Échantillonnage à {sample_fps} img/s => intervalle {frame_interval} frames"
    )
    print(f"[SCENES] Seuil de scène : {scene_threshold}")

    scenes_raw = []
    last_feat = None
    current_start_sec = None
    prev_t_sec = None

    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval != 0:
            frame_idx += 1
            continue

        t_sec = frame_idx / base_fps
        feat = compute_frame_feature(frame)

        if last_feat is None:
            # première frame
            current_start_sec = t_sec
            prev_t_sec = t_sec
            last_feat = feat
        else:
            diff = float(np.mean(np.abs(feat - last_feat)))
            if diff > scene_threshold:
                # clôture de la scène précédente
                scenes_raw.append(
                    {
                        "start_sec": current_start_sec,
                        "end_sec": prev_t_sec,
                    }
                )
                # nouvelle scène
                current_start_sec = t_sec

            prev_t_sec = t_sec
            last_feat = feat

        frame_idx += 1

    # clôture de la dernière scène
    if current_start_sec is not None:
        end_sec = duration_sec if duration_sec > 0 else prev_t_sec
        scenes_raw.append(
            {
                "start_sec": current_start_sec,
                "end_sec": end_sec,
            }
        )

    cap.release()

    print(f"[SCENES] Nombre de scènes détectées : {len(scenes_raw)}")
    for i, sc in enumerate(scenes_raw, start=1):
        print(
            f"  SCENE {i}: {format_time_str(sc['start_sec'])} - {format_time_str(sc['end_sec'])}"
        )

    return scenes_raw, duration_sec


# --------- PASS 2 : QWEN SUR UNE FRAME REPRÉSENTATIVE PAR SCÈNE ---------


def grab_frame_at_time(video_path: str, t_sec: float):
    """
    Récupère une frame à t_sec (en secondes).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Impossible d'ouvrir la vidéo : {video_path}")

    cap.set(cv2.CAP_PROP_POS_MSEC, t_sec * 1000.0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    return frame


def describe_scene_qwen(
    model,
    processor,
    config,
    video_path: str,
    start_sec: float,
    end_sec: float,
    max_tokens: int,
    prompt: str,
):
    """
    Choisit un temps représentatif (milieu de la scène),
    récupère la frame correspondante et la donne à Qwen-VL.
    """
    rep_sec = (start_sec + end_sec) / 2.0
    frame = grab_frame_at_time(video_path, rep_sec)
    if frame is None:
        return None

    small_frame = cv2.resize(frame, RESIZE_DIM)
    frame_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(frame_rgb)

    formatted_prompt = apply_chat_template(processor, config, prompt, num_images=1)

    output = generate(
        model,
        processor,
        formatted_prompt,
        pil_image,
        max_tokens=max_tokens,
        verbose=False,
        repetition_penalty=1.05,
        temp=0.0,
    )

    if hasattr(output, "text"):
        raw_text = output.text
    else:
        raw_text = str(output)

    cleaned = clean_caption(raw_text)
    if not cleaned:
        return None

    return cleaned


def describe_all_scenes(
    model, processor, config, video_path: str, scenes_raw, max_tokens: int, prompt: str
):
    """
    Pour chaque scène brute (start_sec, end_sec),
    appelle Qwen-VL UNE fois,
    et retourne une liste de scènes enrichies :
    {
      "start_sec": ...,
      "end_sec": ...,
      "start_str": "MM:SS",
      "end_str": "MM:SS",
      "caption": "..."
    }
    """
    scenes = []
    t0 = time.time()

    for idx, sc in enumerate(scenes_raw, start=1):
        start_sec = sc["start_sec"]
        end_sec = sc["end_sec"]
        print(
            f"[VLM-SCENE] SCENE {idx} => {format_time_str(start_sec)} - {format_time_str(end_sec)}"
        )
        caption = describe_scene_qwen(
            model,
            processor,
            config,
            video_path,
            start_sec,
            end_sec,
            max_tokens=max_tokens,
            prompt=prompt,
        )
        if caption is None:
            caption = "(Description indisponible)"

        scene_entry = {
            "start_sec": start_sec,
            "end_sec": end_sec,
            "start_str": format_time_str(start_sec),
            "end_str": format_time_str(end_sec),
            "caption": caption,
        }
        print("    ->", caption)
        scenes.append(scene_entry)

    print(f"[VLM-SCENE] Temps total VLM scènes : {time.time() - t0:.1f} s")
    return scenes


# --------- WHISPER ---------


def transcribe_audio_whisper(
    whisper_model, video_path: str, language: str | None = None
) -> dict:
    """
    Transcrit directement la vidéo (Whisper utilise ffmpeg en interne).
    Retourne l'objet complet (avec segments).
    """
    print("[WHISPER] Transcription en cours...")
    t0 = time.time()
    result = whisper_model.transcribe(video_path, language=language)
    print(f"[WHISPER] Transcription terminée en {time.time() - t0:.1f} s")
    return result


# --------- CONSTRUCTION DU TEXTE FINAL ---------


def build_output_text(
    transcription: dict, scenes, video_path: str, duration_sec: float
) -> str:
    lines = []

    lines.append("### CONTEXTE VIDEO POUR LLM (UTF-8)\n")
    lines.append(f"Fichier vidéo d'origine : {video_path}")
    lines.append(f"Durée approximative : {duration_sec:.1f} secondes\n")

    # --- SECTION 0 : description globale approximative ---
    lines.append("SECTION 0 : DESCRIPTION GLOBALE (à partir des scènes)\n")
    if scenes:
        first = scenes[0]
        mid = scenes[len(scenes) // 2]
        last = scenes[-1]

        lines.append(
            f"- Début [{first['start_str']} - {first['end_str']}]: {first['caption']}"
        )
        if mid is not first and mid is not last:
            lines.append(
                f"- Milieu [{mid['start_str']} - {mid['end_str']}]: {mid['caption']}"
            )
        lines.append(
            f"- Fin [{last['start_str']} - {last['end_str']}]: {last['caption']}"
        )
    else:
        lines.append("(Aucune scène détectée.)")
    lines.append("")

    # --- SECTION 1 : transcription audio ---
    lines.append("SECTION 1 : TRANSCRIPTION AUDIO (Whisper)\n")
    full_text = transcription.get("text", "").strip()
    lines.append("TEXTE COMPLET :")
    lines.append(full_text if full_text else "(Transcription vide ou indisponible.)")
    lines.append("")

    if "segments" in transcription:
        lines.append("SEGMENTS HORODATES :")
        for seg in transcription["segments"]:
            start = seg.get("start", 0.0)
            end = seg.get("end", 0.0)
            txt = seg.get("text", "").strip()
            m1, s1 = divmod(int(start), 60)
            m2, s2 = divmod(int(end), 60)
            lines.append(f"[{m1:02d}:{s1:02d} - {m2:02d}:{s2:02d}] {txt}")
        lines.append("")

    # --- SECTION 2 : scènes visuelles décrites ---
    lines.append("SECTION 2 : SCENES VISUELLES (Qwen3-VL, 1 description par scène)\n")
    if not scenes:
        lines.append("(Aucune scène disponible.)")
    else:
        for idx, sc in enumerate(scenes, start=1):
            lines.append(f"SCENE {idx} [{sc['start_str']} - {sc['end_str']}]")
            lines.append(f"- Description : {sc['caption']}")
            lines.append("")

    lines.append("\nFIN DU CONTEXTE.\n")
    return "\n".join(lines)


# --------- MAIN ---------


def main():
    parser = argparse.ArgumentParser(
        description="Analyse vidéo V3.1 : détection de scènes + Whisper + Qwen3-VL (1 description par scène)."
    )
    parser.add_argument(
        "video", help="Chemin de la vidéo (ex: .mp4, .mov iPhone, etc.)"
    )
    parser.add_argument(
        "--sample-fps",
        type=float,
        default=1.0,
        help="FPS d'échantillonnage pour détecter les scènes (défaut: 1.0)",
    )
    parser.add_argument(
        "--scene-threshold",
        type=float,
        default=0.20,
        help="Seuil de changement de scène (différence moyenne 0-1, défaut: 0.20)",
    )
    parser.add_argument(
        "--whisper-model",
        type=str,
        default="small",
        help="Modèle Whisper: small, medium, large-v3, etc. (défaut: small)",
    )
    parser.add_argument(
        "--whisper-lang",
        type=str,
        default=None,
        help="Code langue (ex: 'fr'), ou None pour auto-détection.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=60,
        help="Max tokens générés par Qwen-VL par scène (défaut: 60)",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=(
            "Décris factuellement ce qui est présent dans l'image en français. "
            "Sois direct et précis, sans interprétation inutile."
        ),
        help="Prompt de description pour Qwen-VL (défaut: description factuelle en français).",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="contexte_video_v3_1.txt",
        help="Fichier texte de sortie (UTF-8).",
    )
    args = parser.parse_args()

    video_path = os.path.abspath(args.video)
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Vidéo introuvable : {video_path}")

    # 1) Détection de scènes (rapide, sans modèles)
    scenes_raw, duration_sec = detect_scenes(
        video_path,
        sample_fps=args.sample_fps,
        scene_threshold=args.scene_threshold,
    )

    # 2) Whisper d'abord (audio)
    model_whisper = load_whisper_model(args.whisper_model)
    transcription = transcribe_audio_whisper(
        model_whisper, video_path, language=args.whisper_lang
    )

    # 🔥 Libère Whisper de la RAM
    del model_whisper
    gc.collect()

    # 3) Puis Qwen-VL (vision)
    model_vlm, processor_vlm, config_vlm = load_qwen_model()

    # 4) Description de chaque scène (1 frame représentative)
    scenes = describe_all_scenes(
        model_vlm,
        processor_vlm,
        config_vlm,
        video_path,
        scenes_raw,
        max_tokens=args.max_tokens,
        prompt=args.prompt,
    )

    # 5) Construction du texte final
    output_text = build_output_text(
        transcription,
        scenes,
        video_path,
        duration_sec,
    )

    out_path = Path(args.out)
    out_path.write_text(output_text, encoding="utf-8")
    print(f"\n✅ Fichier contexte V3.1 généré : {out_path}")
    print(
        "   Tu peux maintenant copier/coller ce fichier dans Open WebUI ou LM Studio (RAG)."
    )


if __name__ == "__main__":
    main()
