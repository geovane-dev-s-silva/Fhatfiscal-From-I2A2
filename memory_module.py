# memory_module.py - VERSÃO COMPLETA COM MEMÓRIA INTELIGENTE
"""
 Módulo de Memória Inteligente do ChatFiscal

Combina:
- Memória Compartilhada (thread-safe)
- Memória Dedicada (por módulo)
- Memória Inteligente com FAISS (busca semântica)
- Persistência local em disco
"""

import os
import pickle
import json
import threading
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import faiss
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memory_chatfiscal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# 1️⃣ MEMÓRIA COMPARTILHADA (Thread-Safe)
# ══════════════════════════════════════════════════════════════════
class MemoriaCompartilhada:
    """
    Memória compartilhada entre módulos com thread-safety.
    Ideal para dados globais: arquivos carregados, configurações, cache.
    """
    
    def __init__(self):
        self.dados: Dict[str, Any] = {}
        self.lock = threading.Lock()
        logger.info("✅ MemoriaCompartilhada inicializada")
    
    def salvar(self, chave: str, valor: Any) -> None:
        """Salva um valor de forma thread-safe."""
        with self.lock:
            self.dados[chave] = valor
            logger.debug(f"💾 Salvo: {chave}")
    
    def obter(self, chave: str) -> Optional[Any]:
        """Obtém um valor de forma thread-safe."""
        with self.lock:
            return self.dados.get(chave)
    
    def listar_chaves(self) -> List[str]:
        """Retorna todas as chaves disponíveis."""
        with self.lock:
            return list(self.dados.keys())
    
    def limpar(self, chave: Optional[str] = None) -> None:
        """Limpa uma chave específica ou toda a memória."""
        with self.lock:
            if chave:
                self.dados.pop(chave, None)
                logger.info(f"🗑️ Chave removida: {chave}")
            else:
                self.dados.clear()
                logger.info("🗑️ Memória compartilhada limpa")
    
    def __len__(self) -> int:
        """Retorna quantidade de chaves armazenadas."""
        with self.lock:
            return len(self.dados)


# ══════════════════════════════════════════════════════════════════
# 2️⃣ MEMÓRIA DEDICADA (Isolada por Módulo)
# ══════════════════════════════════════════════════════════════════
class MemoriaDedicada:
    """
    Memória isolada para cada módulo específico.
    Não possui thread-lock (usa apenas no contexto local).
    """
    
    def __init__(self, nome_modulo: str = "default"):
        self.dados: Dict[str, Any] = {}
        self.nome_modulo = nome_modulo
        logger.info(f"✅ MemoriaDedicada [{nome_modulo}] inicializada")
    
    def salvar(self, chave: str, valor: Any) -> None:
        """Salva um valor na memória dedicada."""
        self.dados[chave] = valor
        logger.debug(f"💾 [{self.nome_modulo}] Salvo: {chave}")
    
    def obter(self, chave: str) -> Optional[Any]:
        """Obtém um valor da memória dedicada."""
        return self.dados.get(chave)
    
    def listar_chaves(self) -> List[str]:
        """Retorna todas as chaves disponíveis."""
        return list(self.dados.keys())
    
    def limpar(self, chave: Optional[str] = None) -> None:
        """Limpa uma chave específica ou toda a memória."""
        if chave:
            self.dados.pop(chave, None)
            logger.info(f"🗑️ [{self.nome_modulo}] Chave removida: {chave}")
        else:
            self.dados.clear()
            logger.info(f"🗑️ [{self.nome_modulo}] Memória limpa")
    
    def __len__(self) -> int:
        """Retorna quantidade de chaves armazenadas."""
        return len(self.dados)


