# 🏦 Banco Ágil - Sistema de Atendimento com Agentes de IA

Sistema multi-agente para atendimento bancário digital desenvolvido com LangChain, LangGraph, Gemini API e Streamlit.

## 📋 Visão Geral

O Banco Ágil é um sistema de atendimento automatizado que utiliza múltiplos agentes especializados de IA para oferecer serviços bancários como:

* Autenticação de clientes
* Consulta e aumento de limite de crédito
* Entrevista de crédito para recálculo de score
* Cotação de moedas em tempo real

## 🏗️ Arquitetura do Sistema

### Agentes Implementados

1. **Agente de Triagem**
   * Porta de entrada do sistema
   * Autentica clientes via CPF e data de nascimento
   * Identifica a necessidade e redireciona para agente especializado
   * Implementa sistema de tentativas (máximo 3)
2. **Agente de Crédito**
   * Consulta limite de crédito atual
   * Processa solicitações de aumento
   * Valida solicitações contra tabela de score
   * Oferece entrevista de crédito em caso de rejeição
3. **Agente de Entrevista de Crédito**
   * Conduz entrevista estruturada
   * Coleta dados financeiros (renda, emprego, despesas, dependentes, dívidas)
   * Calcula novo score usando fórmula ponderada
   * Atualiza base de dados do cliente
4. **Agente de Câmbio**
   * Consulta cotações em tempo real via API Tavily
   * Suporta múltiplas moedas (dólar, euro, libra, etc)
   * Apresenta informações atualizadas do mercado

### Fluxo de Dados

```
Usuário → Streamlit UI → Sistema de Agentes → LLM (Gemini) → Resposta
                              ↓
                    Armazenamento CSV
                    - clientes.csv
                    - score_limite.csv
                    - solicitacoes_aumento_limite.csv
```

### Tecnologias Utilizadas

* **Python 3.8+** : Linguagem principal
* **Streamlit** : Interface web interativa
* **LangChain** : Framework para construção de aplicações com LLMs
* **Google Gemini API** : Modelo de linguagem
* **Tavily API** : Busca em tempo real para cotações
* **Pandas** : Manipulação de dados CSV

## ✨ Funcionalidades Implementadas

### ✅ Requisitos Obrigatórios

* [X] Sistema multi-agente com escopo definido
* [X] Agente de Triagem com autenticação
* [X] Agente de Crédito (consulta e aumento)
* [X] Agente de Entrevista de Crédito
* [X] Agente de Câmbio
* [X] Persistência em CSV
* [X] Validação de score e limites
* [X] Sistema de tentativas de autenticação
* [X] Cálculo de score com fórmula ponderada
* [X] Interface Streamlit
* [X] Tratamento de erros

### 🎯 Diferenciais

* Interface limpa e intuitiva
* Feedback visual do agente atual
* Histórico de conversa persistente
* Transições suaves entre agentes
* Validação robusta de dados
* Mensagens contextualizadas

## 🚀 Como Executar

### 1. Pré-requisitos

