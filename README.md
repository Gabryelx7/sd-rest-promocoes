# Sistema de Promoções v2 - REST, SSE e React

Este projeto é um sistema distribuído de microsserviços para gerenciar e promover promoções de produtos. **Esta versão expande a arquitetura RabbitMQ orientada a eventos da [versão anterior](https://github.com/Gabryelx7/sd-rabbitmq-promocoes).**

## Novos Recursos na v2

* **Gateway de API REST:** O microsserviço Gateway agora expõe uma API RESTful (construída com Flask) para lidar com solicitações do frontend e traduzi-las em eventos internos do RabbitMQ.

* **Notificações em Tempo Real (SSE):** Substituímos a consulta de clientes via terminal por Eventos Enviados pelo Servidor (SSE) usando Redis. Os clientes recebem notificações instantâneas no navegador para *hot-deals* e interesses em categorias específicas sem precisar atualizar a página.

* **Frontend Web React:** Um aplicativo de página única (SPA) responsivo, construído com Vite e React, que permite aos usuários visualizar promoções, votar, gerenciar interesses por categoria e receber alertas em tempo real.

* **E-mails Transacionais:** O microsserviço de Notificações agora se integra à **API Resend** externa para enviar e-mails automaticamente aos proprietários das lojas quando suas promoções forem aprovadas ou atingirem o limite de *hot-deal*.

* **Containerização Completa:** Toda a infraestrutura de backend (RabbitMQ, Redis, Gateway, serviços de Promoção, Ranking e Notificação) é totalmente conteinerizada para uma inicialização simples com um único comando.

---

## Arquitetura do Sistema

1. **Cluster de Backend (Containerizado):**

* `rabbitmq`: Broker de mensagens para eventos internos do domínio.
* `redis`: Backend Pub/Sub para os fluxos SSE.
* `ms-gateway`: Expõe a API REST e gerencia as conexões SSE.
* `ms-promocao`: Valida assinaturas e aprova promoções recebidas.
* `ms-ranking`: Contabiliza votos e ativa as ofertas *hot-deal*.
* `ms-notificacao`: Dispara e-mails via *Resend*.

2. **Frontend (Local):** Aplicativo React/Vite para interação com o consumidor.

3. **Cliente da Loja (Local):** Script CLI em Python simulando uma loja de terceiros que envia solicitações HTTP assinadas.

---

## Pré-requisitos

* **Docker** e **Docker Compose**
* **Node.js** (versão 18 ou superior recomendada)
* **Python 3.12** (para gerar chaves e executar o cliente do Store externo)
* Uma **Chave de API do Resend** (para notificações por e-mail)

---

## Como executar o projeto

### 1. Configurar chaves criptográficas

Antes de iniciar os contêineres, você deve gerar os pares de chaves Ed25519 para os microsserviços e o Store externo. Na raiz do projeto, execute:

```bash
python3 backend/utils/generate_key_pair.py
```

(Isso garante que o diretório backend/keys/ seja preenchido para que o Docker possa montá-lo).

### 2. Inicie a Infraestrutura de Backend

Exporte seu token da API Resend e o email utilizado para um arquivo `.env`.
``` Bash
RESEND_API_KEY=sua_chave
RESEND_EMAIL=seu_email@email.com
```

Em seguida, use o Docker Compose para construir e iniciar todo o cluster de microsserviços:
``` Bash
docker-compose up --build -d
```

(A API REST e o fluxo SSE agora estarão disponíveis em http://127.0.0.1:5000).

### 3. Inicie o Frontend React

Abra um novo terminal, navegue até o diretório frontend, instale as dependências e inicie o servidor de desenvolvimento Vite:

``` Bash
cd frontend
npm install
npm run dev
```

(Abra a URL local fornecida, geralmente http://localhost:5173, no seu navegador para acessar o Painel do Consumidor).

### 4. Simule um Envio para a Loja

Para ver o sistema em ação, simule uma loja de terceiros.

Na raiz do projeto, crie um ambiente virtual e instale a biblioteca `python-dotenv` (OPCIONAL: momento você for rodar os scripts localmente em algum momento, instale todas as dependências em `requirements.txt`)

``` Bash
python3 -m venv .venv
source .venv/bin/activate

pip install python-dotenv
# pip install -r backend/requirements.txt
```

Em seguida, execute o script do cliente da loja e siga as instruções para enviar uma promoção.

```Bash
python -m backend.loja
```

#### O que você verá:

1. O frontend exibirá instantaneamente uma notificação flutuante para a nova categoria.
2. A promoção aparecerá na interface do usuário.
3. Você receberá um e-mail de aprovação na sua caixa de entrada.
4. Ao votar na promoção na interface do usuário, você receberá um alerta do SSE e um segundo e-mail de parabéns!