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
    test_map = {
        (ValueError, IndexError): (TestError1, True),
        ConnectionResetError: (TestError2, False)
    }
    test_dec_msg = "Some error occurred, oh no!"
    
    def exception_method():
        hi = "hi"
        return hi
    
    @exc.layer_error_handler(
        error_map=test_map,
        base_exception=DefaultError,
        exclude=TypeError
    )
    def test_decorator_single_exclude(self):
        self.exception_method()
        
    @exc.layer_error_handler(
        error_map=test_map,
        base_exception=DefaultError,
        exclude=(TypeError, AttributeError)
    )
    def test_decorator_multiple_exclude(self):
        self.exception_method()
        
    @exc.layer_error_handler(
        error_map=test_map, 
        base_exception=DefaultError, 
        message=test_dec_msg
    )
    def test_decorator_with_messsage(self):
        self.exception_method()
        
    def test_method2(self):
        try:
            self.exception_method()
        except Exception as e:
            exc.translate_error(
                e,
                self.test_map,
                DefaultError,
                self.__class__.__name__,
                "test_method1",
                f"Error occurred when executing test_method2: {e}",
                exclude=TypeError
            )
            

class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        self.test_class = TestClass()
    
    def testErrorHandlingDecoratorNoMessage(self):
        with patch.object(TestClass, "exception_method") as mock:
            # Test the translation of a tuple of exception types
            with self.assertRaises(TestError1):
                mock.side_effect = ValueError
                self.test_class.test_decorator_single_exclude()
                self.test_class.test_decorator_multiple_exclude()
                
                mock.side_effect = IndexError
                self.test_class.test_decorator_single_exclude()
                self.test_class.test_decorator_multiple_exclude()
                
            # Test the translation of a single exception type
            with self.assertRaises(TestError2):
                mock.side_effect = ConnectionResetError
                self.test_class.test_decorator_single_exclude()
                self.test_class.test_decorator_multiple_exclude()
                
            # Test translating to fallback exception
            with self.assertRaises(DefaultError):
                mock.side_effect = BufferError
                self.test_class.test_decorator_single_exclude()
                self.test_class.test_decorator_multiple_exclude()
                
            # Test ignoring a single exception type
            with self.assertRaises(TypeError):
                mock.side_effect = TypeError
                self.test_class.test_decorator_single_exclude()
                
            # Test ignoring multiple exception types
            with self.assertRaises(TypeError):
                mock.side_effect = TypeError
                self.test_class.test_decorator_multiple_exclude()
                
                mock.side_effect = AttributeError
                self.test_class.test_decorator_multiple_exclude()
                
    
    def testErrorHandlingDecoratorWithMessage(self):
        with patch.object(TestClass, "exception_method") as mock:
            mock.side_effect = BufferError
            # Test if the expected message is added to the tranlsated exception
            with self.assertRaises(DefaultError) as exp:
                self.test_class.test_decorator_with_messsage()
                self.assertEqual(self.test_class.test_dec_msg, exp.msg)
                
        