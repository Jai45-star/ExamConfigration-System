# ai/anti_spoof.py — Smart Anti-Spoofing Detection (Lighting-Aware)
# Yeh module real lighting conditions (shadow, poor light, phone torch) ko
# screen/photo spoofing se distinguish karta hai.
import cv2
import numpy as np
import logging

logger = logging.getLogger("AI_ANTISPOOF")


def detect_glare(image_bgr: np.ndarray, threshold_pixel: int = 240, max_glare_ratio: float = 0.15) -> bool:
    """
    SMART Glare Detection — screen ki chamak vs natural reflect ka fark samjhna.

    Screen/Photo spoofing: Bright pixels SCATTERED aur UNIFORM hote hain poore frame mein.
    Natural sources (sun, torch, window): LOCALIZED ek ya do spots, rest dark.

    Logic:
      - Agar bright pixels < 15% of frame = definitely real, skip.
      - Agar bright pixels > 15%: check karo ki kitne ALAG-ALAG clusters hain.
        > 8 separate bright clusters = screen jaise scatter = SPOOF.
        <= 8 clusters = localized natural highlight = REAL.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    glare_mask = (gray >= threshold_pixel).astype(np.uint8)
    glare_ratio = float(np.sum(glare_mask)) / float(gray.size)

    logger.debug(f"Glare ratio: {glare_ratio:.4f}")

    # Glare kam hai — sab theek hai
    if glare_ratio <= max_glare_ratio:
        return False

    # Glare zyada hai — lakin natural hai ya screen?
    # Connected components se check karo: localized = real, scattered = screen
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(glare_mask)

    # Background label (0) skip karke count karo meaningful bright spots
    significant_spots = sum(
        1 for i in range(1, num_labels)
        if stats[i, cv2.CC_STAT_AREA] > 80  # Sirf bade patches count karo
    )
    logger.debug(f"Glare: ratio={glare_ratio:.3f}, distinct_spots={significant_spots}")

    # Screen mein bright pixels poore frame mein scattered hote hain (many spots)
    # Natural torch/sun: 1-3 concentrated spots
    return significant_spots > 8


def detect_screen_moire(image_bgr: np.ndarray) -> bool:
    """
    Moire Pattern Detection — screen pixels ka regular grid pattern FFT mein dikh jaata hai.
    Real face, shadow, ya poor lighting isko trigger NAHI karte — yeh screen-specific hai.
    Is check ko change karne ki zaroorat nahi.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray_float = np.float32(gray)

    dft = cv2.dft(gray_float, flags=cv2.DFT_COMPLEX_OUTPUT)
    dft_shift = np.fft.fftshift(dft[:, :, 0] + 1j * dft[:, :, 1])
    magnitude = np.abs(dft_shift)
    magnitude_log = np.log1p(magnitude)

    h, w = magnitude_log.shape
    cy, cx = h // 2, w // 2

    center_r = min(h, w) // 10
    magnitude_log[cy - center_r:cy + center_r, cx - center_r:cx + center_r] = 0

    top_region    = magnitude_log[:cy // 3, :]
    bottom_region = magnitude_log[2 * cy // 3:, :]
    left_region   = magnitude_log[:, :cx // 3]
    right_region  = magnitude_log[:, 2 * cx // 3:]

    side_mean   = (top_region.mean() + bottom_region.mean() +
                   left_region.mean() + right_region.mean()) / 4.0
    center_band = magnitude_log[cy // 3:2 * cy // 3, cx // 3:2 * cx // 3].mean()

    ratio = side_mean / (center_band + 1e-6)
    logger.debug(f"Moire freq ratio: {ratio:.4f}")
    return ratio > 0.95


def detect_flat_texture(image_bgr: np.ndarray) -> bool:
    """
    SMART Texture Analysis — brightness-aware version.

    Problem pehle: Shadow/dim light mein real face ka texture variance drop ho jaata tha,
    aur system use screen jaisa treat karta tha.

    Fix: Threshold ko brightness ke saath scale karo.
    - Normal light (128 brightness): threshold = 35
    - Dim light / shadow (64 brightness): threshold = 18  (half)
    - Very dark (< 40 brightness): check skip karo — judge karna impossible hai
    - Screen photo: SAME brightness mein FLAT texture hota hai (variance < scaled threshold)
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    face_region = gray[h // 6: 5 * h // 6, w // 6: 5 * w // 6]

    mean_brightness = float(np.mean(face_region))

    # Bahut dark hai — texture judge karna possible nahi, false positive avoid karo
    if mean_brightness < 40:
        logger.debug(f"Scene too dark ({mean_brightness:.1f}) — skipping texture check to avoid false positive")
        return False

    kernel = np.ones((15, 15), np.float32) / (15 * 15)
    local_mean    = cv2.filter2D(face_region.astype(np.float32), -1, kernel)
    local_sq_mean = cv2.filter2D((face_region.astype(np.float32)) ** 2, -1, kernel)
    local_var     = local_sq_mean - local_mean ** 2
    mean_local_var = float(np.mean(local_var))

    # Brightness-normalized threshold:
    # Normal (128) → 35.0 | Half-dim (64) → ~17.5 | Very dim but ok (40) → ~11
    brightness_factor  = mean_brightness / 128.0
    scaled_threshold   = 35.0 * max(brightness_factor, 0.45)  # Floor at 45% scale

    logger.debug(
        f"Texture: variance={mean_local_var:.2f}, brightness={mean_brightness:.1f}, "
        f"effective_threshold={scaled_threshold:.2f}"
    )
    return mean_local_var < scaled_threshold


def detect_color_flatness(image_bgr: np.ndarray) -> bool:
    """
    SMART Color Flatness — darkness-aware version.

    Problem pehle: Dark room ya shadow mein real face ka saturation naturally kam hota hai,
    jo screen jaisi reading deta tha.

    Fix: Agar scene dark hai (mean brightness < 60) toh saturation check skip karo.
    Screen photos bright hoti hain aur phir bhi flat saturation dikhati hain.
    Ek dark real face mein low saturation = normal, spoof nahi.
    """
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    saturation   = hsv[:, :, 1].astype(np.float32)
    value_channel = hsv[:, :, 2].astype(np.float32)

    mean_brightness = float(np.mean(value_channel))

    # Dark scene — low saturation expected, check skip karo
    if mean_brightness < 60:
        logger.debug(
            f"Scene dark ({mean_brightness:.1f} brightness) — "
            f"skipping color flatness to avoid false positive in low light"
        )
        return False

    sat_std = float(np.std(saturation))
    logger.debug(f"Saturation std: {sat_std:.4f} (brightness: {mean_brightness:.1f})")

    # Screen photo: brightness high hai BUT saturation compressed/flat hai
    # Real face in normal light: saturation naturally varies (skin, lips, background)
    return sat_std < 15.0


def run_anti_spoof_checks(image_bgr: np.ndarray) -> bool:
    """
    Main Anti-Spoof Gate — sabhi 4 checks run karta hai.

    Threshold: 3+ signals = SPOOF (pehle 2+ tha)
    Reason: Real person with shadow/bad lighting ek check fail kar sakta hai.
    Lekin ek real SCREEN 3-4 checks fail karegi kyunki uski poori profile alag hoti hai.

    Returns: True = Real Person ✅ | False = Spoof/Attack ❌
    """
    results = {
        "glare":        detect_glare(image_bgr),
        "moire":        detect_screen_moire(image_bgr),
        "flat_texture": detect_flat_texture(image_bgr),
        "color_flat":   detect_color_flatness(image_bgr),
    }

    spoof_signals = sum(results.values())
    logger.info(
        f"Anti-Spoof Results: {results} | "
        f"Spoof Signals: {spoof_signals}/4 | "
        f"Decision: {'SPOOF' if spoof_signals >= 3 else 'REAL'}"
    )

    # 3+ signals = definite screen/photo attack
    # 1-2 signals = could be bad lighting with a real person — allow
    if spoof_signals >= 3:
        triggered = [k for k, v in results.items() if v]
        logger.warning(
            f"SPOOF DETECTED! {spoof_signals}/4 signals triggered: {triggered}"
        )
        return False

    return True
