"""MediaPy launcher."""

import sys


def main() -> None:
    if "--selftest" in sys.argv[1:]:
        from mediapy.selftest import selftest

        sys.exit(selftest())

    from mediapy.gui import launch

    launch()


if __name__ == "__main__":
    main()
