"""Helpers for sizing Tk windows to the available display."""


def fit_window(window, width, height, min_width=480, min_height=360, margin=40):
    width = min(width, max(320, window.winfo_screenwidth() - margin))
    height = min(height, max(240, window.winfo_screenheight() - margin))

    def apply_size():
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        available_width = max(320, screen_width - margin)
        available_height = max(240, screen_height - margin)
        fitted_width = min(max(width, window.winfo_reqwidth()), available_width)
        fitted_height = min(max(height, window.winfo_reqheight()), available_height)
        window.minsize(min(min_width, fitted_width), min(min_height, fitted_height))
        window.geometry(f"{fitted_width}x{fitted_height}")

    window.after(50, apply_size)
    return width, height