from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class ProjectEntity(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    # Ownership
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    owner = relationship("User", backref="projects")

    # The Graph Data (Nodes & Edges)
    graph_json = Column(JSON, default={}) 
    
    # Version Control
    compiler_version = Column(String, default="1.0.0")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())