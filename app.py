import streamlit as st
import os
from dotenv import load_dotenv
from agents import BancoAgilSystem

# Carrega variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="Banco Ágil - Atendimento Virtual",
    page_icon="🏦",
    layout="centered"
)

# Estilo CSS customizado
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        padding: 1rem 0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        color: #1a1a1a;
    }
    .user-message {
        background-color: #e3f2fd;
        text-align: right;
        color: #0d47a1;
    }
    .agent-message {
        background-color: #f5f5f5;
        color: #212121;
        border-left: 4px solid #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho
st.markdown("<h1 class='main-header'>🏦 Banco Ágil</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Atendimento Virtual Inteligente</p>", unsafe_allow_html=True)

# Inicializa o sistema no session_state
if 'sistema' not in st.session_state:
    st.session_state.sistema = BancoAgilSystem()
    st.session_state.messages = []
    st.session_state.conversa_ativa = False

# Botão para iniciar nova conversa
if not st.session_state.conversa_ativa:
    if st.button("🚀 Iniciar Atendimento", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.sistema = BancoAgilSystem()
        st.session_state.conversa_ativa = True
        
        # Mensagem inicial
        resposta = st.session_state.sistema.processar_mensagem("")
        st.session_state.messages.append({"role": "assistant", "content": resposta})
        st.rerun()

# Exibe histórico de mensagens
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class='chat-message user-message'>
            <strong style='color: #0d47a1;'>👤 Você:</strong><br>
            <span style='color: #1565c0;'>{message["content"]}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='chat-message agent-message'>
            <strong style='color: #1f77b4;'>🤖 Assistente:</strong><br>
            <span style='color: #212121;'>{message["content"]}</span>
        </div>
        """, unsafe_allow_html=True)

# Campo de entrada de mensagem
if st.session_state.conversa_ativa:
    with st.container():
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Digite sua mensagem:",
                key="user_input",
                label_visibility="collapsed",
                placeholder="Digite sua mensagem aqui..."
            )
        
        with col2:
            send_button = st.button("Enviar", type="primary", use_container_width=True)
        
        if send_button and user_input:
            # Adiciona mensagem do usuário
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Processa mensagem
            resposta = st.session_state.sistema.processar_mensagem(user_input)
            
            # Adiciona resposta do agente
            st.session_state.messages.append({"role": "assistant", "content": resposta})
            
            # Verifica se a conversa foi encerrada
            if st.session_state.sistema.conversa_encerrada:
                st.session_state.conversa_ativa = False
            
            st.rerun()
    
    # Botão para encerrar conversa
    st.divider()
    if st.button("❌ Encerrar Atendimento", use_container_width=True):
        st.session_state.conversa_ativa = False
        st.session_state.messages = []
        st.rerun()

# Informações adicionais na sidebar
with st.sidebar:
    st.header("ℹ️ Informações")
    st.markdown("""
    **Banco Ágil** oferece:
    
    - 💳 Consulta de limite de crédito
    - 📈 Solicitação de aumento de limite
    - 🗣️ Entrevista de crédito
    - 💱 Cotação de moedas
    
    ---
    
    **Como usar:**
    1. Clique em "Iniciar Atendimento"
    2. Informe seu CPF
    3. Informe sua data de nascimento
    4. Escolha o serviço desejado
    
    ---
    
    **CPFs de teste:**
    - 12345678901 (15/05/1990)
    - 98765432100 (22/08/1985)
    - 11122233344 (10/03/1992)
    - 55566677788 (30/11/1988)
    """)
    
    if st.session_state.conversa_ativa:
        st.divider()
        st.info(f"**Agente atual:** {st.session_state.sistema.agente_atual}")
        if st.session_state.sistema.cliente_autenticado:
            st.success("✅ Cliente autenticado")