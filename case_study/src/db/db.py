from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from src.db.base import Base, get_engine, get_session
from src.db.models import CampgroundORM
from src.logger import logger, DatabaseException, handle_exception
from src.config import DATABASE_URL

def init_db():
    def op():
        engine = get_engine()
        inspector = inspect(engine)
        if not inspector.has_table("campgrounds"):
            Base.metadata.create_all(engine)
            logger.info("Veritabanı başlatıldı ve tablolar oluşturuldu.")
        else:
            logger.info("Veritabanı zaten başlatılmış. Tablo oluşturma atlanıyor.")
        return True
    from src.utils.utils import retry_operation
    try:
        retry_operation(
            op,
            max_retries=5,
            initial_wait=3,
            backoff_factor=2,
            exception_types=(Exception,),
            context="init_db"
        )
    except Exception:
        raise DatabaseException("Birden fazla denemeden sonra veritabanına bağlanılamadı.")

def insert_campground_to_db(session, validated_campground):
    from src.utils.utils import sanitize_data
    try:
        db_data = CampgroundORM.prepare_data_for_db(validated_campground)
        db_data = sanitize_data(db_data)
        existing_campground = session.query(CampgroundORM).filter_by(id=db_data["id"]).first()
        if existing_campground:
            logger.info(f"Kamp alanı zaten mevcut. Kayıt güncelleniyor: {validated_campground.name}")
            for key, value in db_data.items():
                if hasattr(existing_campground, key):
                    setattr(existing_campground, key, value)
            logger.info(f"Kamp alanı başarıyla güncellendi: {validated_campground.name}")
        else:
            logger.info(f"Kamp alanı mevcut değil. Yeni kayıt ekleniyor: {validated_campground.name}")
            new_campground = CampgroundORM(**db_data)
            session.add(new_campground)
            logger.info(f"Yeni kamp alanı başarıyla eklendi: {validated_campground.name}")
        session.commit()
    except Exception as e:
        session.rollback()
        handle_exception(DatabaseException(str(e)), context=f"insert_campground_to_db: {validated_campground.name}")