# ══════════════════════════════════════════════════════════════════
# 3️⃣ MEMÓRIA INTELIGENTE (FAISS + Histórico + Persistência)
# ══════════════════════════════════════════════════════════════════
class MemoriaInteligente:
    """
    🧠 Memória Inteligente com busca semântica usando FAISS.
    
    Funcionalidades:
    - Armazena histórico de perguntas e respostas
    - Indexa conversas com embeddings vetoriais
    - Busca contexto relevante por similaridade semântica
    - Persistência local em disco
    - Integração com Streamlit Session State
    """
    
    def __init__(self, persist_dir: str = "memory_store", model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Inicializa a memória inteligente.
        
        Args:
            persist_dir: Diretório para persistência dos dados
            model_name: Modelo de embeddings HuggingFace
        """
        self.persist_dir = persist_dir
        self.model_name = model_name
        os.makedirs(persist_dir, exist_ok=True)
        
        # Caminhos de persistência
        self.index_path = os.path.join(persist_dir, "faiss.index")
        self.meta_path = os.path.join(persist_dir, "metadados.pkl")
        self.historico_path = os.path.join(persist_dir, "historico.json")
        
        # Inicialização de embeddings
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
            logger.info(f"✅ Embeddings carregados: {model_name}")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar embeddings: {e}")
            raise
        
        # Estruturas de dados
        self.historico: List[Dict[str, Any]] = []
        self.metadados: List[Dict[str, Any]] = []
        self.index: Optional[faiss.Index] = None
        self.dimension: Optional[int] = None
        
        # Thread-safety
        self.lock = threading.Lock()
        
        # Carrega dados persistentes (se existirem)
        self._carregar_memoria()
        
        logger.info(f"✅ MemoriaInteligente inicializada | Registros: {len(self.historico)}")
    
    def salvar_contexto(self, pergunta: str, resposta: str, metadados_extras: Optional[Dict] = None) -> None:
        """Armazena par pergunta-resposta + embedding FAISS."""
        with self.lock:
            try:
                texto_completo = f"Pergunta: {pergunta}\nResposta: {resposta}"
                vetor = self.embeddings.embed_query(texto_completo)
                vetor_np = np.array([vetor], dtype="float32")
                
                if self.index is None:
                    self.dimension = len(vetor)
                    self.index = faiss.IndexFlatL2(self.dimension)
                    logger.info(f"🔧 Índice FAISS criado | Dimensão: {self.dimension}")
                
                self.index.add(vetor_np)
                
                registro = {
                    "pergunta": pergunta,
                    "resposta": resposta,
                    "timestamp": datetime.now().isoformat(),
                    "id": len(self.metadados)
                }
                
                if metadados_extras:
                    registro.update(metadados_extras)
                
                self.metadados.append(registro)
                self.historico.append(registro)
                self._salvar_memoria()
                
                logger.info(f"💾 Contexto salvo | Total: {len(self.historico)}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao salvar contexto: {e}")
    
    def buscar_contexto_relevante(self, consulta: str, k: int = 3, threshold: float = 1.5) -> str:
        """Retorna contexto mais relevante semanticamente."""
        with self.lock:
            if not self.index or self.index.ntotal == 0:
                logger.warning("⚠️ Índice FAISS vazio")
                return ""
            
            try:
                vetor = self.embeddings.embed_query(consulta)
                vetor_np = np.array([vetor], dtype="float32")
                distancias, indices = self.index.search(vetor_np, min(k, self.index.ntotal))
                
                contexto_partes = []
                for dist, idx in zip(distancias[0], indices[0]):
                    if idx < len(self.metadados) and dist <= threshold:
                        meta = self.metadados[idx]
                        contexto_partes.append(
                            f"🔹 Pergunta: {meta['pergunta']}\n"
                            f"   Resposta: {meta['resposta'][:200]}...\n"
                            f"   [Similaridade: {dist:.3f}]"
                        )
                
                if contexto_partes:
                    logger.info(f"🔍 Encontrados {len(contexto_partes)} contextos relevantes")
                    return "\n\n".join(contexto_partes)
                else:
                    logger.info("🔍 Nenhum contexto relevante encontrado")
                    return ""
                
            except Exception as e:
                logger.error(f"❌ Erro na busca: {e}")
                return ""
    
    def obter_historico(self, ultimos_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retorna histórico completo ou últimos N registros."""
        with self.lock:
            if ultimos_n:
                return self.historico[-ultimos_n:]
            return self.historico.copy()
    
    def obter_historico_formatado(self, ultimos_n: int = 5) -> str:
        """Retorna histórico formatado para exibição ou envio à LLM."""
        historico = self.obter_historico(ultimos_n)
        
        if not historico:
            return "Nenhum histórico disponível."
        
        linhas = ["📜 HISTÓRICO RECENTE:\n"]
        for i, item in enumerate(historico, 1):
            linhas.append(f"{i}. Pergunta: {item['pergunta']}")
            linhas.append(f"   Resposta: {item['resposta'][:150]}...")
            linhas.append("")
        
        return "\n".join(linhas)
    
    def limpar(self, limpar_disco: bool = True) -> None:
        """Limpa memória e opcionalmente remove arquivos persistentes."""
        with self.lock:
            self.historico.clear()
            self.metadados.clear()
            self.index = None
            self.dimension = None
            
            if limpar_disco:
                for caminho in [self.index_path, self.meta_path, self.historico_path]:
                    if os.path.exists(caminho):
                        try:
                            os.remove(caminho)
                            logger.info(f"🗑️ Removido: {caminho}")
                        except Exception as e:
                            logger.warning(f"⚠️ Erro ao remover {caminho}: {e}")
            
            logger.info("🗑️ Memória inteligente limpa")
    
    def _salvar_memoria(self) -> None:
        """Persiste FAISS + metadados + histórico no disco."""
        try:
            if self.index and self.index.ntotal > 0:
                faiss.write_index(self.index, self.index_path)
            
            with open(self.meta_path, "wb") as f:
                pickle.dump({"metadados": self.metadados, "dimension": self.dimension}, f)
            
            with open(self.historico_path, "w", encoding="utf-8") as f:
                json.dump(self.historico, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar memória: {e}")
    
    def _carregar_memoria(self) -> None:
        """Carrega FAISS + metadados + histórico do disco."""
        try:
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
                logger.info(f"✅ Índice FAISS carregado: {self.index.ntotal} vetores")
            
            if os.path.exists(self.meta_path):
                with open(self.meta_path, "rb") as f:
                    dados = pickle.load(f)
                    self.metadados = dados.get("metadados", [])
                    self.dimension = dados.get("dimension")
            
            if os.path.exists(self.historico_path):
                with open(self.historico_path, "r", encoding="utf-8") as f:
                    self.historico = json.load(f)
                    
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar memória: {e}")
    
    def __len__(self) -> int:
        return len(self.historico)
    
    def estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas da memória."""
        with self.lock:
            return {
                "total_registros": len(self.historico),
                "total_vetores_faiss": self.index.ntotal if self.index else 0,
                "dimensao_vetor": self.dimension,
                "tamanho_indice_mb": os.path.getsize(self.index_path) / (1024*1024) if os.path.exists(self.index_path) else 0,
                "modelo_embeddings": self.model_name,
                "diretorio_persistencia": self.persist_dir
            }
