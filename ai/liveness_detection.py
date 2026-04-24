"""
ai/liveness_detection.py — Multi-signal Liveness Score Computation.
Yeh module anti-spoof ke baad run hota hai aur live presence verify karta hai.
Screen ya photo se captured frame ka liveness score asli chehra dikhane se kam hoga.
"""
import cv2
import numpy as np
import logging

logger = logging.getLogger("AI_LIVENESS")


def _blur_score(gray: np.ndarray) -> float:
    """Laplacian variance — screen pe shown image usually sharper/blurrier than real face."""
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Real cameras at normal distance: 100-800 variance.
    # Screen images: either too sharp (>= 1000) or too blurry (< 50) compared to real.
    # We want "natural camera blur" to score high.
    if laplacian_var < 50:
        return 0.1   # Too blurry — fake/printed photo
    elif laplacian_var > 1200:
        return 0.4   # Suspiciously sharp (screen image scaled up)
    else:
        return min(1.0, laplacian_var / 600.0)


def _entropy_score(gray: np.ndarray) -> float:
    """Pixel entropy — checks if image has natural information distribution."""
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist.ravel() / hist.sum()
    non_zero = hist[hist > 0]
    entropy = -np.sum(non_zero * np.log2(non_zero))
    # Natural face: entropy typically between 5.5-7.5
    # Screen image: can be near 7.5-8.0 (too uniform/flat)
    return min(1.0, max(0.0, (entropy - 4.0) / 4.0))


def _specular_reflection_score(image_bgr: np.ndarray) -> float:
    """
    Real human skin has specular reflections with a specific distribution.
    Screen photos have too-uniform or absent specular highlights.
    Checks for natural skin highlight distribution.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    # Look for bright spots in face region (natural specular highlights)
    h, w = gray.shape
    face = gray[h // 5: 4 * h // 5, w // 5: 4 * w // 5]

    bright_pixels = np.sum(face > 200)
    mid_pixels = np.sum((face > 100) & (face <= 200))
    total = face.size

    bright_ratio = bright_pixels / total
    mid_ratio = mid_pixels / total

    # Real face: some bright spots (0.5%-8%), healthy mid range
    # Screen photo: either no bright spots or too many
    if bright_ratio < 0.003 or bright_ratio > 0.15:
        return 0.3  # Suspiciously flat or over-exposed
    if mid_ratio < 0.2:
        return 0.4  # Suspiciously few mid-tones
    return 0.9


def _resolution_score(height: int, width: int) -> float:
    """Resolution-based score (lower weight helper)."""
    min_dim = min(height, width)
    if min_dim < 224:
        return 0.0
    return min(1.0, 0.5 + (max(0, min_dim - 224) / (1080 - 224) * 0.5))


def _chromatic_noise_score(image_bgr: np.ndarray) -> float:
    """
    Natural camera captures have slight chromatic noise (grain) in colors.
    Screen-displayed images are cleaner — lack of natural camera noise is a spoof signal.
    We check per-channel variance in a smooth region.
    """
    h, w = image_bgr.shape[:2]
    # Use forehead area (top-center) as a smooth skin patch
    patch = image_bgr[h // 8: h // 4, w // 3: 2 * w // 3]
    if patch.size == 0:
        return 0.5

    # Real camera photo has noise → inter-channel variance difference
    b_std = np.std(patch[:, :, 0].astype(np.float32))
    g_std = np.std(patch[:, :, 1].astype(np.float32))
    r_std = np.std(patch[:, :, 2].astype(np.float32))

    avg_std = (b_std + g_std + r_std) / 3.0
    logger.debug(f"Chromatic noise avg_std: {avg_std:.4f}")

    # Real camera: avg_std ~8-30; Screen image compressed/smooth: < 6
    if avg_std < 5.0:
        return 0.2   # Too clean — screen/digital copy
    elif avg_std > 40.0:
        return 0.5   # Too noisy — maybe artificial
    return min(1.0, avg_std / 30.0)


def compute_liveness(image_bgr: np.ndarray) -> float:
    """
    Computes a composite liveness score between 0.0 and 1.0.
    Yeh multiple signals combine karta hai.
    Threshold (config): 0.85 — sirf sacche live faces pass honge.
    """
    height, width, _ = image_bgr.shape
    if height < 224 or width < 224:
        raise ValueError("Image resolution must be at least 224x224")

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    blur       = _blur_score(gray)
    entropy    = _entropy_score(gray)
    specular   = _specular_reflection_score(image_bgr)
    resolution = _resolution_score(height, width)
    chroma     = _chromatic_noise_score(image_bgr)

    logger.debug(
        f"Liveness signals — blur:{blur:.2f}, entropy:{entropy:.2f}, "
        f"specular:{specular:.2f}, resolution:{resolution:.2f}, chroma:{chroma:.2f}"
    )

    # Weighted average — chroma aur specular ko zyada weight (screen ke against)
    score = (
        blur       * 0.15 +
        entropy    * 0.15 +
        specular   * 0.30 +
        resolution * 0.10 +
        chroma     * 0.30
    )

    final = float(min(1.0, max(0.0, score)))
    logger.info(f"Liveness Score: {final:.4f}")
    return final
