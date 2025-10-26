# data_validator.py

from pydantic import BaseModel, ValidationError, Field
from typing import List
import pandas as pd


class NotaFiscal(BaseModel):
    valor: float = Field(
        gt=0, description="Valor da nota fiscal deve ser maior que zero."
    )
    cfop: str = Field(pattern=r"^\d{4}$", description="CFOP deve conter 4 dígitos.")
    emitente: str
    data: str


class DataValidator:
    """
    Classe responsável por validar dados fiscais.
    """

    @staticmethod
    def validar_dados(df: pd.DataFrame) -> List[str]:
        erros = []
        for index, row in df.iterrows():
            try:
                nota = NotaFiscal(
                    valor=row["valor"],
                    cfop=row["cfop"],
                    emitente=row["emitente"],
                    data=row["data"],
                )
            except ValidationError as e:
                erros.append(f"Linha {index + 1}: {e}")
        return erros
