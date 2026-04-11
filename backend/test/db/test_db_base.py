import unittest

from sqlalchemy import String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from backend.database import db
from backend.src.db.db_core.models import Base
from backend.src.db.db_core.repository import BaseRepository
from backend.test.base_test_case import BaseTestCase


class TestModel(Base):
    __tablename__ = "testmodels"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    something: Mapped[str] = mapped_column(String(240), nullable=False)
    

class TestBaseDB(BaseTestCase):
            
    def setUp(self):
        TestModel.__table__.drop(bind=db.engine, checkfirst=True)
        TestModel.__table__.create(bind=db.engine, checkfirst=True)
        self.repo = BaseRepository(TestModel, db.session)
                
        # Make sure primary key is populated
        self.test = TestModel(**{"something": "nothing"})
        db.session.add(self.test)
        db.session.flush()
        
        
    def tearDown(self):
        db.session.rollback() # revert changes made from every test_method ran
        db.session.close()
        
        
    def testBaseModelInit(self):
        # ID is not initialized until added to session, this is fine
        self.assertEqual(1, self.test.id)
        self.assertEqual("nothing", self.test.something)
        
        
    def testBaseModelAsDict(self):
        self.assertDictEqual({"id": 1, "something": "nothing"}, self.test._asdict())
        
    def testBaseModelHash(self):
        new_instance = db.session.get(TestModel, 1)
        self.assertEqual(new_instance.__hash__(), self.test.__hash__())
        
    def testBaseModelEqual(self):
        # Other is self
        get_instance = db.session.get(TestModel, 1)
        self.assertEqual(get_instance, self.test)
        
        # Other is dict
        dict_instance = {"id": 1, "something": "nothing"}
        self.assertEqual(dict_instance, self.test)
        
        # Other is same type but different instance
        new_instance = TestModel(**dict_instance)
        self.assertEqual(new_instance, self.test)
        
        # Other is completely different
        self.assertNotEqual("j", self.test)
        
    def testBaseModelCopy(self):
        new_instance = self.test.copy()
        self.assertEqual(new_instance, self.test)
        
        

if __name__ == "__main__":
    unittest.main()