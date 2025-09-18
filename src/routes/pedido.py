from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.user import db
from src.models.pedido import Pedido, Comentario
from src.routes.auth import token_required, admin_required

pedido_bp = Blueprint('pedido', __name__)

# Listar todos os pedidos (requer autenticação)
@pedido_bp.route('/pedidos', methods=['GET'])
@token_required
def listar_pedidos(current_user):
    try:
        pedidos = Pedido.query.all()
        return jsonify([pedido.to_dict() for pedido in pedidos]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Obter um pedido específico (requer autenticação)
@pedido_bp.route('/pedidos/<int:pedido_id>', methods=['GET'])
@token_required
def obter_pedido(current_user, pedido_id):
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        return jsonify(pedido.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Criar um novo pedido (requer autenticação)
@pedido_bp.route('/pedidos', methods=['POST'])
@token_required
def criar_pedido(current_user):
    try:
        data = request.get_json()
        
        # Validação dos campos obrigatórios
        if not data.get('titulo') or not data.get('descricao') or not data.get('nome_solicitante'):
            return jsonify({'error': 'Título, descrição e nome do solicitante são obrigatórios'}), 400
        
        novo_pedido = Pedido(
            titulo=data['titulo'],
            descricao=data['descricao'],
            nome_solicitante=data['nome_solicitante'],
            celular_solicitante=data.get('celular_solicitante'),
            email_solicitante=data.get('email_solicitante'),
            status=data.get('status', 'Pendente'),
            visibilidade=data.get('visibilidade', 'Todos'),
            usuario_criador_id=current_user.id
        )
        
        db.session.add(novo_pedido)
        db.session.commit()
        
        return jsonify(novo_pedido.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Atualizar um pedido (requer autenticação e permissões adequadas)
@pedido_bp.route('/pedidos/<int:pedido_id>', methods=['PUT'])
@token_required
def atualizar_pedido(current_user, pedido_id):
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        data = request.get_json()
        
        # Verificar permissões: admin pode editar qualquer pedido, usuário comum só seus próprios
        if not current_user.is_admin and pedido.usuario_criador_id != current_user.id:
            return jsonify({'error': 'Você só pode editar seus próprios pedidos'}), 403
        
        # Atualizar campos se fornecidos
        if 'titulo' in data:
            pedido.titulo = data['titulo']
        if 'descricao' in data:
            pedido.descricao = data['descricao']
        if 'nome_solicitante' in data:
            pedido.nome_solicitante = data['nome_solicitante']
        if 'celular_solicitante' in data:
            pedido.celular_solicitante = data['celular_solicitante']
        if 'email_solicitante' in data:
            pedido.email_solicitante = data['email_solicitante']
        
        # Apenas admins podem alterar status e visibilidade
        if current_user.is_admin:
            if 'status' in data:
                pedido.status = data['status']
            if 'visibilidade' in data:
                pedido.visibilidade = data['visibilidade']
        
        pedido.data_ultima_atualizacao = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(pedido.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Excluir um pedido (requer autenticação e permissões adequadas)
@pedido_bp.route('/pedidos/<int:pedido_id>', methods=['DELETE'])
@token_required
def excluir_pedido(current_user, pedido_id):
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        
        # Verificar permissões: admin pode excluir qualquer pedido, usuário comum só seus próprios
        if not current_user.is_admin and pedido.usuario_criador_id != current_user.id:
            return jsonify({'error': 'Você só pode excluir seus próprios pedidos'}), 403
        
        db.session.delete(pedido)
        db.session.commit()
        
        return jsonify({'message': 'Pedido excluído com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Adicionar comentário a um pedido (requer autenticação)
@pedido_bp.route('/pedidos/<int:pedido_id>/comentarios', methods=['POST'])
@token_required
def adicionar_comentario(current_user, pedido_id):
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        data = request.get_json()
        
        if not data.get('conteudo'):
            return jsonify({'error': 'Conteúdo do comentário é obrigatório'}), 400
        
        novo_comentario = Comentario(
            pedido_id=pedido_id,
            autor=current_user.nome_completo or current_user.username,
            conteudo=data['conteudo'],
            usuario_id=current_user.id
        )
        
        # Atualizar data de última atualização do pedido
        pedido.data_ultima_atualizacao = datetime.utcnow()
        
        db.session.add(novo_comentario)
        db.session.commit()
        
        return jsonify(novo_comentario.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Obter comentários de um pedido (requer autenticação)
@pedido_bp.route('/pedidos/<int:pedido_id>/comentarios', methods=['GET'])
@token_required
def obter_comentarios(current_user, pedido_id):
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        comentarios = Comentario.query.filter_by(pedido_id=pedido_id).all()
        return jsonify([comentario.to_dict() for comentario in comentarios]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Obter estatísticas dos pedidos (requer autenticação)
@pedido_bp.route('/pedidos/estatisticas', methods=['GET'])
@token_required
def obter_estatisticas(current_user):
    try:
        total = Pedido.query.count()
        pendentes = Pedido.query.filter_by(status='Pendente').count()
        em_oracao = Pedido.query.filter_by(status='Em Oração').count()
        respondidos = Pedido.query.filter_by(status='Respondido').count()
        arquivados = Pedido.query.filter_by(status='Arquivado').count()
        
        estatisticas = {
            'total': total,
            'pendentes': pendentes,
            'em_oracao': em_oracao,
            'respondidos': respondidos,
            'arquivados': arquivados
        }
        
        return jsonify(estatisticas), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Buscar pedidos (requer autenticação)
@pedido_bp.route('/pedidos/buscar', methods=['GET'])
@token_required
def buscar_pedidos(current_user):
    try:
        termo = request.args.get('q', '')
        status = request.args.get('status', '')
        
        query = Pedido.query
        
        if termo:
            query = query.filter(
                db.or_(
                    Pedido.titulo.contains(termo),
                    Pedido.descricao.contains(termo),
                    Pedido.nome_solicitante.contains(termo)
                )
            )
        
        if status and status != 'todos':
            query = query.filter_by(status=status)
        
        pedidos = query.all()
        return jsonify([pedido.to_dict() for pedido in pedidos]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Atualizar apenas o status de um pedido (apenas admins)
@pedido_bp.route('/pedidos/<int:pedido_id>/status', methods=['PUT'])
@token_required
@admin_required
def atualizar_status(current_user, pedido_id):
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        data = request.get_json()
        
        if not data.get('status'):
            return jsonify({'error': 'Status é obrigatório'}), 400
        
        status_validos = ['Pendente', 'Em Oração', 'Respondido', 'Arquivado']
        if data['status'] not in status_validos:
            return jsonify({'error': 'Status inválido'}), 400
        
        pedido.status = data['status']
        pedido.data_ultima_atualizacao = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(pedido.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
