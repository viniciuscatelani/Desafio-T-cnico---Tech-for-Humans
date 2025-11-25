import os
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from tavily import TavilyClient

class BancoAgilSystem:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.3
        )
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        # Estado do sistema
        self.agente_atual = "triagem"
        self.cliente_autenticado = False
        self.cliente_dados = None
        self.tentativas_auth = 0
        self.conversa_encerrada = False
        self.contexto = {}
        self.historico = []
        
    def processar_mensagem(self, mensagem: str) -> str:
        """Processa a mensagem do usuário e retorna resposta apropriada"""
        
        # Verifica se é mensagem inicial
        if not mensagem and not self.historico:
            return self._agente_triagem_inicio()
        
        # Adiciona ao histórico
        if mensagem:
            self.historico.append({"role": "user", "content": mensagem})
        
        # Verifica se usuário quer encerrar
        if self._usuario_quer_encerrar(mensagem):
            self.conversa_encerrada = True
            return "Obrigado por utilizar o Banco Ágil! Até logo! 👋"
        
        # Roteia para o agente apropriado
        if self.agente_atual == "triagem":
            resposta = self._processar_triagem(mensagem)
        elif self.agente_atual == "credito":
            resposta = self._processar_credito(mensagem)
        elif self.agente_atual == "entrevista":
            resposta = self._processar_entrevista(mensagem)
        elif self.agente_atual == "cambio":
            resposta = self._processar_cambio(mensagem)
        else:
            resposta = "Desculpe, ocorreu um erro. Por favor, reinicie o atendimento."
        
        self.historico.append({"role": "assistant", "content": resposta})
        return resposta
    
    def _usuario_quer_encerrar(self, mensagem: str) -> bool:
        """Detecta se usuário quer encerrar a conversa"""
        if not mensagem:
            return False
        
        palavras_chave = ["tchau", "encerrar", "sair", "finalizar", "desligar", "até logo", "adeus"]
        return any(palavra in mensagem.lower() for palavra in palavras_chave)
    
    def _detectar_intencao_negativa(self, mensagem: str, contexto_pergunta: str = "") -> bool:
        """Detecta se o usuário quer encerrar a atividade atual ou responde negativamente"""
        if not mensagem:
            return False
        
        prompt = ChatPromptTemplate.from_template("""
Você é um classificador de intenções de usuário em um banco.

Contexto da pergunta anterior: {contexto}
Resposta do usuário: {mensagem}

O usuário está indicando que NÃO quer continuar com a atividade/serviço atual?
Exemplos de respostas negativas: "não", "não quero", "agora não", "deixa pra depois", "não precisa", "tá bom assim", "só isso mesmo", "é só isso", "não obrigado"

Responda APENAS com: SIM ou NAO
""")
        
        try:
            chain = prompt | self.llm
            resultado = chain.invoke({
                "contexto": contexto_pergunta,
                "mensagem": mensagem
            })
            resposta = resultado.content.strip().upper()
            return "SIM" in resposta
        except:
            # Fallback para palavras-chave simples se LLM falhar
            negativas = ["não", "nao", "nada", "agora não", "deixa", "só isso", "é só isso"]
            return any(neg in mensagem.lower() for neg in negativas)
    
    def _agente_triagem_inicio(self) -> str:
        """Mensagem inicial do agente de triagem"""
        return "Olá! Bem-vindo ao Banco Ágil. 🏦\n\nSou seu assistente virtual e estou aqui para ajudá-lo.\n\nPara começarmos, por favor, informe seu CPF (somente números):"
    
    def _processar_triagem(self, mensagem: str) -> str:
        """Processa mensagens do agente de triagem"""
        
        # Etapa 1: Coletar CPF
        if "cpf" not in self.contexto:
            cpf = self._extrair_cpf(mensagem)
            if cpf:
                self.contexto["cpf"] = cpf
                return "Obrigado! Agora, por favor, informe sua data de nascimento no formato DD/MM/AAAA:"
            else:
                return "Desculpe, não consegui identificar um CPF válido. Por favor, informe apenas os 11 números do CPF:"
        
        # Etapa 2: Coletar data de nascimento e autenticar
        if "data_nascimento" not in self.contexto:
            data = self._extrair_data(mensagem)
            if data:
                self.contexto["data_nascimento"] = data
                return self._autenticar_cliente()
            else:
                return "Por favor, informe a data de nascimento no formato DD/MM/AAAA (exemplo: 15/05/1990):"
        
        # Etapa 3: Identificar intenção e redirecionar
        if self.cliente_autenticado:
            return self._identificar_intencao(mensagem)
        
        return "Desculpe, houve um erro no processo. Por favor, reinicie o atendimento."
    
    def _extrair_cpf(self, mensagem: str) -> Optional[str]:
        """Extrai CPF da mensagem"""
        import re
        cpf = re.sub(r'\D', '', mensagem)
        if len(cpf) == 11:
            return cpf
        return None
    
    def _extrair_data(self, mensagem: str) -> Optional[str]:
        """Extrai data de nascimento da mensagem"""
        import re
        
        # Tenta encontrar data no formato DD/MM/AAAA
        match = re.search(r'(\d{2})[/-](\d{2})[/-](\d{4})', mensagem)
        if match:
            dia, mes, ano = match.groups()
            return f"{ano}-{mes}-{dia}"
        
        # Tenta encontrar data no formato AAAA-MM-DD
        match = re.search(r'(\d{4})[/-](\d{2})[/-](\d{2})', mensagem)
        if match:
            return match.group(0).replace('/', '-')
        
        return None
    
    def _autenticar_cliente(self) -> str:
        """Autentica o cliente contra a base de dados"""
        try:
            df = pd.read_csv("clientes.csv")
            cliente = df[
                (df["cpf"].astype(str) == self.contexto["cpf"]) &
                (df["data_nascimento"] == self.contexto["data_nascimento"])
            ]
            
            if not cliente.empty:
                self.cliente_autenticado = True
                self.cliente_dados = cliente.iloc[0].to_dict()
                self.tentativas_auth = 0
                
                return f"""Perfeito! Autenticação realizada com sucesso. ✅

Olá, {self.cliente_dados['nome']}! Como posso ajudá-lo hoje?

Posso auxiliar com:
💳 Consulta de limite de crédito
📈 Solicitação de aumento de limite
💱 Cotação de moedas

O que você gostaria de fazer?"""
            else:
                self.tentativas_auth += 1
                if self.tentativas_auth >= 3:
                    self.conversa_encerrada = True
                    return "Infelizmente não foi possível completar a autenticação após 3 tentativas. Por favor, dirija-se a uma agência ou entre em contato com nosso SAC. Até logo!"
                else:
                    self.contexto = {}  # Limpa contexto para nova tentativa
                    tentativas_restantes = 3 - self.tentativas_auth
                    return f"""Desculpe, os dados informados não conferem. ❌

Você tem mais {tentativas_restantes} tentativa(s).

Por favor, informe seu CPF novamente:"""
        except Exception as e:
            return f"Erro ao acessar a base de dados. Por favor, tente novamente mais tarde. Detalhes: {str(e)}"
    
    def _identificar_intencao(self, mensagem: str) -> str:
        """Identifica a intenção do cliente e redireciona"""
        
        # Primeiro verifica se quer encerrar explicitamente
        if self._detectar_intencao_negativa(mensagem, "Posso ajudá-lo com algo mais?"):
            self.conversa_encerrada = True
            return "Obrigado por utilizar o Banco Ágil! Até logo! 👋"
        
        prompt = ChatPromptTemplate.from_template("""
Você é um assistente de classificação de intenções para um banco.

Analise a mensagem do cliente e identifique a intenção principal. Responda APENAS com uma das opções:
- credito: se o cliente quer consultar limite ou solicitar aumento de crédito
- cambio: se o cliente quer consultar cotação de moedas
- outros: se não se encaixa nas opções acima

Mensagem do cliente: {mensagem}

Intenção:""")
        
        chain = prompt | self.llm
        resultado = chain.invoke({"mensagem": mensagem})
        intencao = resultado.content.strip().lower()
        
        if "credito" in intencao or "crédito" in intencao:
            self.agente_atual = "credito"
            return self._iniciar_agente_credito()
        elif "cambio" in intencao or "câmbio" in intencao or "moeda" in intencao:
            self.agente_atual = "cambio"
            return self._iniciar_agente_cambio()
        else:
            return """Entendi! Posso ajudá-lo com:

💳 **Crédito**: Consultar seu limite ou solicitar aumento
💱 **Câmbio**: Ver cotação de moedas

Qual serviço você precisa?"""
    
    def _iniciar_agente_credito(self) -> str:
        """Inicia o agente de crédito"""
        limite_atual = self.cliente_dados.get("limite_credito", 0)
        
        # Verifica se já mencionou aumento na mensagem de entrada
        ultimo_user_msg = ""
        for msg in reversed(self.historico):
            if msg["role"] == "user":
                ultimo_user_msg = msg["content"]
                break
        
        # Tenta extrair valor da mensagem
        import re
        valor_match = re.search(r'(\d+\.?\d*)', ultimo_user_msg.replace(',', '.'))
        
        # Se já mencionou aumento E informou valor, processa direto
        if any(palavra in ultimo_user_msg.lower() for palavra in ["aumento", "aumentar", "solicitar", "elevar", "novo limite"]):
            if valor_match:
                valor = float(valor_match.group(1))
                return self._processar_solicitacao_aumento(valor)
            else:
                # Mencionou aumento mas não informou valor
                return f"""Perfeito! Seu limite de crédito atual é de R$ {limite_atual:.2f}

Qual o novo limite de crédito você gostaria de ter? Por favor, informe o valor em reais:"""
        
        # Senão, oferece opções
        return f"""Perfeito! Seu limite de crédito atual é de R$ {limite_atual:.2f}

Você gostaria de solicitar um aumento de limite ou precisa de alguma outra informação sobre seu crédito?"""
    
    def _processar_credito(self, mensagem: str) -> str:
        """Processa mensagens do agente de crédito"""
        
        # Verifica se usuário não quer mais nada após aprovação/rejeição
        if self.contexto.get("solicitacao_processada"):
            
            # --- CORREÇÃO AQUI: Verificamos troca de contexto PRIMEIRO ---
            
            # Se mencionou outro serviço (Câmbio), redireciona
            if any(palavra in mensagem.lower() for palavra in ["cotação", "cotacao", "cambio", "câmbio", "moeda", "dolar", "euro", "libra", "peso"]):
                self.agente_atual = "cambio"
                self.contexto.pop("solicitacao_processada", None)
                # Passa a mensagem para o agente de câmbio processar imediatamente
                return self._processar_cambio(mensagem)
            
            # Só depois verificamos se é uma negativa para encerrar
            if self._detectar_intencao_negativa(mensagem, "Posso ajudá-lo com algo mais?"):
                self.conversa_encerrada = True
                return "Obrigado por utilizar o Banco Ágil! Até logo! 👋"

        # Detecta solicitação de aumento com valor já informado
        import re
        if any(palavra in mensagem.lower() for palavra in ["aumento", "aumentar", "solicitar", "elevar", "novo limite"]):
            valor_match = re.search(r'(\d+\.?\d*)', mensagem.replace(',', '.'))
            if valor_match:
                valor = float(valor_match.group(1))
                return self._processar_solicitacao_aumento(valor)
            else:
                return self._solicitar_valor_aumento()
        
        # Detecta valor numérico para aumento (quando já estava em contexto de aumento)
        valor_match = re.search(r'(\d+\.?\d*)', mensagem.replace(',', '.'))
        if valor_match:
            valor = float(valor_match.group(1))
            return self._processar_solicitacao_aumento(valor)
        
        # Verifica se cliente quer entrevista após rejeição
        if self.contexto.get("solicitacao_rejeitada"):
            # Aqui também aplicamos a mesma lógica: verifica se quer sair antes de assumir negativa
            # Mas para entrevista, "não" geralmente significa "não quero entrevista" (voltar ou sair)
            if self._detectar_intencao_negativa(mensagem, "Gostaria de prosseguir com essa análise?"):
                # Se disse não para a entrevista, perguntamos se quer outra coisa ao invés de sair direto
                self.contexto.pop("solicitacao_rejeitada", None)
                return self._voltar_menu_principal()

            elif any(palavra in mensagem.lower() for palavra in ["sim", "quero", "aceito", "vamos", "pode", "prosseguir"]):
                self.agente_atual = "entrevista"
                return self._iniciar_entrevista()
        
        # Caso genérico - oferece opções
        limite_atual = self.cliente_dados.get("limite_credito", 0)
        return f"""Seu limite de crédito atual é de R$ {limite_atual:.2f}

Como posso ajudá-lo com seu crédito?"""
    
    def _solicitar_valor_aumento(self) -> str:
        """Solicita o valor desejado para aumento"""
        return "Perfeito! Qual o novo limite de crédito você gostaria de ter? Por favor, informe o valor em reais:"
    
    def _processar_solicitacao_aumento(self, valor_solicitado: float) -> str:
        """Processa a solicitação de aumento de limite"""
        
        try:
            # Carrega tabela de score x limite
            df_score = pd.read_csv("score_limite.csv")
            
            # Verifica limite permitido para o score atual
            score_atual = self.cliente_dados["score"]
            limite_atual = self.cliente_dados["limite_credito"]
            
            limite_permitido = None
            for _, row in df_score.iterrows():
                if row["score_min"] <= score_atual <= row["score_max"]:
                    limite_permitido = row["limite_maximo"]
                    break
            
            # Registra solicitação
            timestamp = datetime.now().isoformat()
            
            if valor_solicitado <= limite_permitido:
                status = "aprovado"
                self.contexto["solicitacao_processada"] = True
                resposta = f"""✅ Ótimas notícias! Sua solicitação foi APROVADA!

Seu novo limite de crédito de R$ {valor_solicitado:.2f} já está disponível para uso.

Posso ajudá-lo com algo mais?"""
                
                # Atualiza limite do cliente
                self._atualizar_limite_cliente(valor_solicitado)
            else:
                status = "rejeitado"
                self.contexto["solicitacao_rejeitada"] = True
                resposta = f"""❌ Infelizmente sua solicitação não pode ser aprovada no momento.

Com base no seu perfil atual, o limite máximo disponível seria de R$ {limite_permitido:.2f}.

No entanto, posso fazer uma análise mais detalhada do seu perfil financeiro que pode viabilizar o limite desejado. Isso levará apenas alguns minutos.

Gostaria de prosseguir com essa análise?"""
            
            # Salva solicitação
            self._salvar_solicitacao(
                self.contexto["cpf"],
                timestamp,
                limite_atual,
                valor_solicitado,
                status
            )
            
            return resposta
            
        except Exception as e:
            return f"Erro ao processar solicitação: {str(e)}"
    
    def _salvar_solicitacao(self, cpf, timestamp, limite_atual, novo_limite, status):
        """Salva solicitação de aumento no CSV"""
        try:
            # Cria ou lê o arquivo
            try:
                df = pd.read_csv("solicitacoes_aumento_limite.csv")
            except FileNotFoundError:
                df = pd.DataFrame(columns=[
                    "cpf_cliente", "data_hora_solicitacao", "limite_atual",
                    "novo_limite_solicitado", "status_pedido"
                ])
            
            # Adiciona nova solicitação
            nova_linha = pd.DataFrame([{
                "cpf_cliente": cpf,
                "data_hora_solicitacao": timestamp,
                "limite_atual": limite_atual,
                "novo_limite_solicitado": novo_limite,
                "status_pedido": status
            }])
            
            df = pd.concat([df, nova_linha], ignore_index=True)
            df.to_csv("solicitacoes_aumento_limite.csv", index=False)
        except Exception as e:
            print(f"Erro ao salvar solicitação: {e}")
    
    def _atualizar_limite_cliente(self, novo_limite: float):
        """Atualiza o limite do cliente no CSV"""
        try:
            df = pd.read_csv("clientes.csv")
            df.loc[df["cpf"].astype(str) == self.contexto["cpf"], "limite_credito"] = novo_limite
            df.to_csv("clientes.csv", index=False)
            self.cliente_dados["limite_credito"] = novo_limite
        except Exception as e:
            print(f"Erro ao atualizar limite: {e}")
    
    def _iniciar_entrevista(self) -> str:
        """Inicia a entrevista de crédito"""
        self.contexto["entrevista"] = {}
        return """Entendi! Para analisarmos melhor seu perfil e verificarmos possibilidades de aumento, preciso atualizar algumas informações.

Primeira pergunta: Qual é sua renda mensal em reais?"""
    
    def _processar_entrevista(self, mensagem: str) -> str:
        """Processa a entrevista de crédito"""
        
        entrevista = self.contexto.get("entrevista", {})
        
        # Pergunta 1: Renda mensal
        if "renda_mensal" not in entrevista:
            import re
            valor = re.search(r'(\d+\.?\d*)', mensagem.replace(',', '.'))
            if valor:
                entrevista["renda_mensal"] = float(valor.group(1))
                self.contexto["entrevista"] = entrevista
                return "Qual é o seu tipo de emprego?\n1. Formal (CLT)\n2. Autônomo\n3. Desempregado"
            return "Por favor, informe sua renda mensal em reais (exemplo: 5000):"
        
        # Pergunta 2: Tipo de emprego
        if "tipo_emprego" not in entrevista:
            msg_lower = mensagem.lower()
            if "formal" in msg_lower or "clt" in msg_lower or "1" in mensagem:
                entrevista["tipo_emprego"] = "formal"
            elif "autônomo" in msg_lower or "autonomo" in msg_lower or "2" in mensagem:
                entrevista["tipo_emprego"] = "autônomo"
            elif "desempregado" in msg_lower or "3" in mensagem:
                entrevista["tipo_emprego"] = "desempregado"
            else:
                return "Por favor, escolha uma opção:\n1. Formal (CLT)\n2. Autônomo\n3. Desempregado"
            
            self.contexto["entrevista"] = entrevista
            return "Quais são suas despesas fixas mensais em reais?"
        
        # Pergunta 3: Despesas fixas
        if "despesas_fixas" not in entrevista:
            import re
            valor = re.search(r'(\d+\.?\d*)', mensagem.replace(',', '.'))
            if valor:
                entrevista["despesas_fixas"] = float(valor.group(1))
                self.contexto["entrevista"] = entrevista
                return "Quantos dependentes você tem?\n0, 1, 2 ou 3+"
            return "Por favor, informe suas despesas fixas mensais em reais:"
        
        # Pergunta 4: Dependentes
        if "dependentes" not in entrevista:
            if "0" in mensagem:
                entrevista["dependentes"] = 0
            elif "1" in mensagem:
                entrevista["dependentes"] = 1
            elif "2" in mensagem:
                entrevista["dependentes"] = 2
            elif "3" in mensagem or "+" in mensagem:
                entrevista["dependentes"] = "3+"
            else:
                return "Por favor, informe o número de dependentes: 0, 1, 2 ou 3+"
            
            self.contexto["entrevista"] = entrevista
            return "Você possui dívidas ativas? (sim ou não)"
        
        # Pergunta 5: Dívidas
        if "dividas" not in entrevista:
            msg_lower = mensagem.lower()
            if "sim" in msg_lower or "tenho" in msg_lower:
                entrevista["dividas"] = "sim"
            elif "não" in msg_lower or "nao" in msg_lower:
                entrevista["dividas"] = "não"
            else:
                return "Por favor, responda com 'sim' ou 'não'."
            
            self.contexto["entrevista"] = entrevista
            return self._calcular_novo_score()
        
        return "Erro no processamento da entrevista."
    
    def _calcular_novo_score(self) -> str:
        """Calcula o novo score baseado nas respostas"""
        
        entrevista = self.contexto["entrevista"]
        
        # Pesos
        peso_renda = 30
        peso_emprego = {
            "formal": 300,
            "autônomo": 200,
            "desempregado": 0
        }
        peso_dependentes = {
            0: 100,
            1: 80,
            2: 60,
            "3+": 30
        }
        peso_dividas = {
            "sim": -100,
            "não": 100
        }
        
        # Cálculo
        renda = entrevista["renda_mensal"]
        despesas = entrevista["despesas_fixas"]
        
        score = (
            (renda / (despesas + 1)) * peso_renda +
            peso_emprego[entrevista["tipo_emprego"]] +
            peso_dependentes[entrevista["dependentes"]] +
            peso_dividas[entrevista["dividas"]]
        )
        
        # Limita entre 0 e 1000
        score = max(0, min(1000, int(score)))
        
        # Atualiza score do cliente
        score_antigo = self.cliente_dados["score"]
        self._atualizar_score_cliente(score)
        
        # Retorna ao agente de crédito
        self.agente_atual = "credito"
        self.contexto["solicitacao_rejeitada"] = False
        
        return f"""✅ Análise concluída!

Com base nas novas informações, seu perfil foi reavaliado. Seu score foi atualizado de {score_antigo} para {score}.

Agora você pode fazer uma nova solicitação de aumento de limite.

Qual seria o limite desejado?"""
    
    def _atualizar_score_cliente(self, novo_score: int):
        """Atualiza o score do cliente no CSV"""
        try:
            df = pd.read_csv("clientes.csv")
            df.loc[df["cpf"].astype(str) == self.contexto["cpf"], "score"] = novo_score
            df.to_csv("clientes.csv", index=False)
            self.cliente_dados["score"] = novo_score
        except Exception as e:
            print(f"Erro ao atualizar score: {e}")
    
    def _iniciar_agente_cambio(self) -> str:
        """Inicia o agente de câmbio"""
        return "Posso consultar a cotação de moedas para você. 💱\n\nQual moeda você gostaria de consultar? (exemplo: dólar, euro, libra)"
    
    def _processar_cambio(self, mensagem: str) -> str:
        """Processa consulta de câmbio"""
        
        try:
            # Verifica se usuário não quer mais cotações
            if self.contexto.get("cotacao_realizada"):
                
                # --- CORREÇÃO AQUI TAMBÉM ---
                
                # 1. Verifica se quer trocar para CRÉDITO
                if any(palavra in mensagem.lower() for palavra in ["limite", "aumento", "credito", "crédito", "cartão"]):
                    self.agente_atual = "credito"
                    self.contexto.pop("cotacao_realizada", None)
                    return self._iniciar_agente_credito()

                # 2. Verifica negativa (Encerrar)
                if self._detectar_intencao_negativa(mensagem, "Gostaria de consultar outra moeda?"):
                    self.conversa_encerrada = True
                    return "Obrigado por utilizar o Banco Ágil! Até logo! 👋"
            
            # Identifica a moeda
            moeda = self._identificar_moeda(mensagem)
            
            # Se não identificou moeda e não estamos num fluxo contínuo, pede a moeda
            if moeda == mensagem and not self.contexto.get("cotacao_realizada"):
                 # Tenta ver se é uma saudação ou algo genérico
                 return "Qual moeda você gostaria de consultar? (ex: dólar, euro)"

            # Busca cotação usando Tavily
            query = f"cotação {moeda} hoje Brasil"
            resultado = self.tavily_client.search(query, max_results=3)
            
            # ... (Restante do código de extração com LLM permanece igual) ...
            
            # Extrai informação da cotação
            prompt = ChatPromptTemplate.from_template("""
Com base nos seguintes resultados de busca, extraia a cotação atual do {moeda} em reais brasileiros.

Resultados:
{resultados}

Responda de forma clara e direta, informando o valor da cotação.
""")
            
            resultados_texto = "\n\n".join([
                f"Fonte: {r.get('title', 'N/A')}\n{r.get('content', '')}"
                for r in resultado.get('results', [])
            ])
            
            chain = prompt | self.llm
            resposta = chain.invoke({
                "moeda": moeda,
                "resultados": resultados_texto
            })
            
            cotacao = resposta.content
            
            # Marca que já foi feita uma cotação
            self.contexto["cotacao_realizada"] = True
            
            return f"""💱 Cotação do {moeda.upper()}:

{cotacao}

Gostaria de consultar outra moeda?"""
            
        except Exception as e:
            return f"Desculpe, não consegui consultar a cotação no momento. Erro: {str(e)}\n\nPosso ajudá-lo com algo mais?"
    
    def _voltar_menu_principal(self) -> str:
        """Volta ao menu principal oferecendo outros serviços"""
        # Limpa contextos específicos
        self.contexto.pop("cotacao_realizada", None)
        self.contexto.pop("solicitacao_processada", None)
        self.contexto.pop("solicitacao_rejeitada", None)
        
        # Retorna para triagem (modo menu)
        self.agente_atual = "triagem"
        
        return """Entendi! Posso ajudá-lo com:

💳 **Crédito**: Consultar seu limite ou solicitar aumento
💱 **Câmbio**: Cotação de moedas

Qual serviço você precisa?"""
    
    def _identificar_moeda(self, mensagem: str) -> str:
        """Identifica a moeda mencionada"""
        msg_lower = mensagem.lower()
        
        if "dolar" in msg_lower or "dólar" in msg_lower or "usd" in msg_lower:
            return "dólar"
        elif "euro" in msg_lower or "eur" in msg_lower:
            return "euro"
        elif "libra" in msg_lower or "gbp" in msg_lower:
            return "libra"
        elif "peso" in msg_lower:
            return "peso argentino"
        else:
            return mensagem  # Retorna a mensagem original se não identificar