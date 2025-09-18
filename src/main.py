import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from src.models.user import db, User
from src.routes.user import user_bp
from src.routes.pedido import pedido_bp
from src.routes.auth import auth_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Configurar CORS para permitir requisições do frontend
# Configurar CORS para permitir requisições do frontend no Render
CORS(app, origins=[
    "http://localhost:5173",             # Para rodar local
    "http://127.0.0.1:5173",             # Alternativa local
    "https://pedido-oracao-frontend.onrender.com"  # Frontend hospedado no Render
], supports_credentials=True)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(pedido_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Importar todos os modelos para garantir que as tabelas sejam criadas
from src.models.pedido import Pedido, Comentario

with app.app_context():
    db.create_all()
    
    # Criar usuário administrador padrão se não existir
    if User.query.count() == 0:
        admin_user = User(
            username='admin',
            email='admin@sistema.com',
            password_hash=generate_password_hash('admin123'),
            nome_completo='Administrador do Sistema',
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Usuário administrador criado: admin / admin123")
    
    # Criar dados de exemplo se não existirem
    if Pedido.query.count() == 0:
        from datetime import datetime
        
        # Buscar o usuário admin para associar aos pedidos
        admin_user = User.query.filter_by(username='admin').first()
        
        pedido1 = Pedido(
            titulo='Saúde da família',
            descricao='Pedindo oração pela recuperação da minha mãe que está internada no hospital.',
            nome_solicitante='Maria Silva',
            celular_solicitante='(11) 99999-9999',
            email_solicitante='maria@email.com',
            status='Em Oração',
            data_submissao=datetime(2024, 1, 15),
            data_ultima_atualizacao=datetime(2024, 1, 16),
            usuario_criador_id=admin_user.id if admin_user else None
        )
        
        pedido2 = Pedido(
            titulo='Emprego',
            descricao='Preciso de oração para conseguir um novo emprego. Estou desempregado há 3 meses.',
            nome_solicitante='Carlos Santos',
            celular_solicitante='(11) 88888-8888',
            email_solicitante='carlos@email.com',
            status='Respondido',
            data_submissao=datetime(2024, 1, 10),
            data_ultima_atualizacao=datetime(2024, 1, 20),
            usuario_criador_id=admin_user.id if admin_user else None
        )
        
        db.session.add(pedido1)
        db.session.add(pedido2)
        db.session.commit()
        
        # Adicionar comentários de exemplo
        comentario1 = Comentario(
            pedido_id=pedido1.id,
            autor='Pastor João',
            conteudo='Estamos orando pela sua mãe. Deus é fiel!',
            data_comentario=datetime(2024, 1, 16),
            usuario_id=admin_user.id if admin_user else None
        )
        
        comentario2 = Comentario(
            pedido_id=pedido2.id,
            autor='Carlos Santos',
            conteudo='Glória a Deus! Consegui um emprego ontem. Obrigado pelas orações!',
            data_comentario=datetime(2024, 1, 20),
            usuario_id=admin_user.id if admin_user else None
        )
        
        db.session.add(comentario1)
        db.session.add(comentario2)
        db.session.commit()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
