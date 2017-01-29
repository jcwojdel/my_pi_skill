import sys

from argparse import ArgumentParser
from tests import test_polish_radio
from lambdas import my_pi_lambda


def main(argv=None):
    parser = ArgumentParser()
    intent_names = [e['name'] for e in test_polish_radio.EVENTS]
    parser.add_argument('intent', help='Intent to be invoked, one of {}'.format(', '.join(intent_names)))
    args = parser.parse_args(argv)

    result = my_pi_lambda.lambda_handler(test_polish_radio.find_event_by_name(args.intent), None)

    print result

    return 0

if __name__ == "__main__":
    sys.exit(main())
