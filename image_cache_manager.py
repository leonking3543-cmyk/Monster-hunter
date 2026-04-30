"""
Cache Manager para Monster Images
Otimizado para cache local com metadata tracking
"""

import os
import json
from pathlib import Path
from typing import Optional

class ImageCacheManager:
    """Gerencia cache de imagens de monstros em disco local"""
    
    def __init__(self, cache_dir: str = "imagem"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / ".metadata.json"
        self.metadata = self._load_metadata()
        print(f"[Cache Manager] Cache directory: {self.cache_dir}")
    
    def _load_metadata(self) -> dict:
        """Carrega metadados das imagens em cache"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_metadata(self):
        """Salva metadados das imagens"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Cache Manager] Erro ao salvar metadata: {e}")
    
    def _safe_filename(self, name: str) -> str:
        """Converte nome do monstro em filename seguro"""
        # Remove caracteres especiais mas preserva a essência
        safe = ""
        for c in name.lower():
            if c.isalnum() or c in "-_":
                safe += c
            elif c in "áàâãäéèêëíìîïóòôõöúùûüçñ":
                # Normaliza acentos
                acentos = {
                    'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
                    'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
                    'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
                    'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
                    'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
                    'ç': 'c', 'ñ': 'n'
                }
                safe += acentos.get(c, c)
            else:
                safe += "_"
        return safe.strip("_")
    
    def get_image_path(self, mon_name: str) -> str:
        """Retorna o caminho completo do arquivo de imagem"""
        safe_name = self._safe_filename(mon_name)
        return str(self.cache_dir / f"{safe_name}.png")
    
    def has_cached_image(self, mon_name: str) -> bool:
        """Verifica se a imagem existe em cache"""
        path = self.get_image_path(mon_name)
        return os.path.exists(path) and os.path.getsize(path) > 1000
    
    def get_cached_image_bytes(self, mon_name: str) -> Optional[bytes]:
        """Retorna os bytes da imagem em cache, ou None"""
        path = self.get_image_path(mon_name)
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'rb') as f:
                data = f.read()
            if len(data) > 1000:  # Mínimo esperado para PNG válido
                return data
        except Exception as e:
            print(f"[Cache Manager] Erro ao ler {path}: {e}")
        return None
    
    def save_cached_image(self, mon_name: str, image_bytes: bytes) -> bool:
        """Guarda imagem em cache e atualiza metadata"""
        if not image_bytes or len(image_bytes) < 1000:
            return False
        
        path = self.get_image_path(mon_name)
        try:
            with open(path, 'wb') as f:
                f.write(image_bytes)
            
            # Atualiza metadata
            self.metadata[mon_name] = {
                "path": path,
                "size": len(image_bytes),
                "cached_at": str(Path(path).stat().st_mtime)
            }
            self._save_metadata()
            
            print(f"[Cache Manager] Guardada: {mon_name} ({len(image_bytes)} bytes)")
            return True
        except Exception as e:
            print(f"[Cache Manager] Erro ao guardar {path}: {e}")
            return False
    
    def get_cache_stats(self) -> dict:
        """Retorna estatísticas do cache"""
        total_size = 0
        count = 0
        for mon_name in self.metadata.keys():
            path = self.get_image_path(mon_name)
            if os.path.exists(path):
                total_size += os.path.getsize(path)
                count += 1
        
        return {
            "images_cached": count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
    
    def clear_cache(self):
        """Limpa todo o cache (cuidado!)"""
        for mon_name in list(self.metadata.keys()):
            path = self.get_image_path(mon_name)
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass
        self.metadata = {}
        self._save_metadata()
        print("[Cache Manager] Cache limpo!")


# Instância global
cache_manager = ImageCacheManager("imagem")
