# 🤖 Bot de Divulgação - Sistema de Marketing Automático

Sistema completo de automação para marketing e atendimento comercial em múltiplas plataformas sociais.

## 📋 Características

- **Multi-plataforma**: Instagram, Facebook, Twitter/X, YouTube, WhatsApp
- **Dual-bot**: Marketing (publicações) + Comercial (atendimento)
- **Operação Semiautomática**: Aprovação humana em pontos críticos
- **Analytics Integrado**: Métricas em tempo real
- **Painel Web**: Gestão completa via interface gráfica

## 🚀 Quick Start

### Pré-requisitos

- Python 3.10+
- Docker & Docker Compose (opcional)
- Credenciais das APIs das redes sociais

### Instalação Local

```bash
# 1. Clonar repositório
git clone https://github.com/seu-usuario/bot-divulgacao.git
cd bot-divulgacao

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais

# 5. Inicializar banco de dados
python scripts/init_db.py

# 6. Iniciar API
uvicorn src.api.main:app --reload

# 7. Em outro terminal, iniciar dashboard
streamlit run src/dashboard/app.py
```

### Instalação com Docker

```bash
# 1. Configurar .env
cp .env.example .env
# Editar .env com suas credenciais

# 2. Iniciar todos os serviços
docker-compose up -d

# 3. Inicializar banco de dados
docker-compose exec api python scripts/init_db.py

# 4. Verificar logs
docker-compose logs -f
```

## 📦 Estrutura do Projeto

```
bot-divulgacao/
├── src/
│   ├── api/              # FastAPI endpoints
│   ├── bots/             # Lógica dos bots
│   ├── services/         # Serviços de negócio
│   ├── integrations/     # Adaptadores de APIs
│   ├── models/           # Models do banco
│   ├── utils/            # Utilitários
│   ├── dashboard/        # Interface Streamlit
│   └── scheduler/        # Tarefas agendadas
├── tests/                # Testes automatizados
├── docker/               # Dockerfiles
├── scripts/              # Scripts úteis
├── docs/                 # Documentação
└── logs/                 # Logs da aplicação
```

## 🔑 Configuração de APIs

### Instagram

