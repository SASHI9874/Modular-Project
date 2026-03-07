from sqlalchemy import Column, Integer, String, Enum as SqlEnum, JSON, UniqueConstraint, DateTime
from sqlalchemy.sql import func
from app.db.base_class import Base
from app.domain.feature.trust_level import FeatureTrustLevel

class FeatureEntity(Base):
    __tablename__ = "feature"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    version = Column(String, nullable=False)  # e.g., "1.0.0"
    
    # Metadata
    description = Column(String, nullable=True)
    author_id = Column(Integer, index=True) # ID of user who uploaded it
    
    # Security
    trust_level = Column(SqlEnum(FeatureTrustLevel), default=FeatureTrustLevel.USER, nullable=False)
    
    # The Code
    code_blob_ref = Column(String, nullable=False) # Path in MinIO (s3://bucket/features/name/v1.0.0.zip)
    requirements = Column(JSON, default=list)      # ["pandas==2.0", "numpy"]
    
    # Integration Contract
    inputs_json = Column(JSON, default=dict)       # {"pdf_path": "str"}
    outputs_json = Column(JSON, default=dict)      # {"text_content": "str"}

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Ensure (name + version) is unique
    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_feature_name_version'),
    )