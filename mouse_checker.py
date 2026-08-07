import asyncio
import ctypes
from collections import deque
import flet as ft


try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # Fallback for older Windows builds
    except Exception:
        pass


def get_cursor_pos():
    """Helper function to get raw (x, y) mouse position on Windows."""

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def is_right_clicked():
    """Check if the right mouse button (VK_RBUTTON = 0x02) is currently pressed."""
    return (ctypes.windll.user32.GetAsyncKeyState(0x02) & 0x8000) != 0


async def main(page: ft.Page):
    page.title = "Mouse Tracker & Click Logger"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 350
    page.window.height = 500
    page.window.always_on_top = True

    # Store raw tuples (x, y) instead of formatted strings
    click_buffer = deque(maxlen=50)

    coord_text = ft.Text(
        "X: 0 | Y: 0",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.GREEN_ACCENT,
    )
    click_list = ft.ListView(expand=True, spacing=0, auto_scroll=False)

    page.add(
        ft.Column(
            [
                ft.Text(
                    "Current Cursor Position",
                    size=14,
                    color=ft.Colors.WHITE_70,
                ),
                coord_text,
                ft.Divider(color=ft.Colors.WHITE_24),
                ft.Text("Last 50 Clicks:", size=14, color=ft.Colors.WHITE_70),
                ft.Container(
                    content=click_list,
                    expand=True,
                    border=ft.border.Border(
                        top=ft.BorderSide(1, ft.Colors.WHITE_24),
                        right=ft.BorderSide(1, ft.Colors.WHITE_24),
                        bottom=ft.BorderSide(1, ft.Colors.WHITE_24),
                        left=ft.BorderSide(1, ft.Colors.WHITE_24),
                    ),
                    padding=10,
                    border_radius=5,
                    bgcolor=ft.Colors.BLACK_12,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )
    )

    async def copy_to_clipboard(x: int, y: int):
        """Copies coordinates formatted as [x, y] to clipboard and opens SnackBar."""
        copy_val = f"[{x}, {y}]"
        await ft.Clipboard().set(copy_val)
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(f"Copied: {copy_val}"),
                duration=1500,
                open=True,
            )
        )

    async def update_loop():
        """Non-blocking background loop for tracking mouse state."""
        was_clicked = False
        while True:
            try:
                x, y = get_cursor_pos()
                currently_clicked = is_right_clicked()

                if currently_clicked and not was_clicked:
                    click_buffer.append((x, y))

                    click_list.controls.clear()
                    for i, (cx, cy) in enumerate(reversed(click_buffer)):

                        # Bind current iteration's coordinates cleanly
                        async def handle_click(e, pos_x=cx, pos_y=cy):
                            await copy_to_clipboard(pos_x, pos_y)

                        click_list.controls.append(
                            ft.Row(
                                [
                                    ft.Text(
                                        f"{i}. X: {cx}, Y: {cy}",
                                        size=12,
                                        color=ft.Colors.WHITE,
                                        expand=True,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.COPY,
                                        icon_size=16,
                                        icon_color=ft.Colors.BLUE_400,
                                        tooltip="Copy [x, y]",
                                        on_click=handle_click,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            )
                        )

                    if click_list.page:
                        click_list.update()

                was_clicked = currently_clicked

                coord_text.value = f"X: {x} | Y: {y}"
                if coord_text.page:
                    coord_text.update()

            except Exception:
                pass

            await asyncio.sleep(0.02)

    page.run_task(update_loop)


if __name__ == "__main__":
    ft.run(main)