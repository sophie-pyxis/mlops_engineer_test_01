# Importa a SDK oficial da AWS para interacao com recursos da nuvem
import boto3
# Importa interface com sistema operacional para leitura de variaveis de ambiente
import os
# Importa o modulo de logs para observabilidade
import logging
# Importa tipagem estruturada
from typing import List, Dict, Any

# Resgata o logger raiz configurado previamente no Entrypoint
logger = logging.getLogger()

# Implementa o padrao Repository para centralizar regras de acesso ao banco e isolar o ORM
class PassengerRepository:
    # Metodo construtor e inicializado na primeira execucao (Cold Start)
    def __init__(self):
        # Instancia o recurso de alto nivel do DynamoDB mantendo o pool HTTP ativo (reaproveitamento)
        self.dynamodb = boto3.resource('dynamodb')
        # Busca o nome da tabela dinamicamente a partir do ambiente (injetado via Terraform)
        self.table_name = os.environ.get('DYNAMODB_TABLE', 'sobreviventes_titanic')
        # Conecta o recurso especificamente a tabela do Titanic
        self.table = self.dynamodb.Table(self.table_name)

    # Metodo para salvar a avaliacao analitica do passageiro (Create)
    def save(self, passenger_id: str, features: list, probability: float) -> None:
        # Gera log informativo essencial para rastreabilidade de auditoria (Governance)
        logger.info(f"Persistindo dados do passageiro {passenger_id} no DynamoDB.")
        # Insere ou substitui o item na tabela
        self.table.put_item(Item={
            # Persiste a chave primaria gerada
            'id': passenger_id,
            # Persiste os atributos transacionais independentes
            'caracteristicas': features,
            # Boto3/DynamoDB exigem tipos rigidos; cast de float nativo para string evita erros de Decimal
            'probabilidade_sobrevivencia': str(probability) 
        })

    # Metodo para resgatar todo o historico do banco (Read All)
    def get_all(self) -> List]:
        # Loga a acao de Scan (operacao pesada, monitorada por analistas FinOps)
        logger.info("Buscando todos os registros na base via operacao de Scan.")
        # Executa a varredura total da tabela
        response = self.table.scan()
        # Retorna a lista de itens, ou lista vazia caso falhe ou banco esteja limpo
        return response.get('Items',)

    # Metodo para buscar um passageiro pontual (Read One)
    def get_by_id(self, passenger_id: str) -> Dict[str, Any]:
        # Log para tracking transacional em nivel de cliente
        logger.info(f"Buscando registro para o passageiro {passenger_id}.")
        # Executa operacao de busca rapida baseada na chave Hash primária
        response = self.table.get_item(Key={'id': passenger_id})
        # Retorna o dicionario do item caso exista, senao None
        return response.get('Item')

    # Metodo para deletar o registro visando compliance (Delete)
    def delete(self, passenger_id: str) -> None:
        # Registra operacao destrutiva em logs, vital para seguranca e tracing
        logger.info(f"Removendo passageiro {passenger_id} da base de dados.")
        # Executa comando de exclusao garantido pela chave de particao
        self.table.delete_item(Key={'id': passenger_id})