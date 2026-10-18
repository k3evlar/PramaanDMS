"""Evidence schema v1: cases, members, documents, versions, stored objects, fingerprints,
verdicts and custody events (Phase 5).

Generated from the models with Alembic autogenerate, then reviewed. On PostgreSQL the
app role loses UPDATE and DELETE on rows that must never change after they are written:
custody events, document versions and stored objects (threats T14, T16, T46). Other
databases (SQLite in tests) skip that step.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-16
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.db import UTCDateTime

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('cases',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('case_number', sa.String(length=64), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('created_by', sa.String(length=64), nullable=False),
    sa.Column('created_at', UTCDateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cases')),
    sa.UniqueConstraint('case_number', name=op.f('uq_cases_case_number'))
    )
    op.create_table('storage_objects',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('bucket', sa.String(length=63), nullable=False),
    sa.Column('object_key', sa.String(length=512), nullable=False),
    sa.Column('version_id', sa.String(length=128), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('size_bytes', sa.BigInteger(), nullable=False),
    sa.Column('lock_mode', sa.String(length=16), nullable=False),
    sa.Column('retain_until', UTCDateTime(), nullable=False),
    sa.Column('created_at', UTCDateTime(), nullable=False),
    sa.CheckConstraint('length(sha256) = 64', name=op.f('ck_storage_objects_sha256_length')),
    sa.CheckConstraint('size_bytes > 0', name=op.f('ck_storage_objects_size_positive')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_storage_objects')),
    sa.UniqueConstraint('bucket', 'object_key', name='bucket_key')
    )
    op.create_table('case_members',
    sa.Column('case_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.String(length=64), nullable=False),
    sa.Column('role', sa.String(length=16), nullable=False),
    sa.Column('added_at', UTCDateTime(), nullable=False),
    sa.CheckConstraint("role IN ('IO', 'SUPERVISOR', 'CLERK', 'AUDITOR', 'ADMIN')", name=op.f('ck_case_members_role')),
    sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name=op.f('fk_case_members_case_id_cases')),
    sa.PrimaryKeyConstraint('case_id', 'user_id', name=op.f('pk_case_members'))
    )
    op.create_table('documents',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('case_id', sa.Uuid(), nullable=False),
    sa.Column('doc_type', sa.String(length=16), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('created_by', sa.String(length=64), nullable=False),
    sa.Column('created_at', UTCDateTime(), nullable=False),
    sa.CheckConstraint("doc_type IN ('FIR', 'STATEMENT', 'CHARGESHEET')", name=op.f('ck_documents_doc_type')),
    sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name=op.f('fk_documents_case_id_cases')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_documents'))
    )
    op.create_index(op.f('ix_documents_case_id'), 'documents', ['case_id'], unique=False)
    op.create_table('document_versions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('document_id', sa.Uuid(), nullable=False),
    sa.Column('version_no', sa.Integer(), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('size_bytes', sa.BigInteger(), nullable=False),
    sa.Column('media_type', sa.String(length=32), nullable=False),
    sa.Column('page_count', sa.Integer(), nullable=False),
    sa.Column('original_name', sa.String(length=255), nullable=False),
    sa.Column('reason', sa.String(length=500), nullable=True),
    sa.Column('storage_object_id', sa.Uuid(), nullable=False),
    sa.Column('uploaded_by', sa.String(length=64), nullable=False),
    sa.Column('uploaded_at', UTCDateTime(), nullable=False),
    sa.CheckConstraint("media_type IN ('application/pdf', 'image/png', 'image/jpeg', 'image/tiff')", name=op.f('ck_document_versions_media_type')),
    sa.CheckConstraint('length(sha256) = 64', name=op.f('ck_document_versions_sha256_length')),
    sa.CheckConstraint('version_no >= 1', name=op.f('ck_document_versions_version_positive')),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_document_versions_document_id_documents')),
    sa.ForeignKeyConstraint(['storage_object_id'], ['storage_objects.id'], name=op.f('fk_document_versions_storage_object_id_storage_objects')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_document_versions')),
    sa.UniqueConstraint('document_id', 'version_no', name='document_version'),
    sa.UniqueConstraint('storage_object_id', name=op.f('uq_document_versions_storage_object_id'))
    )
    op.create_index(op.f('ix_document_versions_document_id'), 'document_versions', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_versions_sha256'), 'document_versions', ['sha256'], unique=False)
    op.create_table('custody_events',
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), sa.Identity(always=False), nullable=False),
    sa.Column('event_type', sa.String(length=48), nullable=False),
    sa.Column('actor_id', sa.String(length=64), nullable=False),
    sa.Column('actor_role', sa.String(length=16), nullable=False),
    sa.Column('case_id', sa.Uuid(), nullable=True),
    sa.Column('document_id', sa.Uuid(), nullable=True),
    sa.Column('version_id', sa.Uuid(), nullable=True),
    sa.Column('request_id', sa.String(length=64), nullable=True),
    sa.Column('client_ip', sa.String(length=45), nullable=True),
    sa.Column('reason', sa.String(length=500), nullable=True),
    sa.Column('details', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
    sa.Column('occurred_at', UTCDateTime(), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name=op.f('fk_custody_events_case_id_cases')),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_custody_events_document_id_documents')),
    sa.ForeignKeyConstraint(['version_id'], ['document_versions.id'], name=op.f('fk_custody_events_version_id_document_versions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_custody_events'))
    )
    op.create_index(op.f('ix_custody_events_case_id'), 'custody_events', ['case_id'], unique=False)
    op.create_index(op.f('ix_custody_events_document_id'), 'custody_events', ['document_id'], unique=False)
    op.create_index(op.f('ix_custody_events_event_type'), 'custody_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_custody_events_occurred_at'), 'custody_events', ['occurred_at'], unique=False)
    op.create_table('fingerprints',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('document_version_id', sa.Uuid(), nullable=False),
    sa.Column('kind', sa.String(length=32), nullable=False),
    sa.Column('record', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
    sa.Column('created_at', UTCDateTime(), nullable=False),
    sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], name=op.f('fk_fingerprints_document_version_id_document_versions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fingerprints'))
    )
    op.create_index(op.f('ix_fingerprints_document_version_id'), 'fingerprints', ['document_version_id'], unique=False)
    op.create_table('verdicts',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('document_version_id', sa.Uuid(), nullable=False),
    sa.Column('candidate_sha256', sa.String(length=64), nullable=False),
    sa.Column('verdict', sa.String(length=16), nullable=False),
    sa.Column('severity', sa.String(length=8), nullable=False),
    sa.Column('record', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
    sa.Column('created_by', sa.String(length=64), nullable=False),
    sa.Column('created_at', UTCDateTime(), nullable=False),
    sa.CheckConstraint("(verdict = 'Tampered') = (severity <> 'None')", name=op.f('ck_verdicts_severity_matches_verdict')),
    sa.CheckConstraint("severity IN ('Major', 'Minor', 'None')", name=op.f('ck_verdicts_severity')),
    sa.CheckConstraint("verdict IN ('Identical', 'Equivalent', 'Tampered', 'Inconclusive', 'Not supported')", name=op.f('ck_verdicts_verdict')),
    sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], name=op.f('fk_verdicts_document_version_id_document_versions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_verdicts'))
    )
    op.create_index(op.f('ix_verdicts_document_version_id'), 'verdicts', ['document_version_id'], unique=False)

    if op.get_bind().dialect.name == "postgresql":
        # Append-only rows for the runtime role. The role is created by
        # docker/postgres/init/01-roles.sh; skip quietly if it does not exist.
        op.execute("""
            DO $$
            BEGIN
              IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'pramaan_app') THEN
                REVOKE UPDATE, DELETE, TRUNCATE ON custody_events, document_versions, storage_objects FROM pramaan_app;
              END IF;
            END $$;
        """)


def downgrade() -> None:
    op.drop_index(op.f('ix_verdicts_document_version_id'), table_name='verdicts')
    op.drop_table('verdicts')
    op.drop_index(op.f('ix_fingerprints_document_version_id'), table_name='fingerprints')
    op.drop_table('fingerprints')
    op.drop_index(op.f('ix_custody_events_occurred_at'), table_name='custody_events')
    op.drop_index(op.f('ix_custody_events_event_type'), table_name='custody_events')
    op.drop_index(op.f('ix_custody_events_document_id'), table_name='custody_events')
    op.drop_index(op.f('ix_custody_events_case_id'), table_name='custody_events')
    op.drop_table('custody_events')
    op.drop_index(op.f('ix_document_versions_sha256'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_document_id'), table_name='document_versions')
    op.drop_table('document_versions')
    op.drop_index(op.f('ix_documents_case_id'), table_name='documents')
    op.drop_table('documents')
    op.drop_table('case_members')
    op.drop_table('storage_objects')
    op.drop_table('cases')
