from collections.abc import Iterable
from typing import Type
import unittest
from datetime import datetime
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session

import backend.src.global_core.exceptions as exc


class TestError1(exc.LayerError):
    default_message = "Test Error 1 Raised!"
    
class TestError2(exc.LayerError):
    default_message = "Test Error 2 Raised!"
    
class DefaultError(exc.LayerError):
    default_message = "Default Error Raised!"
    
class TestClass:
    # Initialize a test error map
    test_map = {
        (ValueError, IndexError): (TestError1, True),
        ConnectionResetError: (TestError2, False)
    }
    # Used for testing if custom message is applied
    test_dec_msg = "Some error occurred, oh no!"
    
    # Test method to patch
    def exception_method(self):
        hi = "hi"
        return hi


    def build_test_function(self, func: str, exclude = None, message = None):
        """
        Build and return a test function that wraps `exception_method` with either
        the `layer_error_handler` decorator or `translate_error` function.

        Args:
            func: The type of error handling to apply. Must be either "decorator"
                (uses `layer_error_handler`) or "translator" (uses `translate_error`).
            exclude: An exception type or tuple of exception types to pass through
                    without translation. Defaults to None.
            message: An optional custom error message to attach to raised exceptions.
                    Defaults to None.

        Returns:
            A callable function that invokes `exception_method` with the
            specified error handling applied.

        Raises:
            ValueError: If `func` is not "decorator" or "translator".
        """
        # Return a function that invokes 'exception_method' wrapped with the error handling decorator
        if func == "decorator":
            @exc.layer_error_handler(
                error_map=self.test_map,
                base_exception=DefaultError,
                exclude=exclude,
                message=message
            )
            def test_decorator(self=self):
                self.exception_method()
                
            return test_decorator
        
        # Return a function that invokes 'exception_method' wrapped with the error handling translator
        elif func == "translator":
            def test_translator(self=self):
                try:
                    self.exception_method()
                except Exception as e:
                    raise exc.translate_error(
                        e,
                        self.test_map,
                        DefaultError,
                        self.__class__.__name__,
                        message=message,
                        exclude=exclude
                    )
            
            return test_translator

        else:
            raise ValueError("Invalid function type!")


class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        self.test_class = TestClass()
        
    def check_functions(self, func: str):
        """
        Run a suite of error handling tests for a given function type.

        Patches `TestClass.exception_method` and verifies that exceptions are
        correctly translated, passed through, or attached with a custom message,
        depending on the error map and exclude/message settings.

        Specifically tests:
            - Tuple-mapped exceptions `(ValueError, IndexError)` raise `TestError1`
            - Single-mapped exceptions (`ConnectionResetError`) raise `TestError2`
            - Unmapped exceptions (`BufferError`) raise the `DefaultError` fallback
            - A single excluded exception type is passed through untranslated
            - Multiple excluded exception types are each passed through untranslated
            - A custom message is attached to the raised exception

        Args:
            func: The function type to test, passed to `build_test_function`.
                  Must be "decorator" or "translator".
        """
        
        with patch.object(TestClass, "exception_method") as mock:
            test_func = self.test_class.build_test_function(func)
            
            # Test the translation of a tuple of exception types
            with self.assertRaises(TestError1):
                mock.side_effect = ValueError
                test_func()

            with self.assertRaises(TestError1):
                mock.side_effect = IndexError
                test_func()
                
            # Test the translation of a single exception type
            with self.assertRaises(TestError2):
                mock.side_effect = ConnectionResetError
                test_func()
                
            # Test translating to fallback exception
            with self.assertRaises(DefaultError):
                mock.side_effect = BufferError
                test_func()
                
            # Test ignoring a single exception type
            with self.assertRaises(IndexError):
                mock.side_effect = IndexError
                test_single = self.test_class.build_test_function(func, exclude=IndexError)
                test_single()
            
            # Test ignoring multiple exception types
            test_multiple = self.test_class.build_test_function(func, exclude=(IndexError, AttributeError))
            with self.assertRaises(IndexError):
                mock.side_effect = IndexError
                test_multiple()
                
            with self.assertRaises(AttributeError):
                mock.side_effect = AttributeError
                test_multiple()
                
            # Test with message
            test_message = self.test_class.build_test_function(func, message=self.test_class.test_dec_msg)
            with self.assertRaises(DefaultError) as exp:
                mock.side_effect = BufferError
                test_message()
                self.assertEqual(self.test_class.test_dec_msg, exp.msg)
                
    
    def testErrorHandlingDecorator(self):
        self.check_functions("decorator")
    
    
    def testErrorHandlingTranslator(self):
        self.check_functions("translator")
        
        