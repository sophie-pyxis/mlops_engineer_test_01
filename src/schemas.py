# Importa dataclass para estruturacao limpa de objetos de dados
from dataclasses import dataclass
# Importa tipos estaticos para clareza e ferramentas de linting (Clean Code)
from typing import List
# Importa a biblioteca padrao json para desserializacao de strings
import json

# O decorador @dataclass automatiza a criacao dos metodos dunder (ex: __init__)
@dataclass
# Classe responsavel por representar e validar os dados de entrada (Schema/DTO)
class PassengerFeatureSchema:
    # Define que o objeto deve obrigatoriamente conter uma lista de numeros em ponto flutuante
    caracteristicas: List[float]

    # Metodo estatico atua como uma Factory (Padrao de Projeto) para construir a classe a partir do HTTP
    @staticmethod
    # Recebe o corpo bruto da requisicao como uma string e retorna uma instancia do Schema
    def from_json(body_str: str) -> 'PassengerFeatureSchema':
        # Bloco de tentativa para capturar erros de integridade nos dados (Defensive Programming)
        try:
            # Converte a string JSON para um dicionario Python. Se vazio, usa um dicionario fallback '{}'
            data = json.loads(body_str or '{}')
            # Extrai o valor associado a chave 'caracteristicas'
            features = data.get('caracteristicas')
            
            # Valida logicamente se a chave existe e se o tipo primitivo e realmente uma lista
            if not features or not isinstance(features, list):
                # Interrompe o fluxo imediatamente lancando erro de validacao
                raise ValueError("O campo 'caracteristicas' deve ser uma lista valida.")
            
            # List Comprehension para iterar e garantir que todos os elementos sao conversiveis para float
            numeric_features = [float(f) for f in features]
            
            # Retorna uma nova instancia da propria classe devidamente hidratada e limpa
            return PassengerFeatureSchema(caracteristicas=numeric_features)
            
        # Captura falhas de parsing de JSON, conversao de tipo ou regras de negocio
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            # Repassa a excecao com uma mensagem detalhada para a camada Controller tratar
            raise ValueError(f"Payload invalido: {str(e)}")