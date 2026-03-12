from __future__ import annotations

from app.db.base import TimestampMixin, Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)


class Team(Base, TimestampMixin):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    projects: Mapped[list[Project]] = relationship(
        back_populates="team", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Team id={self.id} name={self.name!r}>"


class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("team_id", "name", name="uq_project_team_name"),
        Index("ix_projects_team_id", "team_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))

    # Relationships
    team: Mapped[Team] = relationship(back_populates="projects")
    prompts: Mapped[list[Prompt]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    environments: Mapped[list[Environment]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r}>"


class Prompt(Base, TimestampMixin):
    __tablename__ = "prompts"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_prompt_project_name"),
        Index("ix_prompts_project_id", "project_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Points to the "live" version; nullable until first version is created
    head_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("prompt_versions.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )

    # Relationships
    project: Mapped[Project] = relationship(back_populates="prompts")
    versions: Mapped[list[PromptVersion]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
        foreign_keys="PromptVersion.prompt_id",
    )
    head_version: Mapped[PromptVersion | None] = relationship(
        foreign_keys=[head_version_id],
    )
    prompt_environments: Mapped[list[PromptEnvironment]] = relationship(
        back_populates="prompt", cascade="all, delete-orphan"
    )
    runs: Mapped[list[PromptRun]] = relationship(
        back_populates="prompt", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Prompt id={self.id} name={self.name!r} active={self.is_active}>"


class PromptVersion(Base, TimestampMixin):
    __tablename__ = "prompt_versions"
    __table_args__ = (
        UniqueConstraint("prompt_id", "version", name="uq_prompt_version"),
        Index("ix_prompt_versions_prompt_id", "prompt_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt_id: Mapped[int] = mapped_column(
        ForeignKey("prompts.id", ondelete="CASCADE", use_alter=True)
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # List of variable name strings, e.g. ["topic", "language"]
    variables: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    model_hint: Mapped[str | None] = mapped_column(String(80), nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    commit_message: Mapped[str | None] = mapped_column(String(250), nullable=True)

    # Relationships
    prompt: Mapped[Prompt] = relationship(
        back_populates="versions",
        foreign_keys=[prompt_id],
    )
    prompt_environments: Mapped[list[PromptEnvironment]] = relationship(
        back_populates="version"
    )
    runs: Mapped[list[PromptRun]] = relationship(back_populates="version")

    def __repr__(self) -> str:
        return f"<PromptVersion id={self.id} prompt_id={self.prompt_id} v={self.version}>"


class Environment(Base, TimestampMixin):
    __tablename__ = "environments"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_environment_project_name"),
        Index("ix_environments_project_id", "project_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    project: Mapped[Project] = relationship(back_populates="environments")
    prompt_environments: Mapped[list[PromptEnvironment]] = relationship(
        back_populates="environment", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Environment id={self.id} name={self.name!r} default={self.is_default}>"


class PromptEnvironment(Base, TimestampMixin):
    __tablename__ = "prompt_environments"
    __table_args__ = (
        UniqueConstraint("prompt_id", "environment_id", name="uq_prompt_env"),
        Index("ix_prompt_environments_environment_id", "environment_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"))
    environment_id: Mapped[int] = mapped_column(
        ForeignKey("environments.id", ondelete="CASCADE")
    )
    version_id: Mapped[int] = mapped_column(
        ForeignKey("prompt_versions.id", ondelete="RESTRICT")
    )

    # Relationships
    prompt: Mapped[Prompt] = relationship(back_populates="prompt_environments")
    environment: Mapped[Environment] = relationship(back_populates="prompt_environments")
    version: Mapped[PromptVersion] = relationship(back_populates="prompt_environments")

    def __repr__(self) -> str:
        return f"<PromptEnvironment prompt_id={self.prompt_id} env_id={self.environment_id} v={self.version_id}>"


class PromptRun(Base, TimestampMixin):
    __tablename__ = "prompt_runs"
    __table_args__ = (
        Index("ix_prompt_runs_prompt_id", "prompt_id"),
        Index("ix_prompt_runs_version_id", "version_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"))
    version_id: Mapped[int] = mapped_column(
        ForeignKey("prompt_versions.id", ondelete="RESTRICT")
    )
    # Raw inputs passed to the prompt (variable values)
    input: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Raw LLM output text
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    # "success" | "error" | "timeout"
    status: Mapped[str] = mapped_column(String(50), default="success", nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    prompt: Mapped[Prompt] = relationship(back_populates="runs")
    version: Mapped[PromptVersion] = relationship(back_populates="runs")

    def __repr__(self) -> str:
        return f"<PromptRun id={self.id} prompt_id={self.prompt_id} status={self.status!r}>"


# ---------------------------------------------------------------------------
# Backward-compatible aliases (old plural names → singular)
# Remove once all call-sites are updated.
# ---------------------------------------------------------------------------
Teams = Team
Projects = Project
