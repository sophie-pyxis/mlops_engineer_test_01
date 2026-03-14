import boto3
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger()


class PassengerRepository:
    """Centraliza todo o acesso ao DynamoDB, isolando a lógica de persistência das demais camadas."""

    def __init__(self):
        # Conexão inicializada no Cold Start e reaproveitada nos Warm Starts subsequentes
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_TABLE', 'sobreviventes_titanic')
        self.table = self.dynamodb.Table(self.table_name)

    def save(self, passenger_id: str, features: list, probability: float) -> None:
        """Persiste a predição gerada pelo modelo. Probabilidade salva como string
        para evitar conflito com o tipo Decimal nativo do DynamoDB."""
        logger.info(f"Persistindo passageiro {passenger_id} no DynamoDB.")
        self.table.put_item(Item={
            'id': passenger_id,
            'caracteristicas': features,
            'probabilidade_sobrevivencia': str(probability)
        })

    def get_all(self) -> List[Dict[str, Any]]:
        """Realiza um Scan completo na tabela. Operação monitorada por ser custosa em tabelas grandes."""
        logger.info("Executando Scan completo na tabela.")
        response = self.table.scan()
        return response.get('Items', [])

    def get_by_id(self, passenger_id: str) -> Dict[str, Any]:
        """Busca um passageiro pela chave primária. Retorna None se não encontrado."""
        logger.info(f"Buscando passageiro {passenger_id}.")
        response = self.table.get_item(Key={'id': passenger_id})
        return response.get('Item')

    def delete(self, passenger_id: str) -> None:
        """Remove o registro do passageiro. Operação irreversível registrada em log para auditoria."""
        logger.info(f"Removendo passageiro {passenger_id}.")
        self.table.delete_item(Key={'id': passenger_id})