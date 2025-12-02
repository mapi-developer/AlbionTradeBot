import ctypes
from typing import Optional, Tuple, List

import win32gui
import win32ui
import win32con
import win32api
import win32process

import numpy as np
import cv2 as cv
from PIL import Image
import pytesseract

from pathlib import Path
import time


class WindowCapture:
    hwnd: int
    width: int
    height: int
    debugging: bool
    

    def __init__(self, window_name: str, base_dir: Optional[str] = "", debugging=False):
        self.BASE_DIR = base_dir
        self.debugging = debugging
        ctypes.windll.user32.SetProcessDPIAware()

        self.hwnd = win32gui.FindWindow(None, window_name)
        if not self.hwnd:
            raise RuntimeError(f"Window not found: {window_name}")

        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        self.width = int(right - left)
        self.height = int(bottom - top)

    def _capture_np_bgra(self) -> Optional[np.ndarray]:
        hwndDC = mfcDC = saveDC = saveBitMap = None
        try:
            hwndDC = win32gui.GetWindowDC(self.hwnd)
            if not hwndDC:
                return None

            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, self.width, self.height)
            saveDC.SelectObject(saveBitMap)

            PW_RENDERFULLCONTENT = 0x00000002
            result = ctypes.windll.user32.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), PW_RENDERFULLCONTENT)

            if result != 1:
                SRCCOPY = 0x00CC0020
                saveDC.BitBlt((0, 0), (self.width, self.height), mfcDC, (0, 0), SRCCOPY)

            bmpinfo = saveBitMap.GetInfo()
            bmpbytes = saveBitMap.GetBitmapBits(True)

            w = bmpinfo["bmWidth"]
            h = bmpinfo["bmHeight"]
            arr = np.frombuffer(bmpbytes, dtype=np.uint8)
            try:
                arr = arr.reshape((h, w, 4))
            except ValueError:
                return None

            return arr

        finally:
            try:
                if saveBitMap:
                    win32gui.DeleteObject(saveBitMap.GetHandle())
            except Exception:
                pass
            try:
                if saveDC:
                    saveDC.DeleteDC()
            except Exception:
                pass
            try:
                if mfcDC:
                    mfcDC.DeleteDC()
            except Exception:
                pass
            try:
                if hwndDC:
                    win32gui.ReleaseDC(self.hwnd, hwndDC)
            except Exception:
                pass

    @staticmethod
    def _bgra_to_pil_rgb(bgra: np.ndarray) -> Image.Image:
        """Convert BGRA ndarray -> PIL RGB Image (drops alpha)."""
        rgb = cv.cvtColor(bgra, cv.COLOR_BGRA2RGB)
        return Image.fromarray(rgb)

    @staticmethod
    def _pil_to_cv_bgr(pil_img: Image.Image) -> np.ndarray:
        """PIL RGB -> OpenCV BGR ndarray."""
        rgb = np.array(pil_img, copy=False)
        return cv.cvtColor(rgb, cv.COLOR_RGB2BGR)

    def get_screenshot(
        self,
        x_0_crop: Optional[int] = None,
        y_0_crop: Optional[int] = None,
        x_1_crop: Optional[int] = None,
        y_1_crop: Optional[int] = None,
    ) -> Optional[Image.Image]:
        bgra = self._capture_np_bgra()
        if bgra is None:
            return None

        pil_img = self._bgra_to_pil_rgb(bgra)

        if x_0_crop is None:
            if self.debugging == True:
                self._safe_imwrite(self.BASE_DIR, pil_img)
            return pil_img

        x0, y0, x1, y1 = int(x_0_crop), int(y_0_crop), int(x_1_crop), int(y_1_crop)
        x0 = max(0, min(x0, self.width))
        x1 = max(0, min(x1, self.width))
        y0 = max(0, min(y0, self.height))
        y1 = max(0, min(y1, self.height))
        if x1 <= x0 or y1 <= y0:
            return None

        if self.debugging == True:
            self._safe_imwrite(self.BASE_DIR, pil_img.crop((x0, y0, x1, y1)))

        return pil_img.crop((x0, y0, x1, y1))

    def get_text_from_screenshot(
        self,
        crop_screenshot_positions: Tuple[int, int, int, int],
        is_gray_reading: bool = True,
        lowercase: bool = True,
        tesseract_config: str = "--psm 6",
    ) -> str:
        pil_img = self.get_screenshot(*crop_screenshot_positions)
        if pil_img is None:
            return ""

        if is_gray_reading:
            cv_img = self._pil_to_cv_bgr(pil_img)
            gray = cv.cvtColor(cv_img, cv.COLOR_BGR2GRAY)
            _, bw = cv.threshold(gray, 0, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)
            
            if self.debugging:
                self._safe_imwrite(self.BASE_DIR, bw)

            text = pytesseract.image_to_string(bw, config=tesseract_config)
        else:
            text = pytesseract.image_to_string(pil_img, config={tesseract_config})

        text = text.rstrip("\n")
        return text.lower() if lowercase else text

    def get_text_screen_position(
        self,
        target_text: str,
        is_gray_reading: bool = True,
        search_region: Optional[Tuple[int, int, int, int]] = None,
        position_offset: Tuple[int, int] = (10, 10),
        tesseract_config: str = "--psm 6",
        gate_left_gt: Optional[int] = 2200,
        gate_top_lt: Optional[int] = 400,
    ) -> List[int]:
        x, y = 0, 0
        if search_region:
            pil_img = self.get_screenshot(*search_region)
        else:
            pil_img = self.get_screenshot()

        if pil_img is None:
            return [x, y]

        cv_img = self._pil_to_cv_bgr(pil_img)
        data_src = cv_img

        if is_gray_reading:
            gray = cv.cvtColor(cv_img, cv.COLOR_BGR2GRAY)
            _, data_src = cv.threshold(gray, 0, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)

        if self.debugging:
            self._safe_imwrite(self.BASE_DIR, cv_img)

        text_data = pytesseract.image_to_data(
            data_src, output_type=pytesseract.Output.DICT, config=tesseract_config
        )

        if not text_data or "text" not in text_data:
            return [x, y]

        x_offset = search_region[0] if search_region else 0
        y_offset = search_region[1] if search_region else 0

        t_lower = target_text.lower()
        for i, word in enumerate(text_data.get("text", [])):
            if not word:
                continue
            if t_lower in word.lower():
                left = int(text_data["left"][i]) + x_offset
                top = int(text_data["top"][i]) + y_offset

                if (gate_left_gt is None or left > gate_left_gt) and (gate_top_lt is None or top < gate_top_lt):
                    x = left + position_offset[0]
                    y = top + position_offset[1]
                    break

        return [x, y]

    def get_window_resolution(self) -> str:
        return f"{self.width}x{self.height}"

    def get_window(self) -> int:
        return self.hwnd

    def set_foreground_window(self, max_wait_seconds=5) -> None:
        """Repeatedly tries to set the window to the foreground for a specified duration."""
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            if self.is_foreground_window():
                return  # Success

            try:
                # Standard method to bring window to front
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(self.hwnd)
            except win32gui.error:
                # Fallback for when the above fails, often due to focus issues
                try:
                    fg_hwnd = win32gui.GetForegroundWindow()
                    cur_tid = win32api.GetCurrentThreadId()
                    fg_tid = win32process.GetWindowThreadProcessId(fg_hwnd)[0]
                    ctypes.windll.user32.AttachThreadInput(cur_tid, fg_tid, True)
                    win32gui.SetForegroundWindow(self.hwnd)
                    ctypes.windll.user32.AttachThreadInput(cur_tid, fg_tid, False)
                except Exception:
                    pass  # Ignore errors in the fallback
            time.sleep(0.5) # Wait before next attempt

    def is_foreground_window(self) -> bool:
        """Checks if the captured window is currently the foreground window."""
        return win32gui.GetForegroundWindow() == self.hwnd

    @staticmethod
    def _safe_imwrite(path: str, img) -> bool:
        # Normalize and ensure folder exists
        p = Path(path+"/debug_image")
        if p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}:
            # default to .png if missing/bad extension
            p = p.with_suffix(".png")
        if p.parent and not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)

        import numpy as np
        if not isinstance(img, np.ndarray):
            try:
                from PIL import Image
                if isinstance(img, Image.Image):
                    img = np.array(img)
                else:
                    raise TypeError("Unsupported image type for imwrite")
            except Exception as e:
                raise TypeError(f"Unsupported image type for imwrite: {type(img)}") from e

        if img.dtype != np.uint8:
            img = img.astype(np.uint8, copy=False)
        if not img.flags["C_CONTIGUOUS"]:
            img = np.ascontiguousarray(img)

        ok = cv.imwrite(str(p), img)
        if not ok:
            raise IOError(
                f"cv.imwrite failed for '{p}'. "
                "Check write permissions and that the image has a valid shape "
                "(HxW, HxWx3/BGR, or HxWx4/BGRA) and dtype=uint8."
            )
        return True