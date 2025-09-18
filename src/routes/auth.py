from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
from src.models.user import db, User

auth_bp = Blueprint('auth', __name__)

# Chave secreta para JWT (em produção, deve ser uma variável de ambiente)
JWT_SECRET = 'sua-chave-secreta-jwt-muito-segura'

def token_required(f):
    """Decorator para verificar se o token JWT é válido"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token de acesso é obrigatório'}), 401
        
        try:
            # Remove 'Bearer ' do início do token
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'error': 'Token inválido'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator para verificar se o usuário é administrador"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'error': 'Acesso negado. Permissões de administrador necessárias.'}), 403
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registrar um novo usuário"""
    try:
        data = request.get_json()
        
        # Validação dos campos obrigatórios
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Nome de usuário, email e senha são obrigatórios'}), 400
        
        # Verificar se o usuário já existe
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Nome de usuário já existe'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email já está em uso'}), 400
        
        # Criar novo usuário
        hashed_password = generate_password_hash(data['password'])
        
        # O primeiro usuário registrado será automaticamente admin
        is_first_user = User.query.count() == 0
        
        novo_usuario = User(
            username=data['username'],
            email=data['email'],
            password_hash=hashed_password,
            nome_completo=data.get('nome_completo', ''),
            is_admin=is_first_user or data.get('is_admin', False)
        )
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário registrado com sucesso',
            'user': novo_usuario.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Fazer login e obter token JWT"""
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Nome de usuário e senha são obrigatórios'}), 400
        
        # Buscar usuário
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        # Gerar token JWT
        token_payload = {
            'user_id': user.id,
            'username': user.username,
            'is_admin': user.is_admin,
            'exp': datetime.utcnow() + timedelta(hours=24)  # Token válido por 24 horas
        }
        
        token = jwt.encode(token_payload, JWT_SECRET, algorithm='HS256')
        
        return jsonify({
            'message': 'Login realizado com sucesso',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify-token', methods=['GET'])
@token_required
def verify_token(current_user):
    """Verificar se o token é válido e retornar dados do usuário"""
    return jsonify({
        'valid': True,
        'user': current_user.to_dict()
    }), 200

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Obter perfil do usuário atual"""
    return jsonify(current_user.to_dict()), 200

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Atualizar perfil do usuário atual"""
    try:
        data = request.get_json()
        
        # Atualizar campos permitidos
        if 'nome_completo' in data:
            current_user.nome_completo = data['nome_completo']
        if 'email' in data:
            # Verificar se o email não está em uso por outro usuário
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != current_user.id:
                return jsonify({'error': 'Email já está em uso'}), 400
            current_user.email = data['email']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Perfil atualizado com sucesso',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """Alterar senha do usuário atual"""
    try:
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Senha atual e nova senha são obrigatórias'}), 400
        
        # Verificar senha atual
        if not check_password_hash(current_user.password_hash, data['current_password']):
            return jsonify({'error': 'Senha atual incorreta'}), 400
        
        # Atualizar senha
        current_user.password_hash = generate_password_hash(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Senha alterada com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def list_users(current_user):
    """Listar todos os usuários (apenas administradores)"""
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/users/<int:user_id>/admin', methods=['PUT'])
@token_required
@admin_required
def toggle_admin(current_user, user_id):
    """Alterar status de administrador de um usuário"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Não permitir que o usuário remova seu próprio status de admin
        if user.id == current_user.id:
            return jsonify({'error': 'Você não pode alterar seu próprio status de administrador'}), 400
        
        user.is_admin = not user.is_admin
        db.session.commit()
        
        return jsonify({
            'message': f'Status de administrador {"ativado" if user.is_admin else "desativado"} para {user.username}',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
