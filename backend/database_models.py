"""
SQLAlchemy models for Legacy Interview App
Optimized for fast retrieval and RAG capabilities
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Project(Base):
    """Core interview project model"""
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    subject_name = Column(String(255), nullable=False)
    subject_age = Column(Integer)
    relation = Column(String(100), nullable=False)
    background = Column(Text)
    interview_mode = Column(String(20), nullable=False)
    language = Column(String(10), nullable=False, default='en')
    status = Column(String(50), nullable=False, default='created')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    extra_metadata = Column(JSONB, default={})
    
    # Relationships
    responses = relationship("InterviewResponse", back_populates="project", cascade="all, delete-orphan")
    themes = relationship("InterviewTheme", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("KnowledgeDocument", back_populates="project", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'name': self.name,
            'subject_info': {
                'name': self.subject_name,
                'age': self.subject_age,
                'relation': self.relation,
                'background': self.background,
                'language': self.language
            },
            'interview_mode': self.interview_mode,
            'language': self.language,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'themes': [theme.to_dict() for theme in self.themes],
            'responses': [resp.to_dict() for resp in self.responses],
            'metadata': self.extra_metadata
        }

class InterviewResponse(Base):
    """Individual interview response model"""
    __tablename__ = "interview_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False, default='seed')
    theme_id = Column(UUID(as_uuid=True), ForeignKey('interview_themes.id'))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    followup_questions = Column(JSONB, default=[])
    extra_metadata = Column(JSONB, default={})
    
    # Relationships
    project = relationship("Project", back_populates="responses")
    theme = relationship("InterviewTheme", back_populates="responses")
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'project_id': str(self.project_id),
            'question': self.question,
            'answer': self.answer,
            'question_type': self.question_type,
            'theme_id': str(self.theme_id) if self.theme_id else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'followup_questions': self.followup_questions,
            'metadata': self.extra_metadata
        }

class InterviewTheme(Base):
    """Interview theme model"""
    __tablename__ = "interview_themes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    questions = Column(JSONB, default=[])
    suggested_interviewer = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    extra_metadata = Column(JSONB, default={})
    
    # Relationships
    project = relationship("Project", back_populates="themes")
    responses = relationship("InterviewResponse", back_populates="theme")
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'project_id': str(self.project_id),
            'name': self.name,
            'description': self.description,
            'questions': self.questions,
            'suggested_interviewer': self.suggested_interviewer,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.extra_metadata
        }

class KnowledgeDocument(Base):
    """Knowledge document for RAG capabilities"""
    __tablename__ = "knowledge_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'))
    title = Column(String(500))
    content = Column(Text, nullable=False)
    source_type = Column(String(50), nullable=False, default='interview')
    source_url = Column(Text)
    extra_metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="documents")
    embeddings = relationship("DocumentEmbedding", back_populates="document", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'project_id': str(self.project_id) if self.project_id else None,
            'title': self.title,
            'content': self.content,
            'source_type': self.source_type,
            'source_url': self.source_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.extra_metadata
        }

class DocumentEmbedding(Base):
    """Vector embeddings for semantic search"""
    __tablename__ = "document_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('knowledge_documents.id', ondelete='CASCADE'), nullable=False)
    chunk_index = Column(Integer, nullable=False, default=0)
    content = Column(Text, nullable=False)
    embedding = Column('embedding', String)  # Will be handled by pgvector
    extra_metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("KnowledgeDocument", back_populates="embeddings")
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'chunk_index': self.chunk_index,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.extra_metadata
        }
