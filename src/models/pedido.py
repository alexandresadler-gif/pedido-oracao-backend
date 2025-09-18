from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    nome_solicitante = db.Column(db.String(255), nullable=False)
    celular_solicitante = db.Column(db.String(20), nullable=True)
    email_solicitante = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Pendente')
    data_submissao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_ultima_atualizacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    visibilidade = db.Column(db.String(50), nullable=False, default='Todos')
    usuario_criador_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relacionamentos
    comentarios = db.relationship('Comentario', backref='pedido', lazy=True, cascade='all, delete-orphan')
    usuario_criador = db.relationship('User', backref='pedidos_criados', lazy=True)

    def __repr__(self):
        return f'<Pedido {self.titulo}>'

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'nome_solicitante': self.nome_solicitante,
            'celular_solicitante': self.celular_solicitante,
            'email_solicitante': self.email_solicitante,
            'status': self.status,
            'data_submissao': self.data_submissao.isoformat() if self.data_submissao else None,
            'data_ultima_atualizacao': self.data_ultima_atualizacao.isoformat() if self.data_ultima_atualizacao else None,
            'visibilidade': self.visibilidade,
            'usuario_criador_id': self.usuario_criador_id,
            'usuario_criador': self.usuario_criador.username if self.usuario_criador else None,
            'comentarios': [comentario.to_dict() for comentario in self.comentarios]
        }

class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    autor = db.Column(db.String(255), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_comentario = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relacionamento
    usuario = db.relationship('User', backref='comentarios', lazy=True)

    def __repr__(self):
        return f'<Comentario {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'pedido_id': self.pedido_id,
            'autor': self.autor,
            'conteudo': self.conteudo,
            'data_comentario': self.data_comentario.isoformat() if self.data_comentario else None,
            'usuario_id': self.usuario_id,
            'usuario': self.usuario.username if self.usuario else None
        }
