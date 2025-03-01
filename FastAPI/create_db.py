from database import Base, engine

print("Creating database tables...")
Base.metadata.drop_all(bind=engine)  # Drop all existing tables
Base.metadata.create_all(bind=engine)  # Create new tables
print("Database tables created successfully!") 