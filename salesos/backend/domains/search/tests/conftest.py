import os

os.environ.setdefault("SALESOS_TESTING", "true")
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("NEO4J_PASSWORD", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test")
