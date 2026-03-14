# Importa gerador de strings pseudo-aleatorias baseadas em tempo
import uuid
# Importa ferramenta padrao para lidar com JSON responses
import json
# Importa o logger corporativo
import logging
# Importa definicoes formais de tipo de dados
from typing import Dict, Any
# Importa as classes construidas para Inversao/Injecao de Dependencias (Principio D do SOLID)
from schemas import PassengerFeatureSchema
from service import InferenceService
from repository import PassengerRepository

# Acessa a raiz de eventos logaveis
logger = logging.getLogger()

# Classe orquestradora: Recebe request, comanda dominios e formata a resposta padronizada
class PassengerController:
    # Metodo construtor aplica padrao de Injecao de Dependencias, vital para testes Mocks unitarios
    def __init__(self, service: InferenceService, repository: PassengerRepository):
        # Acopla a logica analitica injetada
        self.service = service
        # Acopla a logica de banco injetada
        self.repository = repository

    # Lida com o roteamento do metodo POST para criar predicoes
    def create_passenger(self, body_str: str) -> Dict[str, Any]:
        # Bloco Try isola possiveis erros de formato capturados pelo Schema
        try:
            # Etapa 1: Valida o payload de string impuro para um DTO confiavel 
            schema = PassengerFeatureSchema.from_json(body_str)
            
            # Etapa 2: Entrega o dado purificado a camada de servico para processamento de ML
            probability = self.service.calculate_survival_probability(schema.caracteristicas)
            
            # Etapa 3: Instancia um UUIDv4 (string universal unica) para o rastreio da entidade
            passenger_id = str(uuid.uuid4())
            
            # Etapa 4: Solicita a persistencia dos dados ao Repository
            self.repository.save(passenger_id, schema.caracteristicas, probability)
            
            # Etapa 5: Empacota a estrutura de exito e retorna Http Code 201 (Created)
            return self._build_response(201, {'id': passenger_id, 'probabilidade_sobrevivencia': probability})
            
        # Captura os problemas de consistencia lancados especificamente pela classe Schema
        except ValueError as e:
            # Emite log de tipo Warning pois e um erro do lado do cliente (Bad Request), nao da maquina
            logger.warning(f"Rejeicao por quebra de contrato (Schema): {str(e)}")
            # Retorna Http Code 400 avisando quem consumiu a API do erro de sintaxe
            return self._build_response(400, {'erro': str(e)})

    # Lida com o roteamento do metodo GET geral (Listagem)
    def get_passengers(self) -> Dict[str, Any]:
        # Delega diretamente ao repositorio a acao de buscar lista completa
        items = self.repository.get_all()
        # Retorna com Http Code 200 (Success)
        return self._build_response(200, items)

    # Lida com a extracao de um recurso pontual (GET parametrizado)
    def get_passenger(self, passenger_id: str) -> Dict[str, Any]:
        # Comanda o resgate unitario na base
        item = self.repository.get_by_id(passenger_id)
        
        # Verifica se o objeto e valido (nao e None)
        if item:
            # Trata o valor recuperado, convertendo do formato 'string' do dynamoDB para ponto flutuante Json
            item['probabilidade_sobrevivencia'] = float(item['probabilidade_sobrevivencia'])
            # Retorna o passageiro
            return self._build_response(200, item)
        
        # Caso objeto retorne None, o passageiro nao reside na base: envia 404 (Not Found)
        return self._build_response(404, {'erro': 'Passageiro nao encontrado'})

    # Lida com o percurso de delecao (DELETE)
    def delete_passenger(self, passenger_id: str) -> Dict[str, Any]:
        # Orquestra remocao perante camada persistente
        self.repository.delete(passenger_id)
        # O padrao REST designa o retorno 204 (No Content) para deletes bem-sucedidos sem corpo de reposta
        return self._build_response(204, '')

    # Helper privado interno responsavel por uniformizar as cascas do formato HTTP
    def _build_response(self, status_code: int, body: Any) -> Dict[str, Any]:
        # Monta a assinatura estrita requisitada pelo AWS API Gateway Proxy
        return {
            # Define o codigo cabecalho do status
            'statusCode': status_code,
            # Forca informacao MIME garantindo leitura correta no cliente/Frontend
            'headers': {'Content-Type': 'application/json'},
            # Serializa a resposta se houver dados, ou entrega string nula
            'body': json.dumps(body) if body else ''
        }