* Python 3.8 ou superior
* Chaves de API:
  * Google Gemini API ([obtenha aqui](https://makersuite.google.com/app/apikey))
  * Tavily API ([obtenha aqui](https://tavily.com/))

### 2. Instalação

```bash
# Clone o repositório
git clone <seu-repositorio>
cd banco-agil

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configuração

Crie um arquivo `.env` na raiz do projeto:

```bash
GOOGLE_API_KEY=sua_chave_gemini_aqui
TAVILY_API_KEY=sua_chave_tavily_aqui
```

### 4. Executar a Aplicação

```bash
streamlit run app.py
```

A aplicação abrirá automaticamente no navegador em `http://localhost:8501`

## 🧪 Como Testar

### CPFs de Teste Disponíveis

Use os seguintes CPFs para testar o sistema:

| CPF         | Data de Nascimento | Nome         | Limite    | Score |
| ----------- | ------------------ | ------------ | --------- | ----- |
| 12345678901 | 15/05/1990         | João Silva  | R$ 5.000  | 650   |
| 98765432100 | 22/08/1985         | Maria Santos | R$ 8.000  | 750   |
| 11122233344 | 10/03/1992         | Pedro Costa  | R$ 3.000  | 550   |
| 55566677788 | 30/11/1988         | Ana Oliveira | R$ 10.000 | 850   |

### Fluxo de Teste Completo

1. **Teste de Autenticação**
   * CPF: 12345678901
   * Data: 15/05/1990
   * ✅ Deve autenticar com sucesso
2. **Teste de Consulta de Crédito**
   * Após autenticar, diga: "quero consultar meu limite"
   * ✅ Deve mostrar limite atual
3. **Teste de Aumento Aprovado**
   * Solicite aumento para R$ 6.000
   * ✅ Deve aprovar (score 650 permite até R$ 7.000)
4. **Teste de Aumento Rejeitado**
   * Use CPF 11122233344 (score 550)
   * Solicite aumento para R$ 8.000
   * ✅ Deve rejeitar e oferecer entrevista
5. **Teste de Entrevista de Crédito**
   * Aceite a entrevista
   * Responda as perguntas
   * ✅ Deve calcular novo score
6. **Teste de Câmbio**
   * Após autenticar, diga: "quero ver cotação do dólar"
   * ✅ Deve buscar e exibir cotação atual
7. **Teste de Falha de Autenticação**
   * Use CPF 12345678901 com data errada
   * Tente 3 vezes
   * ✅ Deve encerrar após 3 tentativas

## 🎯 Desafios Enfrentados e Soluções

### 1. **Gerenciamento de Estado Entre Agentes**

 **Desafio** : Manter contexto consistente durante transições entre agentes.

 **Solução** : Implementei um dicionário de contexto centralizado no `BancoAgilSystem` que persiste informações críticas (CPF, dados do cliente, etapa da entrevista) e é acessível por todos os agentes.

### 2. **Extração de Informações das Mensagens do Usuário**

 **Desafio** : Usuários digitam CPF e datas em formatos variados.

 **Solução** : Usei regex patterns flexíveis que aceitam múltiplos formatos (com/sem pontuação, diferentes separadores) e normalizei para formato padrão.

### 3. **Transições Suaves Entre Agentes**

 **Desafio** : Fazer transições imperceptíveis para o usuário.

 **Solução** : Implementei mensagens contextualizadas que mantêm continuidade narrativa, sem mencionar "mudança de agente" explicitamente.

### 4. **Integração com APIs Externas (Tavily)**

 **Desafio** : Extrair informação precisa de resultados de busca não estruturados.

 **Solução** : Combinei busca Tavily + processamento com LLM, onde o Gemini extrai e formata a cotação dos resultados brutos.

### 5. **Validação de Score vs Limite**

 **Desafio** : Verificar se solicitação é permitida baseado em tabela de faixas.

 **Solução** : Implementei lógica de busca em DataFrame pandas que mapeia score atual para limite máximo permitido.

## 💡 Escolhas Técnicas e Justificativas

### Por que Gemini API?

* ✅ Tier gratuito generoso
* ✅ Boa performance em português
* ✅ Baixa latência
* ✅ Integração simples via LangChain

### Por que CSV em vez de Banco de Dados?

* ✅ Simplicidade para POC
* ✅ Fácil visualização e debug
* ✅ Sem setup adicional
* ✅ Suficiente para demonstração
* ⚠️  **Para produção** : recomenda-se PostgreSQL ou MongoDB

### Por que Não Usei LangGraph Explicitamente?

Optei por uma abordagem mais direta com máquina de estados simples porque:

* ✅ Fluxo linear bem definido
* ✅ Poucos estados possíveis
* ✅ Código mais legível para revisão
* ✅ Mais fácil de debugar

Para sistemas mais complexos com múltiplos caminhos paralelos, LangGraph seria mais apropriado.

### Estrutura de Código

* `app.py`: Interface Streamlit (separação UI/lógica)
* `agents.py`: Toda lógica de negócio centralizada
* CSVs: Dados persistentes
* Benefícios: manutenção fácil, código testável, responsabilidades claras

## 📁 Estrutura de Arquivos

```
banco-agil/
│
├── app.py                              # Interface Streamlit
├── agents.py                           # Sistema de agentes
├── requirements.txt                    # Dependências
├── .env                               # Variáveis de ambiente (não versionado)
├── .env.example                       # Exemplo de configuração
│
├── clientes.csv                        # Base de clientes
├── score_limite.csv                    # Tabela score x limite
├── solicitacoes_aumento_limite.csv    # Log de solicitações (gerado)
│
└── README.md                           # Este arquivo
```

## 🔒 Segurança

⚠️  **IMPORTANTE** : Este é um projeto de demonstração. Em produção:

* [ ] Nunca armazene senhas em texto plano
* [ ] Use banco de dados seguro com criptografia
* [ ] Implemente autenticação JWT
* [ ] Adicione rate limiting
* [ ] Use HTTPS
* [ ] Valide e sanitize todos os inputs
* [ ] Implemente logs de auditoria

## 🐛 Tratamento de Erros

O sistema implementa tratamento de erros para:

* ✅ Arquivo CSV não encontrado
* ✅ Formato de data inválido
* ✅ CPF inválido
* ✅ API indisponível
* ✅ Valores numéricos inválidos
* ✅ Falhas na busca de cotação

## 🚧 Melhorias Futuras

* [ ] Implementar LangGraph para fluxo mais robusto
* [ ] Adicionar mais testes unitários
* [ ] Criar dashboard de métricas
* [ ] Implementar sistema de logging estruturado
* [ ] Adicionar suporte a mais moedas
* [ ] Criar API REST
* [ ] Implementar autenticação real (2FA)
* [ ] Adicionar análise de sentimento
* [ ] Implementar cache de cotações

## 📝 Notas de Desenvolvimento

* **Tempo estimado de desenvolvimento** : 4-6 horas
* **Versão Python testada** : 3.10.x
* **Compatibilidade** : Windows, Linux, macOS

## 📞 Suporte

Em caso de dúvidas ou problemas:

1. Verifique se todas as dependências estão instaladas
2. Confirme que as chaves de API estão corretas no `.env`
3. Verifique se os arquivos CSV estão no diretório correto
4. Consulte os logs de erro no terminal

## 📄 Licença

Este projeto foi desenvolvido como parte de um desafio técnico para fins educacionais e de avaliação.

---
