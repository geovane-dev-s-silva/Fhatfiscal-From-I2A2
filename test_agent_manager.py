import unittest
from agent_manager import AgentManager


class TestAgentManager(unittest.TestCase):

    def setUp(self):
        self.manager = AgentManager()

    def test_carregar_arquivo_csv(self):
        # Simula o carregamento de um arquivo CSV válido
        with open("data/exemplo.csv", "r") as arquivo:
            df = self.manager.carregar_arquivo(arquivo)
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)

    def test_validar_arquivo(self):
        # Simula a validação de um arquivo carregado
        with open("data/exemplo.csv", "r") as arquivo:
            self.manager.carregar_arquivo(arquivo)
        relatorio = self.manager.validar_arquivo()
        self.assertIn("validation error", relatorio)

    def test_gerar_resposta(self):
        # Simula a geração de uma resposta baseada nos dados
        with open("data/exemplo.csv", "r") as arquivo:
            self.manager.carregar_arquivo(arquivo)
        resposta = self.manager.gerar_resposta("Qual o faturamento total?")
        self.assertIsInstance(resposta, str)


if __name__ == "__main__":
    unittest.main()
