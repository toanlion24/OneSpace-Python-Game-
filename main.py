import sys

from codequest.game import main

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        from codequest.selftest import run_self_test

        sys.exit(run_self_test())
    main()
