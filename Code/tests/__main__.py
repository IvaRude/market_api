from .complex_test import complex_test
from .unit_test import test_all
from .validation_tests import test_all_validators

if __name__ == '__main__':
    test_all()
    test_all_validators()
    complex_test()
    print('All tests passed.')
