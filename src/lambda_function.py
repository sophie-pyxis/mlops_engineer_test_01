# Importa para gestao da instrumentacao analitica de diagnostico
import logging
# Importa os modulos isolados da nossa arquitetura estruturada
from controller import PassengerController
from service import InferenceService
from repository import PassengerRepository

# Inicializa o framework de monitoramento nativo no ambiente da nuvem
logger = logging.getLogger()
# Força nivel INFO para que impressoes analiticas sejam armazenadas no CloudWatch Logs
logger.setLevel(logging.INFO)

# Instancia as dependencias no espaco Global (Fora da Funcao Handler).
# Isso aplica o padrao Reuse da AWS: conexoes HTTP e memorias das classes persistem 
# vivas em background para as proximas chamadas da mesma maquina (Warm Container).
service = InferenceService()
repository = PassengerRepository()
# Fabrica o controller unindo as partes (Injecao via construtor)
controller = PassengerController(service, repository)

# Funcao de Entrada Absoluta. A AWS localiza este 'Entrypoint' por padrao.
def lambda_handler(event, context):
    # Extrai o verbo HTTP (Ex: POST, GET, DELETE) da abstracao do evento do Gateway
    http_method = event.get('httpMethod')
    # Extrai a rota bruta ativada
    resource = event.get('resource')
    
    # Rastro generico de acoplamento transacional
    logger.info(f"Recebendo disparo de Rota Externa: [ {http_method} ] na path {resource}")

    # Bloco global superior visando contornar bugs obscuros (Fail-Safe Mechanism)
    try:
        # Se for um envio de dados para calcular probabilidade...
        if http_method == 'POST' and resource == '/sobreviventes':
            # Repassa a carga de dados para o orquestrador
            return controller.create_passenger(event.get('body'))
            
        # Se for solicitada a lista de passageiros...
        elif http_method == 'GET' and resource == '/sobreviventes':
            # Ativa rotina de scanner
            return controller.get_passengers()
            
        # Se for para consultar as estatisticas de uma chave/ID unica...
        elif http_method == 'GET' and resource == '/sobreviventes/{id}':
            # Isola o campo identificador de dentro do roteamento do caminho URI
            passenger_id = event['pathParameters']['id']
            # Requisita a pesquisa
            return controller.get_passenger(passenger_id)
            
        # Se o sistema frontend precisar purgar metadados devido a LGPD...
        elif http_method == 'DELETE' and resource == '/sobreviventes/{id}':
            # Extrai novamente a chave a ser extirpada
            passenger_id = event['pathParameters']['id']
            # Delega delecao
            return controller.delete_passenger(passenger_id)
            
        # Caso ocorra falha de roteamento por endpoint desconhecido:
        else:
            # Dispara log de trafego indevido para ferramentas APM (Ex: Datadog)
            logger.warning(f"Invocacao HTTP desestruturada detectada e barrada: {resource}")
            # Emite HTTP 405 bloqueando trafego lixo
            return controller._build_response(405, {'erro': 'Metodo ou Rota nao permitidos'})

    # Interceptacao generica final: Garantia de continuidade caso uma anomalia severa (OOM, timeout) passe
    except Exception as e:
        # Usa exc_info=True para desenhar todo o traceback analitico na interface de erro (CloudWatch)
        logger.error(f"Pânico sistêmico não mapeado (Catástrofe): {str(e)}", exc_info=True)
        # Devolve HTTP 500 elegante a quem chamou, mascarando traces que sao vetores de ciberataques
        return controller._build_response(500, {'erro_interno': 'Falha no servidor de Machine Learning'})