"""`python -m point_filter.gui` 用の起動入口。"""

from multiprocessing import freeze_support

from .main_window import main


if __name__ == "__main__":
    freeze_support()
    raise SystemExit(main())
