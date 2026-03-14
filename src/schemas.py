from dataclasses import dataclass
from typing import List
import json


@dataclass
class PassengerFeatureSchema:
    """DTO de entrada da API. Valida e tipifica o payload antes de qualquer lógica de negócio."""

    caracteristicas: List[float]

    @staticmethod
    def from_json(body_str: str) -> 'PassengerFeatureSchema':
        """Desserializa e valida o corpo da requisição HTTP.

        Garante que 'caracteristicas' existe, é uma lista e contém apenas valores numéricos.
        Lança ValueError com mensagem descritiva para o Controller tratar e retornar 400.
        """
        try:
            data = json.loads(body_str or '{}')
            features = data.get('caracteristicas')

            if not features or not isinstance(features, list):
                raise ValueError("O campo 'caracteristicas' deve ser uma lista valida.")

            numeric_features = [float(f) for f in features]
            return PassengerFeatureSchema(caracteristicas=numeric_features)

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            raise ValueError(f"Payload invalido: {str(e)}")