"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-29

"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('email', sa.String(120), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(128), nullable=False),
        sa.Column('nombre_completo', sa.String(120), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'clientes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nombre', sa.String(80), nullable=False),
        sa.Column('apellido', sa.String(80), nullable=False),
        sa.Column('cedula_ruc', sa.String(20), nullable=False, unique=True, index=True),
        sa.Column('telefono', sa.String(20), nullable=True),
        sa.Column('email', sa.String(120), nullable=True),
        sa.Column('direccion', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'vehiculos',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('cliente_id', sa.Integer(), sa.ForeignKey('clientes.id'), nullable=False, index=True),
        sa.Column('placa', sa.String(20), nullable=False, unique=True, index=True),
        sa.Column('marca', sa.String(60), nullable=False),
        sa.Column('modelo', sa.String(60), nullable=False),
        sa.Column('anio', sa.Integer(), nullable=True),
        sa.Column('color', sa.String(40), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'personal',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nombre', sa.String(80), nullable=False),
        sa.Column('apellido', sa.String(80), nullable=False),
        sa.Column('rol', sa.String(30), nullable=False),
        sa.Column('telefono', sa.String(20), nullable=True),
        sa.Column('email', sa.String(120), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'ordenes_trabajo',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('vehiculo_id', sa.Integer(), sa.ForeignKey('vehiculos.id'), nullable=False, index=True),
        sa.Column('creado_por_id', sa.Integer(), sa.ForeignKey('usuarios.id'), nullable=True),
        sa.Column('estado', sa.String(20), nullable=False, server_default='PERITAJE', index=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('descuento_porcentaje', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_cotizado', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_con_descuento', sa.Float(), nullable=False, server_default='0'),
        sa.Column('aprobado_por_cliente', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('fecha_aprobacion', sa.DateTime(), nullable=True),
        sa.Column('fecha_ingreso', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('fecha_estimada_entrega', sa.DateTime(), nullable=True),
        sa.Column('fecha_entrega_real', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'items_cotizacion',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('orden_id', sa.Integer(), sa.ForeignKey('ordenes_trabajo.id'), nullable=False, index=True),
        sa.Column('descripcion', sa.String(200), nullable=False),
        sa.Column('area_vehiculo', sa.String(100), nullable=False),
        sa.Column('precio_unitario', sa.Float(), nullable=False),
        sa.Column('cantidad', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('subtotal', sa.Float(), nullable=False),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'facturas',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('orden_id', sa.Integer(), sa.ForeignKey('ordenes_trabajo.id'), nullable=False, unique=True),
        sa.Column('numero_factura', sa.String(30), nullable=False, unique=True, index=True),
        sa.Column('fecha_emision', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('fecha_estimada_entrega', sa.DateTime(), nullable=True),
        sa.Column('monto_total', sa.Float(), nullable=False),
        sa.Column('monto_adelanto', sa.Float(), nullable=False),
        sa.Column('monto_saldo', sa.Float(), nullable=False),
        sa.Column('monto_pagado', sa.Float(), nullable=False, server_default='0'),
        sa.Column('estado', sa.String(20), nullable=False, server_default='PENDIENTE'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'pagos',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('factura_id', sa.Integer(), sa.ForeignKey('facturas.id'), nullable=False, index=True),
        sa.Column('registrado_por_id', sa.Integer(), sa.ForeignKey('usuarios.id'), nullable=True),
        sa.Column('monto', sa.Float(), nullable=False),
        sa.Column('tipo', sa.String(20), nullable=False),
        sa.Column('metodo', sa.String(20), nullable=False),
        sa.Column('referencia', sa.String(100), nullable=True),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'fases_trabajo',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('orden_id', sa.Integer(), sa.ForeignKey('ordenes_trabajo.id'), nullable=False, index=True),
        sa.Column('fase', sa.String(30), nullable=False),
        sa.Column('estado', sa.String(20), nullable=False, server_default='PENDIENTE'),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('fecha_inicio', sa.DateTime(), nullable=True),
        sa.Column('fecha_fin', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'asignaciones',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('fase_id', sa.Integer(), sa.ForeignKey('fases_trabajo.id'), nullable=False, index=True),
        sa.Column('personal_id', sa.Integer(), sa.ForeignKey('personal.id'), nullable=False, index=True),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('asignaciones')
    op.drop_table('fases_trabajo')
    op.drop_table('pagos')
    op.drop_table('facturas')
    op.drop_table('items_cotizacion')
    op.drop_table('ordenes_trabajo')
    op.drop_table('personal')
    op.drop_table('vehiculos')
    op.drop_table('clientes')
    op.drop_table('usuarios')