1. Acesse [Facebook Developers](https://developers.facebook.com)
2. Crie um App e adicione Instagram Basic Display
3. Vincule sua conta Instagram Business
4. Gere token de longa duração
5. Adicione no `.env`:
   ```
   INSTAGRAM_ACCESS_TOKEN=seu_token
   INSTAGRAM_USER_ID=seu_user_id
   ```

### Facebook

1. No mesmo app do Facebook Developers
2. Adicione sua Página
3. Gere Page Access Token
4. Adicione no `.env`:
   ```
   FACEBOOK_PAGE_ACCESS_TOKEN=seu_token
   FACEBOOK_PAGE_ID=seu_page_id
   ```

### Twitter/X

1. Acesse [Twitter Developer Portal](https://developer.twitter.com)
2. Crie um App e gere credenciais
3. Adicione no `.env`:
   ```
   TWITTER_API_KEY=sua_key
   TWITTER_API_SECRET=seu_secret
   TWITTER_ACCESS_TOKEN=seu_token
   TWITTER_ACCESS_SECRET=seu_secret
   ```

### YouTube

1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie projeto e habilite YouTube Data API v3
3. Crie credenciais OAuth 2.0
4. Execute script de autenticação
5. Adicione no `.env`:
   ```
   YOUTUBE_CLIENT_ID=seu_client_id
   YOUTUBE_CLIENT_SECRET=seu_secret
   YOUTUBE_REFRESH_TOKEN=seu_token
   ```

### WhatsApp (Twilio)

1. Crie conta no [Twilio](https://www.twilio.com)
2. Ative WhatsApp no console
3. Adicione no `.env`:
   ```
   TWILIO_ACCOUNT_SID=seu_sid
   TWILIO_AUTH_TOKEN=seu_token
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   ```

## 🎯 Uso Básico

### 1. Agendar Publicação

```bash
# Via API
curl -X POST "http://localhost:8000/api/v1/posts" \
  -H "Authorization: Bearer sua_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "plataforma": "instagram",
    "tipo_conteudo": "image",
    "titulo": "Novo produto",
    "descricao": "Confira nosso novo smartphone! #tech",
    "scheduled_time": "2025-12-10T12:30:00Z"
  }'
```

Ou use o dashboard web em `http://localhost:8501`

### 2. Ver Métricas

Acesse o dashboard: `http://localhost:8501`

Ou via API:
```bash
curl "http://localhost:8000/api/v1/analytics/overview?period=week" \
  -H "Authorization: Bearer sua_api_key"
```

### 3. Capturar Lead (Webhook da LP)

```bash
curl -X POST "http://localhost:8000/api/v1/leads/capture" \
  -H "Authorization: Bearer sua_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva",
    "email": "joao@email.com",
    "phone": "+5511999999999",
    "source": "LP_ELETRONICOS"
  }'
```

## 📊 Endpoints da API

### Health Check
- `GET /health` - Status da API
- `GET /health/detailed` - Status detalhado

### Posts
- `GET /api/v1/posts` - Listar posts
- `POST /api/v1/posts` - Criar post
- `PUT /api/v1/posts/{uuid}/approve` - Aprovar post
- `DELETE /api/v1/posts/{uuid}` - Cancelar post

### Leads
- `GET /api/v1/leads` - Listar leads
- `POST /api/v1/leads/capture` - Capturar lead
- `GET /api/v1/leads/{uuid}` - Detalhes do lead

### Analytics
- `GET /api/v1/analytics/overview` - Visão geral
- `GET /api/v1/analytics/best-times` - Melhores horários
- `GET /api/v1/analytics/export` - Exportar relatório

Documentação completa: `http://localhost:8000/docs`

## 🛠️ Desenvolvimento

### Executar Testes

```bash
# Todos os testes
pytest

# Com coverage
pytest --cov=src tests/

# Apenas um módulo
pytest tests/unit/test_models.py
```

### Formatar Código

```bash
# Black (formatação)
black src/ tests/

# Flake8 (linter)
flake8 src/ tests/

# MyPy (type checking)
mypy src/
```

### Adicionar Nova Plataforma

1. Criar adaptador em `src/integrations/nova_plataforma.py`
2. Implementar interface base
3. Adicionar testes
4. Atualizar configurações
5. Documentar

## 📈 Monitoramento

### Logs

```bash
# Ver logs em tempo real
tail -f logs/$(date +%Y-%m-%d).log

# Logs de erro
grep ERROR logs/*.log

# Logs de uma plataforma específica
grep instagram logs/*.log
```

### Métricas

Acesse:
- Dashboard: `http://localhost:8501`
- Prometheus: `http://localhost:9090` (se configurado)
- Grafana: `http://localhost:3000` (se configurado)

## 🔒 Segurança

- **Nunca commite** credenciais (use `.env`)
- **Rate limiting** configurado automaticamente
- **Logs de auditoria** em `logs/audit.log`
- **Criptografia** de tokens sensíveis
- **CORS** configurado para origens específicas

## 🐛 Troubleshooting

### Posts não estão publicando

```bash
# Verificar scheduler
docker-compose logs scheduler

# Verificar fila de posts
python scripts/check_queue.py

# Testar conexão com API
python scripts/test_api_connection.py --platform instagram
```

### Leads não estão sendo capturados

```bash
# Testar webhook
curl -X POST http://localhost:8000/api/v1/leads/capture \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"name": "Teste"}'

# Verificar logs
docker-compose logs api | grep leads
```

## 📚 Documentação Adicional

- [Documentação Técnica Completa](docs/technical_documentation.md)
- [Guia de APIs](docs/api_reference.md)
- [Fluxos de Dados](docs/data_flows.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é privado e proprietário.

## 📞 Suporte

- Email: suporte@seudominio.com
- Slack: #bot-divulgacao
- Issues: GitHub Issues

## 🗺️ Roadmap

### Fase 1 (Atual) - MVP ✅
- [x] Estrutura base
- [x] Banco de dados
- [x] Configurações
- [ ] Integrações Instagram/Facebook
- [ ] API REST básica
- [ ] Dashboard básico

### Fase 2 - Bot Marketing
- [ ] Sistema de publicação
- [ ] Análise de horários
- [ ] Comentários automáticos

### Fase 3 - Bot Comercial
- [ ] Qualificação de leads
- [ ] Integração LP
- [ ] WhatsApp Business

### Fase 4 - Analytics
- [ ] Relatórios Excel
- [ ] Dashboard completo
- [ ] Alertas

### Fase 5 - Deploy
- [ ] Azure deployment
- [ ] CI/CD
- [ ] Monitoramento produção

---

**Versão**: 1.0.0  
**Última Atualização**: Dezembro 2025