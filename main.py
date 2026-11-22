import sys


def run_classic() -> None:
    from codequest.game import main

    main()


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        from codequest.selftest import run_self_test

        sys.exit(run_self_test())
    if "--classic" in sys.argv:
        run_classic()
        sys.exit(0)
    try:
        from codequest.web_app import main as run_web
    except ImportError:
        run_classic()
        sys.exit(0)
    try:
        run_web()
    except Exception:  # noqa: BLE001 - máy thiếu WebView2: mở giao diện pygame cũ thay thế
        run_classic()
