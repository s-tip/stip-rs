#!/usr/bin/env python3

import sys
import argparse
from django.core.management.utils import get_random_secret_key
from decouple import AutoConfig, UndefinedValueError

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='setup .env Script')
    parser.add_argument('path', help='.env path')
    args = parser.parse_args()

    config = AutoConfig(args.path)
    try:
        secret_key = config('SECRET_KEY')
        print('SECRET_KEY has been already configured. (%s)' % (secret_key))
    except UndefinedValueError:
        secret_key = get_random_secret_key()
        with open(args.path, 'a') as fp:
            fp.write('SECRET_KEY=\'%s\'\n' % (secret_key))
        print('Set a SECRET_KEY value into .env (%s)' % (secret_key))

    sys.exit(0)
